"""Safety checks for destructive local workspace consolidation."""
import importlib.util
from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import hashlib
import struct
import zlib

SPEC = importlib.util.spec_from_file_location("maintenance", Path(__file__).resolve().parents[1] / "tools/MaintainWorkspaces.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class WorkspaceMaintenanceTests(unittest.TestCase):
    def test_runtime_and_retained_material_are_not_disposable_cache(self):
        for active in (True, False):
            for path in ('.conda/project/Lib/__pycache__/module.pyc',
                         '.local-archive/environments/Lib/__pycache__/module.pyc',
                         '.local-library/cache/unique-source.pyc'):
                self.assertFalse(M.cache_file(path, active), path)
        self.assertTrue(M.cache_file('python/__pycache__/module.pyc', True))

    def test_process_guard_distinguishes_sibling_path_prefixes(self):
        root = "C:/Workspaces/repos/litz-wire-research"
        self.assertFalse(M.command_uses_root('python C:/Workspaces/repos/litz-wire-research-opensource/tools/check.py', root))
        self.assertTrue(M.command_uses_root('python C:\\Workspaces\\repos\\litz-wire-research\\tools\\check.py', root))
        self.assertTrue(M.command_uses_root('git -C "C:/Workspaces/repos/litz-wire-research" status', root))

    @contextmanager
    def directory(self):
        self.db = None
        with tempfile.TemporaryDirectory() as td:
            try:
                yield td
            finally:
                if self.db is not None:
                    self.db.close()

    def fixture(self, base):
        current, old = base / "current", base / "old"
        current.mkdir(); old.mkdir()
        destination = current / ".local-archive/workspaces/old"
        spec = [dict(id="current", source=str(current), destination=str(current), active=True), dict(id="old", source=str(old), destination=str(destination), active=False)]
        batch = current / ".local-archive/maintenance/test"
        db = M.connect(batch)
        self.db = db
        return current, old, destination, batch, db, spec

    def test_changed_file_blocks_deletion_and_does_not_overwrite(self):
        with self.directory() as td:
            current, old, dest, batch, db, spec = self.fixture(Path(td))
            (old / "input.json").write_text("first")
            M.scan(db, batch, spec); M.plan(db, batch)
            (old / "input.json").write_text("changed")
            with self.assertRaisesRegex(RuntimeError, "changed|mismatch"):
                M.apply(db, batch)
            self.assertEqual((old / "input.json").read_text(), "changed")
            self.assertFalse((dest / "input.json").exists())

    def test_unicode_long_path_conflict_and_resume(self):
        with self.directory() as td:
            current, old, dest, batch, db, spec = self.fixture(Path(td))
            relative = Path("资料 " + "长" * 35) / ("阶段 " + "段" * 35) / ("结果 " + "流" * 35) / "电流.json"
            source = Path(M.native(old / relative))
            source.parent.mkdir(parents=True)
            source.write_text("{\"phase\": 1}", encoding="utf-8")
            (current / "same.txt").write_text("current")
            (old / "same.txt").write_text("historical")
            cache = old / "__pycache__"
            cache.mkdir(); (cache / "temporary.pyc").write_bytes(b"cache")
            M.scan(db, batch, spec); M.plan(db, batch)
            M.apply(db, batch)
            M.apply(db, batch)
            result = M.verify(db, batch)
            self.assertFalse(result["failures"])
            self.assertFalse(old.exists())
            self.assertEqual(Path(M.native(dest / relative)).read_text(encoding="utf-8"), '{"phase": 1}')
            self.assertEqual((dest / "same.txt").read_text(), "historical")
            self.assertEqual((current / "same.txt").read_text(), "current")
            self.assertFalse((dest / "__pycache__/temporary.pyc").exists())
            found = M.locate(db, old / relative)
            self.assertEqual(Path(found["retained"]), dest / relative)
            restored = Path(td) / "Restored With Spaces"
            M.restore(db, "old", restored)
            self.assertEqual(Path(M.native(restored / relative)).read_text(encoding="utf-8"), '{"phase": 1}')

    def test_complete_duplicate_mapping_and_new_source_file(self):
        with self.directory() as td:
            current, old, dest, batch, db, spec = self.fixture(Path(td))
            for root in [current, old]:
                p = root / "outputs/verified"
                p.mkdir(parents=True)
                (p / "field.wxf").write_bytes(b"x" * (1024 * 1024))
            M.scan(db, batch, spec); M.plan(db, batch)
            self.assertEqual(db.execute("SELECT action FROM entries WHERE root='old'").fetchone()[0], "duplicate")
            (old / "new-user-file.txt").write_text("keep")
            with self.assertRaisesRegex(RuntimeError, "membership changed"):
                M.apply(db, batch)
            self.assertTrue((old / "outputs/verified/field.wxf").exists())

    def test_boundary_and_linked_parent_rejected(self):
        with self.directory() as td:
            base = Path(td)
            selected, outside = base / "selected", base / "outside"
            selected.mkdir(); outside.mkdir()
            with self.assertRaisesRegex(ValueError, "outside"):
                M.checked(outside / "file", selected)
            try:
                (selected / "escape").symlink_to(outside, target_is_directory=True)
            except OSError:
                # Model the Windows reparse-point bit when this account cannot
                # create a real link; the exact production boundary guard runs.
                (selected / "escape").mkdir()
                link_ino = os.lstat(M.native(selected / "escape")).st_ino
                with patch.object(M, "is_link", side_effect=lambda s: s.st_ino == link_ino):
                    with self.assertRaisesRegex(ValueError, "Linked ancestor"):
                        M.checked(selected / "escape/file", selected)
                return
            with self.assertRaisesRegex(ValueError, "Linked ancestor"):
                M.checked(selected / "escape/file", selected)

    def test_resume_after_unlink_before_commit(self):
        with self.directory() as td:
            current, old, dest, batch, db, spec = self.fixture(Path(td))
            for name in ["a", "b"]:
                (old / name).write_text(name)
            M.scan(db, batch, spec); M.plan(db, batch)
            original_delete = M.delete_one
            calls = []
            def interrupted(path, row, root):
                original_delete(path, row, root)
                calls.append(path)
                if len(calls) == 1:
                    raise RuntimeError("simulated shutdown after unlink")
            with patch.object(M, "delete_one", side_effect=interrupted):
                with self.assertRaisesRegex(RuntimeError, "simulated"):
                    M.apply(db, batch)
            db.rollback()
            M.apply(db, batch)
            self.assertFalse(M.verify(db, batch)["failures"])
            self.assertFalse(old.exists())

    def test_existing_different_destination_is_never_overwritten(self):
        with self.directory() as td:
            current, old, dest, batch, db, spec = self.fixture(Path(td))
            (old / "user.txt").write_text("source")
            M.scan(db, batch, spec); M.plan(db, batch)
            dest.mkdir(parents=True)
            (dest / "user.txt").write_text("independent modification")
            with self.assertRaisesRegex(RuntimeError, "mismatch"):
                M.apply(db, batch)
            self.assertEqual((dest / "user.txt").read_text(), "independent modification")
            self.assertTrue((old / "user.txt").exists())

    def test_git_temporary_requires_exact_retained_object_prefix(self):
        with self.directory() as td:
            current, old, dest, batch, db, spec = self.fixture(Path(td))
            raw = b"retained scientific data" * 10000
            sha = hashlib.sha256(raw).hexdigest()
            obj = old / ".git/lfs/objects" / sha[:2] / sha[2:4] / sha
            obj.parent.mkdir(parents=True); obj.write_bytes(raw)
            size = len(raw); encoded = bytearray([(3 << 4) | (size & 15)])
            size >>= 4
            if size: encoded[0] |= 128
            while size:
                b = size & 127; size >>= 7
                encoded.append(b | (128 if size else 0))
            packed = b"PACK" + struct.pack(">II", 2, 1) + encoded + zlib.compress(raw)
            folder = old / ".git/objects/pack"
            folder.mkdir(parents=True)
            (folder / "tmp_pack_verified").write_bytes(packed[:len(packed)//2])
            (folder / "tmp_pack_unmatched").write_bytes(packed[:20] + b"independent bytes")
            M.scan(db, batch, spec)
            result = M.audit_git_temps(db, batch)
            self.assertEqual(result["verified_files"], 1)
            self.assertEqual(len(result["preserved_unresolved"]), 1)
            M.plan(db, batch)
            actions = dict(db.execute("SELECT rel,action FROM entries WHERE root='old'"))
            self.assertEqual(actions[".git/objects/pack/tmp_pack_verified"], "cache")
            self.assertEqual(actions[".git/objects/pack/tmp_pack_unmatched"], "migrate")

    def test_duplicate_chains_resolve_to_retained_current_data(self):
        with self.directory() as td:
            current, old, dest, batch, db, spec = self.fixture(Path(td))
            rel = Path("outputs/quark_backup_20261020_01/restore_one/run/data.wxf")
            canonical = current / "data/original/run/data.wxf"
            for path in [current / rel, old / rel, canonical]:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"field" * 220000)
            M.scan(db, batch, spec); M.plan(db, batch)
            row = db.execute("SELECT canonical_root,canonical_rel FROM entries WHERE root='old'").fetchone()
            self.assertEqual(tuple(row), ("current", "data/original/run/data.wxf"))
            M.apply(db, batch)
            self.assertTrue(canonical.is_file())
            self.assertFalse((current / rel).exists())
            self.assertFalse(M.verify(db, batch)["failures"])


if __name__ == "__main__":
    unittest.main()
