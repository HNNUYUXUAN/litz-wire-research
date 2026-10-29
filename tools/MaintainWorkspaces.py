"""Inventory, consolidate and verify explicitly selected local research folders.

No arguments beyond a batch directory performs no cleanup.  Inventory and plan
are read-only with respect to sources.  Apply requires --execute and consumes the
recorded identities; no glob-based recursive deletion is used.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import subprocess
import sys
import time
import zlib
import struct
import traceback
import re

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIRS = {"__pycache__", ".ipynb_checkpoints", "node_modules", ".next", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


def now():
    return datetime.now(timezone.utc).isoformat()


def native(path):
    text = os.path.abspath(os.fspath(path))
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\UNC\\" + text[2:] if text.startswith("\\\\") else "\\\\?\\" + text
    return text


def digest(path):
    with open(native(path), "rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def identity(path):
    s = os.lstat(native(path))
    return (s.st_size, s.st_mtime_ns, s.st_dev, s.st_ino)


def is_link(s):
    return stat.S_ISLNK(s.st_mode) or bool(getattr(s, "st_file_attributes", 0) & 0x400)


def within(path, root):
    p, r = os.path.normcase(os.path.abspath(path)), os.path.normcase(os.path.abspath(root))
    return os.path.commonpath([p, r]) == r


def checked(path, root):
    """Lexical boundary plus a no-reparse-point walk through every ancestor."""
    if not within(path, root):
        raise ValueError("Path outside selected root: " + str(path))
    relative = Path(os.path.relpath(path, root))
    cursor = Path(root)
    if os.path.lexists(native(cursor)) and is_link(os.lstat(native(cursor))):
        raise ValueError("Root is a link: " + str(cursor))
    for part in relative.parts[:-1]:
        cursor /= part
        if os.path.lexists(native(cursor)) and is_link(os.lstat(native(cursor))):
            raise ValueError("Linked ancestor: " + str(cursor))
    return Path(path)


def write_json(path, obj):
    Path(native(path.parent)).mkdir(parents=True, exist_ok=True)
    temporary = Path(str(path) + ".writing")
    with open(native(temporary), "w", encoding="utf-8", newline="\n") as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(native(temporary), native(path))


def connect(batch):
    batch.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(native(batch / "inventory.sqlite"))
    db.row_factory = sqlite3.Row
    db.executescript("""
    PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS roots(id TEXT PRIMARY KEY,source TEXT,destination TEXT,active INTEGER,complete INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS entries(root TEXT,rel TEXT,kind TEXT,size INTEGER,mtime INTEGER,dev INTEGER,ino INTEGER,sha TEXT,target TEXT,attrs INTEGER,cache INTEGER,action TEXT DEFAULT 'keep',canonical_root TEXT,canonical_rel TEXT,status TEXT DEFAULT 'pending',PRIMARY KEY(root,rel));
    CREATE TABLE IF NOT EXISTS dirs(root TEXT,rel TEXT,digest TEXT,bytes INTEGER DEFAULT 0,files INTEGER DEFAULT 0,PRIMARY KEY(root,rel));
    CREATE TABLE IF NOT EXISTS events(at TEXT,operation TEXT,root TEXT,rel TEXT,detail TEXT);
    CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT);
    CREATE INDEX IF NOT EXISTS entries_parent ON entries(root,rel);
    CREATE INDEX IF NOT EXISTS entries_hash ON entries(sha,size);
    """)
    return db


def event(db, operation, root, rel, detail=""):
    db.execute("INSERT INTO events VALUES(?,?,?,?,?)", (now(), operation, root, rel, detail))


def resource_guard():
    try:
        import psutil
        if psutil.virtual_memory().available < 8 * 1024**3:
            raise RuntimeError("Less than 8 GiB system memory reserve")
        if psutil.Process().memory_info().rss > 24 * 1024**3:
            raise RuntimeError("Task memory budget exceeded")
    except ImportError:
        raise RuntimeError("psutil is required for the resource guard")


def command_uses_root(command, root):
    command = command.replace("\\", "/").casefold()
    root = str(root).replace("\\", "/").rstrip("/").casefold()
    return bool(re.search(re.escape(root) + r"(?=$|[/\s\"'])", command))


def writer_guard(roots, batch):
    """Observe writers; never terminate processes owned by somebody else."""
    import psutil
    selected = [r["source"] for r in roots.values() if not r["active"]]
    writers, inaccessible = [], []
    for process in psutil.process_iter(["pid", "name", "create_time"]):
        if process.pid == os.getpid():
            continue
        try:
            for opened in process.open_files():
                mode = getattr(opened, "mode", "unknown")
                if any(within(opened.path, root) for root in selected) and (mode == "unknown" or any(c in mode for c in ("w", "a", "+"))):
                    writers.append(dict(process.info, path=opened.path, mode=mode))
            if (process.info["name"] or "").lower() in {"git.exe", "git", "robocopy.exe", "7z.exe", "node.exe", "python.exe", "pythonw.exe", "wolframkernel.exe", "wolframscript.exe", "ansysedt.exe"}:
                command = " ".join(process.cmdline())
                cwd = process.cwd()
                if any(command_uses_root(command, root) or within(cwd, root) for root in selected):
                    writers.append(dict(process.info, reason="active repository/archive command"))
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            inaccessible.append(process.pid)
    write_json(batch / "writer-check.json", dict(at=now(), writers=writers, inaccessible_process_ids=inaccessible))
    if writers:
        raise RuntimeError("Selected source has an external writer; see writer-check.json")


def default_spec(project):
    repos = project.parent
    archives = repos.parent / "archives"
    names = ["litz-wire-modeling-src", "litz-wire-modeling", "litz-wire-research"]
    snapshots = ["litz_private_20261007_final_02", "litz_public_preparation_20261007_01", "litz_candidate_self_audit_20261013", "litz_paper_sample_review_20261013", "litz_tool_experience_20261013_01"]
    result = [dict(id="current", source=str(project), destination=str(project), active=True)]
    result += [dict(id=name, source=str(repos / name), destination=str(project / ".local-archive/workspaces" / name), active=False) for name in names]
    result += [dict(id=name, source=str(archives / name), destination=str(project / ".local-archive/snapshots" / name), active=False) for name in snapshots]
    return result


def destination_rel(rel):
    return "/".join("git-metadata" if x == ".git" else x for x in Path(rel).parts)


def cache_file(rel, active):
    parts = Path(rel).parts
    # Preserve the current interpreter and everything below Git object stores.
    if ".git" in parts:
        return False
    if parts and parts[0] in {".conda", ".local-archive", ".local-library"}:
        return False
    if active and parts and parts[0] == ".venv":
        return False
    if any(p in CACHE_DIRS for p in parts[:-1]):
        return True
    if not active and any(p in {".venv", "venv"} for p in parts[:-1]):
        return True
    if parts and parts[0] in {"build", "dist"}:
        return True
    return Path(rel).suffix in {".pyc", ".pyo", ".tsbuildinfo"}


def git_record(source):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    result = {}
    for label, args in [("head", ["rev-parse", "HEAD"]), ("refs", ["show-ref"]), ("status", ["status", "--porcelain=v1", "--untracked-files=all"]), ("worktrees", ["worktree", "list", "--porcelain"])]:
        p = subprocess.run(["git", "-c", "safe.directory=" + str(source), "-c", "core.longpaths=true", "-C", str(source), *args], capture_output=True, env=env)
        result[label] = dict(exit_code=p.returncode, stdout=p.stdout.decode("utf-8", "replace"), stderr=p.stderr.decode("utf-8", "replace"))
    return result


def scan(db, batch, spec):
    if db.execute("SELECT 1 FROM meta WHERE key='applied'").fetchone():
        raise ValueError("Cannot inventory an already applied batch")
    stored = db.execute("SELECT value FROM meta WHERE key='spec'").fetchone()
    serialized = json.dumps(spec, sort_keys=True)
    if stored and stored[0] != serialized:
        raise ValueError("Batch source specification changed")
    db.execute("INSERT OR IGNORE INTO meta VALUES('spec',?)", (serialized,))
    for item in spec:
        db.execute("INSERT OR IGNORE INTO roots(id,source,destination,active) VALUES(?,?,?,?)", (item["id"], item["source"], item["destination"], item["active"]))
    db.commit()
    progress = dict(started_utc=now(), files=0, bytes_hashed=0, errors=0)
    last = time.monotonic()
    # Bounded batches avoid retaining a full filesystem inventory in memory.
    with ThreadPoolExecutor(max_workers=4) as pool:
        for root in db.execute("SELECT * FROM roots ORDER BY rowid").fetchall():
            if root["complete"]:
                continue
            source = Path(root["source"])
            checked(source, source)
            if not source.is_dir():
                raise FileNotFoundError(str(source))
            if (source / ".git").exists():
                write_json(batch / (root["id"] + "-git-before.json"), git_record(source))
            pending = [source]
            hash_jobs = []

            def flush():
                nonlocal last
                for row, result in zip(hash_jobs, pool.map(hash_one, hash_jobs)):
                    rel, kind, size, mtime, dev, ino, sha, target, attrs, cache = result
                    db.execute("INSERT OR REPLACE INTO entries(root,rel,kind,size,mtime,dev,ino,sha,target,attrs,cache) VALUES(?,?,?,?,?,?,?,?,?,?,?)", (root["id"], rel, kind, size, mtime, dev, ino, sha, target, attrs, cache))
                    progress["files"] += 1
                    progress["bytes_hashed"] += size
                hash_jobs.clear()
                db.commit()
                if time.monotonic() - last > 10:
                    resource_guard()
                    write_json(batch / "progress.json", dict(progress, stage="inventory", root=root["id"], updated_utc=now()))
                    print(json.dumps(dict(progress, root=root["id"])), flush=True)
                    last = time.monotonic()

            def hash_one(job):
                path, rel, s, cache = job
                before = identity(path)
                expected = (s.st_size, s.st_mtime_ns, s.st_dev, s.st_ino)
                if before != expected:
                    raise RuntimeError("Changed before hashing: " + str(path))
                sha = digest(path)
                if identity(path) != before:
                    raise RuntimeError("Changed during hashing: " + str(path))
                return rel, "file", s.st_size, s.st_mtime_ns, s.st_dev, s.st_ino, sha, None, getattr(s, "st_file_attributes", 0), cache

            while pending:
                folder = pending.pop()
                rel_dir = folder.relative_to(source).as_posix()
                if rel_dir == ".":
                    rel_dir = ""
                db.execute("INSERT OR IGNORE INTO dirs(root,rel) VALUES(?,?)", (root["id"], rel_dir))
                try:
                    children = list(os.scandir(native(folder)))
                    for child in children:
                        path = folder / child.name
                        rel = path.relative_to(source).as_posix()
                        if root["active"] and rel.split("/")[0] == ".local-archive":
                            continue
                        s = os.lstat(native(path))
                        if is_link(s):
                            target = os.readlink(native(path))
                            db.execute("INSERT OR REPLACE INTO entries(root,rel,kind,size,mtime,dev,ino,sha,target,attrs,cache) VALUES(?,?,?,?,?,?,?,?,?,?,?)", (root["id"], rel, "link", 0, s.st_mtime_ns, s.st_dev, s.st_ino, hashlib.sha256(target.encode()).hexdigest(), target, getattr(s, "st_file_attributes", 0), cache_file(rel + "/link", bool(root["active"]))))
                        elif stat.S_ISDIR(s.st_mode):
                            pending.append(path)
                        elif stat.S_ISREG(s.st_mode):
                            prior = db.execute("SELECT size,mtime,dev,ino,sha FROM entries WHERE root=? AND rel=?", (root["id"], rel)).fetchone()
                            if prior and tuple(prior)[:4] == (s.st_size, s.st_mtime_ns, s.st_dev, s.st_ino) and prior["sha"]:
                                continue
                            hash_jobs.append((path, rel, s, int(cache_file(rel, bool(root["active"])))))
                            if len(hash_jobs) >= 128:
                                flush()
                        else:
                            raise ValueError("Unsupported filesystem entry: " + str(path))
                except Exception as exc:
                    event(db, "inventory_error", root["id"], rel_dir, repr(exc))
                    db.commit()
                    raise
            flush()
            db.execute("UPDATE roots SET complete=1 WHERE id=?", (root["id"],))
            db.commit()
    db.execute("INSERT OR REPLACE INTO meta VALUES('inventory_complete',?)", (now(),))
    db.commit()
    write_json(batch / "inventory-summary.json", summary(db))


def tree_hashes(db):
    for root in db.execute("SELECT * FROM roots ORDER BY rowid").fetchall():
        folders = {r["rel"]: [] for r in db.execute("SELECT rel FROM dirs WHERE root=?", (root["id"],))}
        totals = {name: [0, 0] for name in folders}
        for row in db.execute("SELECT rel,kind,size,sha FROM entries WHERE root=?", (root["id"],)):
            parent, _, name = row["rel"].rpartition("/")
            folders[parent].append((name, row["kind"], row["sha"]))
            totals[parent][0] += row["size"]
            totals[parent][1] += 1
        for rel in sorted(folders, key=lambda p: (p.count("/") + bool(p), p), reverse=True):
            sha = hashlib.sha256(json.dumps(sorted(folders[rel]), ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
            count_bytes, count_files = totals[rel]
            db.execute("UPDATE dirs SET digest=?,bytes=?,files=? WHERE root=? AND rel=?", (sha, count_bytes, count_files, root["id"], rel))
            if rel:
                parent, _, name = rel.rpartition("/")
                folders[parent].append((name, "dir", sha))
                totals[parent][0] += count_bytes
                totals[parent][1] += count_files
        db.commit()


def rows_under(db, root, rel):
    # No LIKE: literal %, _, brackets and Unicode are valid research filenames.
    prefix = rel + "/" if rel else ""
    if prefix:
        return db.execute("SELECT * FROM entries WHERE root=? AND rel>=? AND rel<? ORDER BY rel", (root, prefix, rel + "0")).fetchall()
    return db.execute("SELECT * FROM entries WHERE root=? ORDER BY rel", (root,)).fetchall()


def audit_git_temps(db, batch):
    """Prove truncated one-blob pack files are prefixes of retained LFS data.

    Merely having a tmp_pack name is insufficient.  The complete raw object is
    hashed, re-encoded, and the exact compressed prefix is matched to every
    temporary file's inventoried SHA256.  Unmatched files remain preserved.
    """
    if not db.execute("SELECT 1 FROM meta WHERE key='inventory_complete'").fetchone():
        raise ValueError("Complete inventory required")
    roots = {r["id"]: r for r in db.execute("SELECT * FROM roots")}
    groups, unresolved, proofs = {}, [], []
    for row in db.execute("SELECT * FROM entries WHERE kind='file' AND rel LIKE '%/.git/objects/pack/tmp_pack_%' OR (kind='file' AND rel LIKE '.git/objects/pack/tmp_pack_%')").fetchall():
        path = source_path(roots[row["root"]], row)
        with open(native(path), "rb") as stream:
            header = stream.read(12)
            if header != b"PACK" + struct.pack(">II", 2, 1):
                unresolved.append(dict(root=row["root"], path=row["rel"], reason="not a single-object v2 pack")); continue
            byte = stream.read(1)[0]
            kind, size, shift = (byte >> 4) & 7, byte & 15, 4
            encoded = bytes([byte])
            while byte & 128:
                byte = stream.read(1)[0]; encoded += bytes([byte])
                size |= (byte & 127) << shift; shift += 7
        if kind != 3:
            unresolved.append(dict(root=row["root"], path=row["rel"], reason="not a raw blob")); continue
        groups.setdefault((size, header + encoded), []).append(dict(row))
    for (object_size, header), rows in groups.items():
        candidates = db.execute("SELECT * FROM entries WHERE kind='file' AND size=? AND rel LIKE '%/lfs/objects/%' ORDER BY root,rel", (object_size,)).fetchall()
        candidates = list({r["sha"]: r for r in candidates}.values())
        remaining = rows[:]
        for candidate in candidates:
            source = source_path(roots[candidate["root"]], candidate)
            verify_file(source, candidate, source=True)
            boundaries = sorted({r["size"] for r in remaining})
            if not boundaries:
                break
            hashes, position, h, index = {}, 0, hashlib.sha256(), 0
            def consume(data):
                nonlocal position, index
                offset = 0
                while index < len(boundaries) and position + len(data) - offset >= boundaries[index]:
                    take = boundaries[index] - position
                    h.update(data[offset:offset+take]); offset += take; position += take
                    hashes[boundaries[index]] = h.copy().hexdigest(); index += 1
                if index < len(boundaries):
                    h.update(data[offset:]); position += len(data) - offset
            consume(header)
            compressor = zlib.compressobj(6)
            with open(native(source), "rb") as stream:
                while index < len(boundaries):
                    block = stream.read(1024**2)
                    if not block:
                        consume(compressor.flush()); break
                    consume(compressor.compress(block))
            still_unmatched = []
            for row in remaining:
                if hashes.get(row["size"]) == row["sha"]:
                    proof = dict(root=row["root"], path=row["rel"], bytes=row["size"], sha256=row["sha"], preserved_object_root=candidate["root"], preserved_object_path=candidate["rel"], preserved_object_sha256=candidate["sha"], declared_object_bytes=object_size, method="exact SHA256 of re-encoded retained blob pack prefix")
                    proofs.append(proof)
                    db.execute("UPDATE entries SET cache=1 WHERE root=? AND rel=?", (row["root"], row["rel"]))
                    event(db, "git_temp_prefix_verified", row["root"], row["rel"], json.dumps(proof))
                else:
                    still_unmatched.append(row)
            remaining = still_unmatched
            print(json.dumps(dict(stage="audit-git-temp", declared_object_bytes=object_size, verified=len(rows)-len(remaining), remaining=len(remaining))), flush=True)
        unresolved.extend(dict(root=r["root"], path=r["rel"], reason="no exact retained-object encoding matched") for r in remaining)
        db.commit()
    unresolved.extend(dict(root=r["root"], path=r["rel"], bytes=r["size"], reason="loose temporary object retained; no regeneration proof") for r in db.execute("SELECT root,rel,size FROM entries WHERE kind='file' AND rel LIKE '%/.git/objects/%/tmp_obj_%' OR (kind='file' AND rel LIKE '.git/objects/%/tmp_obj_%')"))
    result = dict(at=now(), verified_files=len(proofs), verified_bytes=sum(p["bytes"] for p in proofs), proofs=proofs, preserved_unresolved=unresolved)
    write_json(batch / "git-temp-audit.json", result)
    return result


def plan(db, batch):
    if not db.execute("SELECT 1 FROM meta WHERE key='inventory_complete'").fetchone():
        raise ValueError("Inventory must complete first")
    if db.execute("SELECT 1 FROM meta WHERE key='applied'").fetchone():
        raise ValueError("Cannot replan an applied batch")
    db.execute("UPDATE entries SET action=CASE WHEN cache=1 THEN 'cache' WHEN root='current' THEN 'keep' ELSE 'migrate' END,canonical_root=NULL,canonical_rel=NULL")
    tree_hashes(db)
    roots = db.execute("SELECT * FROM roots ORDER BY rowid").fetchall()
    canonical = {}
    duplicates = []
    candidates = []
    for rank, root in enumerate(roots):
        # Preserve source layouts and metadata; remove only complete duplicate trees.
        directories = db.execute("SELECT * FROM dirs WHERE root=? AND rel<>'' AND (bytes>=1048576 OR files>=20) ORDER BY length(rel),rel", (root["id"],)).fetchall()
        for folder in directories:
            redundant = any(any(word in p.casefold() for word in ("restore", "readback", "download")) for p in Path(folder["rel"]).parts)
            candidates.append((20 + rank if redundant else rank, len(folder["rel"]), folder["rel"], dict(root), dict(folder), redundant))
    removed_by_root = {r["id"]: [] for r in roots}
    for _, _, _, root, folder, redundant in sorted(candidates, key=lambda r: r[:3]):
            removed = removed_by_root[root["id"]]
            rel = folder["rel"]
            if any(rel == p or rel.startswith(p + "/") for p in removed):
                continue
            entries = rows_under(db, root["id"], rel)
            if any(r["cache"] for r in entries) or any(r["kind"] == "link" for r in entries):
                continue
            key = (folder["digest"], folder["files"])
            prior = canonical.get(key)
            # Never remove current paths or small source/reader directory trees.
            has_git = any(".git" in Path(r["rel"]).parts for r in entries)
            eligible = not has_git and ((not root["active"] and (rel.startswith(("outputs/", "data/", "web/public/")) or root["id"].startswith("litz_"))) or (root["active"] and rel.startswith("outputs/quark_backup_20261020_01/") and redundant))
            if prior and eligible:
                cr, cp = prior
                for row in entries:
                    suffix = row["rel"][len(rel):].lstrip("/")
                    target = cp + "/" + suffix
                    reference = db.execute("SELECT action,sha,size,kind FROM entries WHERE root=? AND rel=?", (cr, target)).fetchone()
                    if not reference or reference["action"] not in {"keep", "migrate", "duplicate"} or (reference["sha"], reference["size"], reference["kind"]) != (row["sha"], row["size"], row["kind"]):
                        raise ValueError("Invalid duplicate tree mapping: " + repr((root["id"], row["rel"], cr, target)))
                    db.execute("UPDATE entries SET action='duplicate',canonical_root=?,canonical_rel=? WHERE root=? AND rel=?", (cr, target, root["id"], row["rel"]))
                removed.append(rel)
                duplicates.append(dict(root=root["id"], path=rel, canonical_root=cr, canonical_path=cp, bytes=folder["bytes"], files=folder["files"]))
            elif not prior:
                canonical[key] = (root["id"], rel)
    db.commit()
    write_json(batch / "duplicate-trees.json", duplicates)
    # Later whole-tree decisions may replace an earlier canonical subtree.
    # Flatten every file mapping to a location that will actually be retained.
    for row in db.execute("SELECT root,rel,canonical_root,canonical_rel FROM entries WHERE action='duplicate'").fetchall():
        cr, cp = row["canonical_root"], row["canonical_rel"]
        visited = {(row["root"], row["rel"])}
        while True:
            if (cr, cp) in visited:
                raise ValueError("Duplicate mapping cycle")
            visited.add((cr, cp))
            target = db.execute("SELECT action,canonical_root,canonical_rel FROM entries WHERE root=? AND rel=?", (cr, cp)).fetchone()
            if target["action"] == "duplicate":
                cr, cp = target["canonical_root"], target["canonical_rel"]
                continue
            if target["action"] not in {"keep", "migrate"}:
                raise ValueError("Duplicate points to a nonretained file")
            break
        db.execute("UPDATE entries SET canonical_root=?,canonical_rel=? WHERE root=? AND rel=?", (cr, cp, row["root"], row["rel"]))
    db.commit()
    write_json(batch / "plan.json", dict(created_utc=now(), roots=[dict(r) for r in roots], source_trees=[dict(r) for r in db.execute("SELECT root,digest,bytes,files FROM dirs WHERE rel=''")], actions=summary(db), duplicate_trees=len(duplicates), execute_required=True))
    db.execute("INSERT OR REPLACE INTO meta VALUES('planned',?)", (now(),))
    db.commit()
    print(json.dumps(summary(db)), flush=True)


def source_path(root, row):
    return checked(Path(root["source"]) / Path(row["rel"]), root["source"])


def output_path(root, rel):
    path = Path(root["destination"]) / (Path(rel) if root["active"] else Path(destination_rel(rel)))
    return checked(path, root["destination"])


def verify_file(path, row, source=False):
    if row["kind"] == "link":
        if not os.path.lexists(native(path)) or os.readlink(native(path)) != row["target"]:
            raise RuntimeError("Link identity mismatch: " + str(path))
        return
    s = os.lstat(native(path))
    if is_link(s) or not stat.S_ISREG(s.st_mode) or s.st_size != row["size"]:
        raise RuntimeError("File type/size mismatch: " + str(path))
    if source and (s.st_size, s.st_mtime_ns, s.st_dev, s.st_ino) != (row["size"], row["mtime"], row["dev"], row["ino"]):
        raise RuntimeError("Source changed since inventory: " + str(path))
    if digest(path) != row["sha"]:
        raise RuntimeError("SHA256 mismatch: " + str(path))
    if identity(path) != (s.st_size, s.st_mtime_ns, s.st_dev, s.st_ino):
        raise RuntimeError("File changed during verification: " + str(path))


def delete_one(path, row, root):
    checked(path, root)
    s = os.lstat(native(path))
    if row["kind"] == "link":
        if getattr(s, "st_file_attributes", 0) & 0x10:
            os.rmdir(native(path))
        else:
            os.unlink(native(path))
    else:
        if getattr(s, "st_file_attributes", 0) & 1:
            os.chmod(native(path), stat.S_IWRITE | stat.S_IREAD)
        os.unlink(native(path))


def verify_git(db, batch, verify_entry=verify_file):
    results = []
    roots = {r["id"]: r for r in db.execute("SELECT * FROM roots")}
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    metadata = [r for r in db.execute("SELECT root,rel FROM dirs") if r["rel"] == ".git" or r["rel"].endswith("/.git")]
    for index, folder in enumerate(metadata):
        root, rel = roots[folder["root"]], folder["rel"]
        if not db.execute("SELECT 1 FROM entries WHERE root=? AND rel=?", (root["id"], rel + "/HEAD")).fetchone():
            continue
        path = output_path(root, rel)
        args = ["git", "-c", "safe.directory=" + str(path.parent), "-c", "core.longpaths=true", "--git-dir=" + str(path), "--work-tree=" + str(path.parent), "fsck", "--full", "--no-dangling"]
        result = subprocess.run(args, capture_output=True, env=env)
        log = batch / ("git-fsck-" + str(index) + ".log")
        log.write_bytes(result.stdout + result.stderr)
        lfs_count, lfs_errors = 0, []
        for row in rows_under(db, root["id"], rel + "/lfs/objects"):
            name = Path(row["rel"]).name
            if row["kind"] == "file" and len(name) == 64 and all(c in "0123456789abcdef" for c in name):
                verify_entry(output_path(root, row["rel"]), row)
                lfs_count += 1
                if row["sha"] != name:
                    lfs_errors.append(row["rel"])
        record = dict(root=root["id"], original_metadata=rel, retained_metadata=str(path), fsck_exit_code=result.returncode, log=log.name, lfs_objects=lfs_count, lfs_errors=lfs_errors)
        results.append(record)
        write_json(batch / "git-verification.json", dict(at=now(), repositories=results))
        print(json.dumps(dict(stage="git-verify", repository=root["id"], fsck_exit_code=result.returncode, lfs_objects=lfs_count)), flush=True)
        if result.returncode or lfs_errors:
            raise RuntimeError("Archived Git/LFS integrity check failed: " + str(path))
    return results


def apply(db, batch):
    if not db.execute("SELECT 1 FROM meta WHERE key='planned'").fetchone():
        raise ValueError("Plan must be generated first")
    roots = {r["id"]: r for r in db.execute("SELECT * FROM roots")}
    writer_guard(roots, batch)
    db.execute("INSERT OR IGNORE INTO meta VALUES('applied',?)", (now(),))
    db.commit()
    last = time.monotonic()
    counters = dict(copied=0, removed=0, bytes_copied=0, bytes_removed=0)
    verified_targets = {}

    def target_verify(path, row):
        key = str(path)
        fingerprint = identity(path)
        if verified_targets.get(key) == (fingerprint, row["sha"]):
            return
        verify_file(path, row)
        verified_targets[key] = (identity(path), row["sha"])

    def progress(stage):
        nonlocal last
        if time.monotonic() - last >= 10:
            resource_guard()
            db.commit()
            write_json(batch / "progress.json", dict(counters, stage=stage, updated_utc=now()))
            print(json.dumps(dict(counters, stage=stage)), flush=True)
            last = time.monotonic()

    # No source is deleted until all retained files have a verified target.
    for root in roots.values():
        if root["active"]:
            continue
        for folder in db.execute("SELECT rel,files FROM dirs WHERE root=? AND files=0 ORDER BY length(rel)", (root["id"],)).fetchall():
            if not cache_file(folder["rel"] + "/_", False):
                path = output_path(root, folder["rel"])
                Path(native(path)).mkdir(parents=True, exist_ok=True)
        for row in db.execute("SELECT * FROM entries WHERE root=? AND action='migrate' ORDER BY rel", (root["id"],)).fetchall():
            src, dst = source_path(root, row), output_path(root, row["rel"])
            if row["status"] == "removed":
                continue
            Path(native(dst.parent)).mkdir(parents=True, exist_ok=True)
            if row["kind"] == "link":
                # Links are preserved as explicit inert records, never followed.
                record = Path(str(dst) + ".link-record.json")
                write_json(record, dict(original_path=row["rel"], target=row["target"], sha256=row["sha"], attributes=row["attrs"]))
                if os.path.lexists(native(src)):
                    verify_file(src, row, source=True)
            else:
                if os.path.lexists(native(dst)):
                    target_verify(dst, row)
                else:
                    verify_file(src, row, source=True)
                    staging = batch / "copy-staging"
                    staging.mkdir(parents=True, exist_ok=True)
                    tmp = checked(staging / (root["id"] + "_" + row["sha"] + ".partial"), staging)
                    if os.path.lexists(native(tmp)) and (is_link(os.lstat(native(tmp))) or not stat.S_ISREG(os.lstat(native(tmp)).st_mode)):
                        raise ValueError("Unsafe task copy staging file: " + str(tmp))
                    shutil.copy2(native(src), native(tmp), follow_symlinks=False)
                    verify_file(tmp, row)
                    if os.path.lexists(native(dst)):
                        raise FileExistsError(str(dst))
                    os.replace(native(tmp), native(dst))
                    verified_targets[str(dst)] = (identity(dst), row["sha"])
                    counters["copied"] += 1
                    counters["bytes_copied"] += row["size"]
            db.execute("UPDATE entries SET status='copied' WHERE root=? AND rel=?", (root["id"], row["rel"]))
            progress("copy")
        db.commit()
    write_json(batch / "copy-complete.json", dict(completed_utc=now(), **counters))
    verify_git(db, batch, target_verify)
    # Full source-set check catches new files before a batch can be removed.
    for root in roots.values():
        if root["active"]:
            continue
        actual = set()
        stack = [Path(root["source"])]
        if not os.path.exists(native(stack[0])):
            continue
        while stack:
            folder = stack.pop()
            for child in os.scandir(native(folder)):
                p = folder / child.name
                s = child.stat(follow_symlinks=False)
                if stat.S_ISDIR(s.st_mode) and not is_link(s):
                    stack.append(p)
                else:
                    actual.add(p.relative_to(root["source"]).as_posix())
        expected = {r["rel"] for r in db.execute("SELECT rel FROM entries WHERE root=? AND status<>'removed'", (root["id"],))}
        # Reconcile an interruption between unlink and the next SQLite commit.
        started = db.execute("SELECT 1 FROM meta WHERE key=?", ("delete_started:" + root["id"],)).fetchone()
        if started and not actual - expected:
            for missing in expected - actual:
                row = db.execute("SELECT * FROM entries WHERE root=? AND rel=?", (root["id"], missing)).fetchone()
                if row["action"] == "migrate" and row["kind"] == "file":
                    target_verify(output_path(root, row["rel"]), row)
                elif row["action"] == "duplicate":
                    target_verify(output_path(roots[row["canonical_root"]], row["canonical_rel"]), row)
                elif row["action"] == "migrate" and row["kind"] == "link":
                    record = Path(str(output_path(root, row["rel"])) + ".link-record.json")
                    preserved = json.loads(Path(native(record)).read_text(encoding="utf-8"))
                    if preserved["sha256"] != row["sha"] or preserved["target"] != row["target"]:
                        raise ValueError("Cannot reconcile missing source link")
                elif row["action"] != "cache":
                    raise RuntimeError("Cannot reconcile missing source link")
                db.execute("UPDATE entries SET status='removed' WHERE root=? AND rel=?", (root["id"], missing))
                event(db, "resumed_unlink", root["id"], missing, row["action"])
            db.commit()
            expected = actual
        if actual != expected:
            raise RuntimeError("Source membership changed: " + root["id"] + "; added=" + str(len(actual-expected)) + "; missing=" + str(len(expected-actual)))
        # Validate the whole batch before the first deletion in that source root.
        verified_sources = {}
        for row in db.execute("SELECT * FROM entries WHERE root=? AND status<>'removed'", (root["id"],)).fetchall():
            verify_file(source_path(root, row), row, source=True)
            verified_sources[row["rel"]] = identity(source_path(root, row))
            if row["action"] == "duplicate":
                cr = roots[row["canonical_root"]]
                target_verify(output_path(cr, row["canonical_rel"]), row)
            progress("predelete-verify")
        db.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", ("delete_started:" + root["id"], now()))
        db.commit()
        for row in db.execute("SELECT * FROM entries WHERE root=? AND status<>'removed' ORDER BY length(rel) DESC", (root["id"],)).fetchall():
            src = source_path(root, row)
            # Check immediately before unlinking, including the retained copy.
            if identity(src) != verified_sources[row["rel"]]:
                raise RuntimeError("Source changed after batch verification: " + str(src))
            if row["action"] == "migrate" and row["kind"] == "file":
                target_verify(output_path(root, row["rel"]), row)
            elif row["action"] == "duplicate":
                target_verify(output_path(roots[row["canonical_root"]], row["canonical_rel"]), row)
            elif row["kind"] == "link" and row["action"] == "migrate":
                record = Path(str(output_path(root, row["rel"])) + ".link-record.json")
                obj = json.loads(record.read_text(encoding="utf-8"))
                if obj["target"] != row["target"] or obj["sha256"] != row["sha"]:
                    raise ValueError("Invalid link record")
            delete_one(src, row, root["source"])
            db.execute("UPDATE entries SET status='removed' WHERE root=? AND rel=?", (root["id"], row["rel"]))
            event(db, "source_removed", root["id"], row["rel"], row["action"])
            counters["removed"] += 1
            counters["bytes_removed"] += row["size"]
            progress("remove-source")
        db.commit()
        for folder in db.execute("SELECT rel FROM dirs WHERE root=? ORDER BY length(rel) DESC", (root["id"],)).fetchall():
            path = checked(Path(root["source"]) / folder["rel"], root["source"])
            if os.path.isdir(native(path)):
                os.rmdir(native(path))
    # Current paths are retained except explicitly inventoried runtime caches.
    root = roots.get("current")
    if root:
        for row in db.execute("SELECT * FROM entries WHERE root='current' AND action IN ('cache','duplicate') AND status<>'removed'").fetchall():
            path = source_path(root, row)
            if not os.path.lexists(native(path)):
                db.execute("UPDATE entries SET status='removed' WHERE root='current' AND rel=?", (row["rel"],))
                continue
            verify_file(path, row, source=True)
            if row["action"] == "duplicate":
                target_verify(output_path(roots[row["canonical_root"]], row["canonical_rel"]), row)
            delete_one(path, row, root["source"])
            db.execute("UPDATE entries SET status='removed' WHERE root='current' AND rel=?", (row["rel"],))
            event(db, "current_removed", "current", row["rel"], row["action"])
            progress("current-cache")
        for folder in db.execute("SELECT rel FROM dirs WHERE root='current' AND rel<>'' ORDER BY length(rel) DESC").fetchall():
            entries = rows_under(db, "current", folder["rel"])
            if entries and all(r["action"] in {"cache", "duplicate"} for r in entries):
                path = checked(Path(root["source"]) / folder["rel"], root["source"])
                if os.path.isdir(native(path)) and not is_link(os.lstat(native(path))):
                    try:
                        os.rmdir(native(path))
                    except OSError as exc:
                        if getattr(exc, "winerror", None) != 145 and exc.errno not in {39, 66}:
                            raise
    db.commit()
    db.execute("INSERT OR REPLACE INTO meta VALUES('apply_complete',?)", (now(),))
    db.commit()
    write_json(batch / "apply-summary.json", summary(db))


def verify(db, batch):
    roots = {r["id"]: r for r in db.execute("SELECT * FROM roots")}
    failures = []
    checked_count = 0
    verified_targets = {}
    last = time.monotonic()
    mapping = batch / "path-map.jsonl"
    with open(native(mapping), "w", encoding="utf-8") as stream:
        for row in db.execute("SELECT * FROM entries ORDER BY root,rel"):
            root = roots[row["root"]]
            try:
                if row["action"] == "cache":
                    continue
                cr = roots[row["canonical_root"]] if row["action"] == "duplicate" else root
                rel = row["canonical_rel"] if row["action"] == "duplicate" else row["rel"]
                dst = output_path(cr, rel)
                if row["kind"] == "file":
                    fingerprint = identity(dst)
                    if verified_targets.get(str(dst)) != (fingerprint, row["sha"]):
                        verify_file(dst, row)
                        verified_targets[str(dst)] = (identity(dst), row["sha"])
                else:
                    if root["active"]:
                        verify_file(dst, row)
                    else:
                        dst = Path(str(dst) + ".link-record.json")
                        obj = json.loads(dst.read_text(encoding="utf-8"))
                        if obj["sha256"] != row["sha"] or obj["target"] != row["target"]:
                            raise ValueError("Invalid preserved link record")
                stream.write(json.dumps(dict(source=str(Path(root["source"]) / row["rel"]), retained=str(dst), sha256=row["sha"], action=row["action"]), ensure_ascii=False) + "\n")
                checked_count += 1
            except Exception as exc:
                failures.append(dict(root=row["root"], path=row["rel"], error=repr(exc)))
            if time.monotonic() - last > 15:
                print(json.dumps(dict(stage="verify", files=checked_count, failures=len(failures))), flush=True)
                last = time.monotonic()
                resource_guard()
    result = dict(completed_utc=now(), verified_files=checked_count, failures=failures, summary=summary(db))
    write_json(batch / "verification.json", result)
    if failures:
        raise RuntimeError(str(len(failures)) + " retained-file verification failures")
    return result


def summary(db):
    return [dict(r) for r in db.execute("SELECT root,action,status,count(*) AS files,sum(size) AS bytes FROM entries GROUP BY root,action,status ORDER BY root,action,status")]


def refresh_maintenance(db):
    """Bind this task's explicitly named implementation edits before planning."""
    if db.execute("SELECT 1 FROM meta WHERE key='applied'").fetchone():
        raise ValueError("Implementation identities are frozen after apply starts")
    root = db.execute("SELECT * FROM roots WHERE id='current'").fetchone()
    names = [".gitignore", "tools/MaintainWorkspaces.py", "tests/test_workspace_maintenance.py", "docs/workspace-maintenance.zh-CN.md"]
    for rel in names:
        path = checked(Path(root["source"]) / rel, root["source"])
        s = os.lstat(native(path))
        if is_link(s) or not stat.S_ISREG(s.st_mode):
            raise ValueError("Maintenance source must be a regular file")
        old = db.execute("SELECT sha FROM entries WHERE root='current' AND rel=?", (rel,)).fetchone()
        sha = digest(path)
        event(db, "implementation_identity", "current", rel, json.dumps(dict(previous_sha256=old[0] if old else None, execution_sha256=sha)))
        db.execute("INSERT OR REPLACE INTO entries(root,rel,kind,size,mtime,dev,ino,sha,attrs,cache,action) VALUES('current',?,'file',?,?,?,?,?,?,0,'keep')", (rel, s.st_size, s.st_mtime_ns, s.st_dev, s.st_ino, sha, getattr(s, "st_file_attributes", 0)))
    db.commit()


