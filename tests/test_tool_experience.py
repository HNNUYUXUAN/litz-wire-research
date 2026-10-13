"""Check command discovery, truthful probes, and a first analytical run."""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from litz_research.cli import RUN_MODELS, _aedt_executable, _probe, doctor, main, model_catalog, run_plan
from litz_research.common import project


class ToolExperienceTests(unittest.TestCase):
    def setUp(self):
        self.root = project()

    def test_catalogue_entry_points_and_evidence_datasets_exist(self):
        datasets = json.loads((self.root / "data/catalog.json").read_text(encoding="utf-8"))["datasets"]
        models = model_catalog(self.root)
        self.assertEqual(len({item["id"] for item in models}), len(models))
        for item in models:
            self.assertTrue(item["source_available"], item["id"])
            for name in item["execution_datasets"] + item["evidence_datasets"]:
                self.assertIn(name, datasets)
        self.assertEqual({m["id"] for m in models if m["interface"] == "cli_run"}, set(RUN_MODELS)|{'rt0','aphi','ansys','wolfram'})
        self.assertTrue(all('legacy_command' in m for m in models))

    def test_models_are_discoverable_without_solver_probes(self):
        output = io.StringIO()
        with patch("litz_research.cli.subprocess.run") as run, redirect_stdout(output):
            self.assertEqual(main(["--project", str(self.root), "models", "ansys", "--json"]), 0)
        run.assert_not_called()
        entry = json.loads(output.getvalue())
        self.assertIn("--case preflight", entry["command"])
        self.assertIn("--task preflight", entry["legacy_command"])
        self.assertEqual(entry["interface"], "cli_run")

    def test_dry_run_reports_missing_sources_without_creating_outputs(self):
        with tempfile.TemporaryDirectory(prefix="Litz Missing Inputs ") as tmp:
            root = Path(tmp)
            plan = run_plan(root, "analytic", "example_01")
            self.assertEqual(plan["dispatch_status"], "blocked")
            self.assertIn("configs/reference_values.json", " ".join(plan["diagnostics"]))
            self.assertFalse((root / "outputs").exists())

    def test_run_identity_is_checked_before_execution(self):
        with self.assertRaises(ValueError):
            run_plan(self.root, "analytic", "../other")
        with tempfile.TemporaryDirectory(prefix="Litz Existing Run ") as tmp:
            root = Path(tmp)
            (root / "outputs/example").mkdir(parents=True)
            plan = run_plan(root, "analytic", "example")
            self.assertIn("choose a new --run-id", " ".join(plan["diagnostics"]))

    def test_probe_reports_nonzero_exit_and_timeout(self):
        with patch("litz_research.cli.subprocess.run", return_value=subprocess.CompletedProcess([], 17, "", "runtime unavailable")):
            probe = _probe(["example"])
        self.assertEqual(probe["status"], "failed")
        self.assertEqual(probe["exit_code"], 17)
        with patch("litz_research.cli.subprocess.run", side_effect=subprocess.TimeoutExpired(["example"], 15)):
            self.assertEqual(_probe(["example"])["status"], "timeout")

    def test_ansys_student_executable_is_discovered_from_environment_root(self):
        with tempfile.TemporaryDirectory(prefix="Ansys Student ") as tmp:
            executable = Path(tmp) / "ansysedtsv.exe"
            executable.write_bytes(b"installation marker")
            with patch("litz_research.cli.tool", return_value=None), patch.dict("os.environ", {"ANSYSEMSV_ROOT252": tmp}, clear=True):
                self.assertEqual(Path(_aedt_executable(self.root)), executable)

    def test_doctor_preserves_existing_fields_and_observation_scope(self):
        def probe(command, timeout=15):
            if command[0] == "test-xelatex":
                return {"status": "failed", "exit_code": 1, "version_lines": ["runtime initialization failed"]}
            return {"status": "passed", "exit_code": 0, "version_lines": ["test version"]}
        with patch("litz_research.cli.tool", side_effect=lambda root, name: "test-" + name), patch("litz_research.cli._probe", side_effect=probe):
            result = doctor(self.root)
        for field in ["version", "python", "system", "tools", "fonts", "resource_policy", "solver_requirements", "versions"]:
            self.assertIn(field, result)
        self.assertTrue(result["tools"]["xelatex"])
        self.assertEqual(result["versions"]["xelatex"]["status"], "failed")
        self.assertEqual(result["capabilities"]["pdf_compilation"]["status"], "dependencies_required")
        self.assertEqual(result["wolfram_kernel"]["status"], "not_probed")
        self.assertEqual(result["ansys_installation"]["license_status"], "not_probed")

    def test_json_output_uses_utf8_in_a_legacy_encoded_console(self):
        raw = io.BytesIO()
        output = io.TextIOWrapper(raw, encoding="gbk")
        with patch("litz_research.cli.doctor", return_value={"version": "© Wolfram φ"}), redirect_stdout(output):
            self.assertEqual(main(["--project", str(self.root), "doctor"]), 0)
        output.flush()
        self.assertEqual(json.loads(raw.getvalue().decode("utf-8"))["version"], "© Wolfram φ")

    def test_analytical_cli_in_checkout_with_spaces(self):
        with tempfile.TemporaryDirectory(prefix="Litz First Reading ") as tmp:
            root = Path(tmp)
            for name in ["configs/reference_parameters.json", "configs/reference_values.json", "manuscript/publication.json"]:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.root / name, target)
            output, errors = io.StringIO(), io.StringIO()
            args = ["--project", str(root), "run", "analytic", "--run-id", "first_example"]
            with redirect_stdout(output), redirect_stderr(errors):
                self.assertEqual(main([*args, "--dry-run"]), 0)
            self.assertFalse((root / "outputs").exists())
            output = io.StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                self.assertEqual(main(args), 0)
            result = json.loads(output.getvalue())
            self.assertEqual(result["physical_acceptance_status"], "passed")
            self.assertEqual(len(result["checks"]), 12)
            self.assertTrue((root / "outputs/first_example/radial_current_density.csv").is_file())
            with redirect_stderr(errors):
                self.assertEqual(main(args), 1)
            self.assertIn("choose a new --run-id", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
