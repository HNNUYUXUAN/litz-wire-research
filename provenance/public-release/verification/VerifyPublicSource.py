"""Download a public tagged source ZIP and verify every file against local Git.

This helper reads local committed objects, never clones or fetches through Git.
It extracts only after complete byte verification, into a new directory.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import urllib.request
from urllib.parse import quote
import zipfile

from AnonymousHTTP import opener


def now():
    return datetime.now(timezone.utc).isoformat()


def git_manifest(root, commit):
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("A full lowercase commit SHA is required")
    git = ["git", "-c", "safe.directory=" + str(root), "-C", str(root)]
    resolved = subprocess.run(git + ["rev-parse", "--verify", commit + "^{commit}"],
                              check=True, capture_output=True, text=True).stdout.strip()
    if resolved != commit:
        raise ValueError("Commit identity did not resolve exactly")
    tree = subprocess.run(git + ["ls-tree", "-r", "-z", "--full-tree", commit],
                          check=True, capture_output=True).stdout
    records = []
    for entry in tree.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, object_id = metadata.decode("ascii").split()
        if mode not in {"100644", "100755"} or kind != "blob":
            raise ValueError("Unsupported Git entry mode")
        records.append({"path": raw_path.decode("utf-8"), "mode": mode, "git_blob": object_id})
    with subprocess.Popen(git + ["cat-file", "--batch"], stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        try:
            for record in records:
                process.stdin.write((record["git_blob"] + "\n").encode("ascii"))
                process.stdin.flush()
                header = process.stdout.readline().decode("ascii").strip().split()
                if len(header) != 3 or header[:2] != [record["git_blob"], "blob"]:
                    raise ValueError("Git object stream identity mismatch")
                size = int(header[2])
                remaining, digest = size, hashlib.sha256()
                while remaining:
                    block = process.stdout.read(min(1024 * 1024, remaining))
                    if not block:
                        raise ValueError("Truncated local Git object")
                    digest.update(block)
                    remaining -= len(block)
                if process.stdout.read(1) != b"\n":
                    raise ValueError("Malformed Git object stream")
                record.update(bytes=size, sha256=digest.hexdigest(), hash_basis="raw-bytes")
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)
    return sorted(records, key=lambda row: row["path"])


def validate_path(path):
    relative = PurePosixPath(path)
    if relative.is_absolute() or ".." in relative.parts or "\\" in path or ":" in path:
        raise ValueError("Archive member escapes its destination")
    for part in relative.parts:
        if part in {"", ".", ".."} or part.endswith((" ", ".")):
            raise ValueError("Unsupported archive member name")
        stem = part.split(".")[0].upper()
        if stem in {"CON", "PRN", "AUX", "NUL", *["COM" + str(n) for n in range(1, 10)], *["LPT" + str(n) for n in range(1, 10)]}:
            raise ValueError("Reserved Windows archive member name")


def inspect_zip(archive, manifest):
    expected = {row["path"]: row for row in manifest}
    files, roots, normalized = {}, set(), set()
    with zipfile.ZipFile(archive) as bundle:
        for entry in bundle.infolist():
            validate_path(entry.filename.rstrip("/"))
            mode = entry.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError("Archive symlinks are not accepted")
            parts = PurePosixPath(entry.filename).parts
            roots.add(parts[0])
            if entry.is_dir():
                continue
            if len(parts) < 2:
                raise ValueError("Source archive has no common prefix")
            path = "/".join(parts[1:])
            if path.casefold() in normalized:
                raise ValueError("Duplicate or case-colliding archive member")
            normalized.add(path.casefold())
            files[path] = entry
        if len(roots) != 1 or set(files) != set(expected):
            raise ValueError("Source archive file inventory differs from committed Git tree")
        for path, entry in files.items():
            record = expected[path]
            if entry.file_size != record["bytes"]:
                raise ValueError("Source archive member length mismatch: " + path)
            digest, count = hashlib.sha256(), 0
            with bundle.open(entry) as stream:
                while block := stream.read(1024 * 1024):
                    count += len(block)
                    if count > record["bytes"]:
                        raise ValueError("Archive member exceeds committed length")
                    digest.update(block)
            if count != record["bytes"] or digest.hexdigest() != record["sha256"]:
                raise ValueError("Source archive member hash mismatch: " + path)
    return files


def extract_verified(archive, manifest, destination):
    files = inspect_zip(archive, manifest)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive) as bundle:
        for path, entry in files.items():
            target = (destination / path).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise ValueError("Extraction path escapes destination")
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(entry) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
    return len(files)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--tag", default="v1.0.0-rc.3")
    parser.add_argument("--repository", default="HNNUYUXUAN/litz-wire-research")
    parser.add_argument("--directory", required=True, type=Path)
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository):
        raise ValueError("Invalid repository identity")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", args.tag):
        raise ValueError("This verifier accepts a simple tag name")
    root, directory = args.root.resolve(), args.directory.resolve()
    manifest = git_manifest(root, args.commit)
    directory.mkdir(parents=True, exist_ok=False)
    archive = directory / (args.tag + ".zip")
    extracted = directory / "source checkout"
    receipt_path = directory / "source-verification.json"
    requests = []
    record = {"schema_version": 1, "repository": args.repository, "tag": args.tag,
              "source_commit": args.commit, "started_at": now(), "status": "running",
              "authentication": "none", "requests": requests, "git_files": manifest}
    def save():
        receipt_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    save()
    try:
        url = "https://github.com/" + args.repository + "/archive/refs/tags/" + quote(args.tag, safe="") + ".zip"
        request = urllib.request.Request(url, headers={"User-Agent": "litz-public-source-verifier/1", "Accept-Encoding": "identity"})
        maximum = sum(row["bytes"] for row in manifest) + max(1024 * 1024, len(manifest) * 2048)
        digest, count = hashlib.sha256(), 0
        with opener(requests).open(request, timeout=90) as response, archive.open("xb") as output:
            if response.status != 200:
                raise ValueError("Source archive HTTP status is not 200")
            while block := response.read(1024 * 1024):
                count += len(block)
                if count > maximum:
                    raise ValueError("Source archive exceeds committed tree size bound")
                digest.update(block)
                output.write(block)
        checked = extract_verified(archive, manifest, extracted)
        record.update(status="passed", checked_at=now(), source_directory=str(extracted),
                      zip={"name": archive.name, "sha256": digest.hexdigest(), "bytes": count},
                      method="GET", scope="full-body", http_status=200,
                      verified_files=checked, verified_raw_bytes=sum(row["bytes"] for row in manifest),
                      full_git_tree_match=True, cache_hits=0)
        save()
        print(json.dumps({key: record[key] for key in ("status", "source_commit", "verified_files", "source_directory")}))
        return 0
    except Exception as error:
        # Network error strings may contain signed URLs; preserve classifications.
        record.update(status="failed", checked_at=now(), error_type=type(error).__name__)
        save()
        print(json.dumps({"status": "failed", "error_type": type(error).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