def locate(db, source):
    for root in db.execute("SELECT * FROM roots ORDER BY length(source) DESC"):
        if within(source, root["source"]):
            rel = Path(os.path.relpath(source, root["source"])).as_posix()
            row = db.execute("SELECT * FROM entries WHERE root=? AND rel=?", (root["id"], rel)).fetchone()
            if not row:
                raise KeyError("No inventoried file at " + str(source))
            if row["action"] == "cache":
                return dict(source=str(source), action="cache", retained=None)
            cr = db.execute("SELECT * FROM roots WHERE id=?", (row["canonical_root"],)).fetchone() if row["action"] == "duplicate" else root
            dst = output_path(cr, row["canonical_rel"] if row["action"] == "duplicate" else rel)
            if row["kind"] == "link" and not cr["active"]:
                dst = Path(str(dst) + ".link-record.json")
            return dict(source=str(source), action=row["action"], retained=str(dst), sha256=row["sha"])
    raise ValueError("Source is outside selected roots")


def restore(db, root_id, destination):
    """Reconstruct one original tree into a fresh directory, entirely offline."""
    root = db.execute("SELECT * FROM roots WHERE id=?", (root_id,)).fetchone()
    if not root:
        raise ValueError("Unknown root id")
    if os.path.lexists(native(destination)):
        raise FileExistsError("Restore destination must be new: " + str(destination))
    destination.mkdir(parents=True)
    count = 0
    for row in db.execute("SELECT * FROM entries WHERE root=? AND action<>'cache' ORDER BY rel", (root_id,)):
        found = locate(db, Path(root["source"]) / row["rel"])
        target = checked(destination / row["rel"], destination)
        Path(native(target.parent)).mkdir(parents=True, exist_ok=True)
        if row["kind"] == "link":
            write_json(Path(str(target) + ".link-record.json"), dict(original_path=row["rel"], target=row["target"], sha256=row["sha"], attributes=row["attrs"]))
        else:
            source = Path(found["retained"])
            verify_file(source, row)
            shutil.copy2(native(source), native(target), follow_symlinks=False)
            verify_file(target, row)
        count += 1
    return dict(root=root_id, destination=str(destination), files=count)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", nargs="?", choices=["inventory", "audit-git-temp", "refresh-maintenance", "plan", "apply", "verify", "verify-git", "locate", "restore", "status"], default="status")
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--project", type=Path, default=ROOT)
    parser.add_argument("--spec", type=Path, help="Explicit JSON roots; saved immutably in the batch")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--root-id")
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    resource_guard()
    db = connect(args.batch)
    try:
        import psutil
        with open(native(args.batch / "invocations.jsonl"), "a", encoding="utf-8") as stream:
            stream.write(json.dumps(dict(at=now(), stage=args.stage, execute=args.execute, script_sha256=digest(__file__), python=sys.version, pid=os.getpid(), process_created_UTC=datetime.fromtimestamp(psutil.Process().create_time(), timezone.utc).isoformat())) + "\n")
        if args.stage == "inventory":
            spec = json.loads(args.spec.read_text(encoding="utf-8")) if args.spec else default_spec(args.project)
            scan(db, args.batch, spec)
        elif args.stage == "plan":
            plan(db, args.batch)
        elif args.stage == "audit-git-temp":
            audit_git_temps(db, args.batch)
        elif args.stage == "refresh-maintenance":
            if not args.execute:
                print("Preview only. Refresh the four named maintenance files with --execute.")
            else:
                refresh_maintenance(db)
        elif args.stage == "apply":
            if not args.execute:
                print("Preview only. Review plan.json; --execute is required.")
                print(json.dumps(summary(db)))
            else:
                apply(db, args.batch)
        elif args.stage == "verify":
            verify(db, args.batch)
        elif args.stage == "verify-git":
            verify_git(db, args.batch)
        elif args.stage == "locate":
            if not args.source:
                parser.error("locate requires --source")
            print(json.dumps(locate(db, args.source), ensure_ascii=False))
        elif args.stage == "restore":
            if not args.root_id or not args.destination:
                parser.error("restore requires --root-id and --destination")
            if not args.execute:
                print("Preview only. Restore requires --execute and a new destination.")
            else:
                print(json.dumps(restore(db, args.root_id, args.destination), ensure_ascii=False))
        else:
            print(json.dumps(summary(db)))
    except Exception as exc:
        write_json(args.batch / ("failure-" + str(time.time_ns()) + ".json"), dict(at=now(), stage=args.stage, execution_status="failed", error=repr(exc), traceback=traceback.format_exc()))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
