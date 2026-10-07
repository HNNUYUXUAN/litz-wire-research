"""Reject a release conclusion whose selection, state or readback is incomplete."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
spec = importlib.util.spec_from_file_location("freeze", ROOT / "src" / "FreezePreManuscriptCompute.py")
freeze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(freeze)


class ReleaseGateTests(unittest.TestCase):
    def test_original_wrapper_schemas_keep_native_exit_unknown(self):
        for key in ("wrapper_exit_code", "wrapper_process_exit_code"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary)
                evidence = folder / "wrapper_resource_observation.json"
                evidence.write_text(json.dumps({key: 1, "kernel_exit_code": None}), encoding="utf-8")
                with patch.object(freeze, "ROOT", folder):
                    process, source = freeze.process_evidence(folder)
                self.assertIsNone(process["process_exit_code"])
                self.assertEqual(process["wrapper_exit_code"], 1)
                self.assertEqual(source["sha256"], freeze.closure.digest(evidence))
                self.assertFalse((folder / "process_status.json").exists())

    def test_missing_native_and_wrapper_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "Missing original process"):
                freeze.process_evidence(Path(temporary))

    def test_all_inventory_tasks_require_terminal_decisions(self):
        with patch.object(freeze.closure, "inventory", return_value=[{"task_id": "required_case"}]):
            with self.assertRaisesRegex(ValueError, "missing"):
                freeze.validate_selection({"task_finalizations": {}})

    def test_running_is_not_a_terminal_state(self):
        value = {"task_finalizations": {"case": {"final_status": "running", "reason": "still calculating", "source_run_ids": ["saved"]}}}
        with patch.object(freeze.closure, "inventory", return_value=[{"task_id": "case"}]):
            with self.assertRaisesRegex(ValueError, "terminal"):
                freeze.validate_selection(value)

    def test_modified_selection_is_rejected_before_release_or_folder_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            selection = folder / "selection.json"
            selection.write_text(json.dumps({"task_finalizations": {}}), encoding="utf-8")
            index = folder / "index.json"
            index.write_text(json.dumps({"closure_selection": {"selection_sha256": "original_sha"}}), encoding="utf-8")
            with patch.object(freeze.closure, "INDEX", index), patch.object(freeze, "validate_selection", return_value={}):
                with self.assertRaisesRegex(ValueError, "differs from.*pinned"):
                    freeze.release(selection, "new_release", "audit")

    def test_decisions_must_equal_finalized_audited_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            selection = folder / "selection.json"
            selection.write_text(json.dumps({"task_finalizations": {"case": {"final_status": "completed_scope_pass"}}}), encoding="utf-8")
            index = folder / "index.json"
            index.write_text(json.dumps({"closure_selection": {"selection_sha256": freeze.closure.digest(selection)}}), encoding="utf-8")
            state = folder / "state.json"
            state.write_text(json.dumps({"finalized_tasks": {"case": {"final_status": "completed_scope_fail"}}}), encoding="utf-8")
            with patch.object(freeze.closure, "INDEX", index), patch.object(freeze.closure, "STATE", state), patch.object(freeze, "validate_selection", return_value={"case": {"final_status": "completed_scope_pass"}}):
                with self.assertRaisesRegex(ValueError, "finalized task state"):
                    freeze.release(selection, "new_release", "audit")


if __name__ == "__main__":
    unittest.main()
