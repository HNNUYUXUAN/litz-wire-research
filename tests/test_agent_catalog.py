"""Discovery must preserve scientific status and avoid untracked local inputs."""
import contextlib
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import unittest

HERE = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("LITZ_CATALOG_TEST_ROOT", str(HERE)))
SPEC = importlib.util.spec_from_file_location("agent_catalog", HERE / "tools/BuildAgentCatalog.py")
CATALOG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CATALOG)


class CatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = CATALOG.build(ROOT)

    def test_registered_coverage_and_failed_physics_retained(self):
        self.assertEqual(self.catalog["counts"], {"route": 7, "adapter": 3, "skill": 9, "workflow": 5, "case": 6, "manuscript": 6})
        case = next(item for item in self.catalog["items"] if item["id"] == "case/aphi-diagnostics")
        self.assertTrue(any(run["execution_status"] == "completed" and
                            run["physical_acceptance_status"] == "failed_retained_phi_gauge"
                            for run in case["recorded_runs"]))

    def test_inputs_exclude_ignored_evidence_and_bind_raw_bytes(self):
        for resource in self.catalog["input_resources"]:
            self.assertFalse(resource["path"].startswith(("outputs/", "data/evidence/")))
            self.assertEqual(resource["hash_basis"], "raw-bytes")
            self.assertEqual(resource["sha256"], hashlib.sha256((ROOT / resource["path"]).read_bytes()).hexdigest())

    def test_manuscripts_identify_current_sources_and_readings(self):
        for item in self.catalog["items"]:
            if item["kind"] == "manuscript":
                self.assertEqual(len(item["resources"]), 2)
                self.assertTrue(item["resources"][0]["path"].endswith('/main.tex'))
                self.assertTrue(item["resources"][1]["path"].startswith('publications/reading/'))
                self.assertTrue(all(r["path"].endswith('.tex') for r in item["chapter_sources"]))
                self.assertIn(item["layout"], ('single', 'ieee-journal'))

    def test_deterministic_generation(self):
        self.assertEqual(CATALOG.outputs(self.catalog), CATALOG.outputs(CATALOG.build(ROOT)))

    def test_check_detects_modified_output_without_repairing_it(self):
        with tempfile.TemporaryDirectory(prefix="litz catalog check ") as directory:
            args = ["--root", str(ROOT), "--output-dir", directory]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(CATALOG.main(args), 0)
                self.assertEqual(CATALOG.main(args + ["--check"]), 0)
                path = Path(directory) / "llms.txt"
                path.write_bytes(b"changed\n")
                self.assertEqual(CATALOG.main(args + ["--check"]), 1)
            self.assertEqual(path.read_bytes(), b"changed\n")

    def test_untracked_and_escape_paths_are_rejected(self):
        repository = CATALOG.Repository(ROOT)
        for path in ("../outside.txt", "outputs/ignored.json", "C:/absolute.json"):
            with self.assertRaises(ValueError):
                repository.read_bytes(path)


if __name__ == "__main__":
    unittest.main()
