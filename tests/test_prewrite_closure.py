import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("closure", ROOT / "src" / "PreManuscriptClosure.py")
closure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(closure)
CFG = closure.read(closure.DEFAULT_CONFIG)


class ClosureControllerTests(unittest.TestCase):
    def setUp(self):
        self.high = {"RAM_bytes": 64*closure.GIB, "free_RAM_bytes": 54*closure.GIB,
                     "logical_processors": 32, "gpu": {"memory_MiB": 16384}}
        self.low = {"RAM_bytes": 32*closure.GIB, "free_RAM_bytes": 29*closure.GIB,
                    "logical_processors": 8, "gpu": None}

    def test_low_reading_is_actual_hardware_acceptance(self):
        self.assertEqual(closure.check_profile(self.low, "low32", {}, CFG, strict=True)[0], [])
        self.assertIn("actual_low32_host_required_for_acceptance", closure.check_profile(self.high, "low32", {}, CFG, strict=True)[0])

    def test_cpu_does_not_require_nvidia(self):
        self.assertEqual(closure.check_profile(self.low, "low32", closure.task_spec("analytic"), CFG)[0], [])

    def test_gpu_is_blocked_on_low(self):
        self.assertIn("task_requires_GPU", closure.check_profile(self.low, "low32", closure.task_spec("gpu_m40"), CFG)[0])

    def test_budget_reserves_eight_gib(self):
        reasons, budget = closure.check_profile(self.low, "low32", {"estimated_working_bytes": 22*closure.GIB}, CFG)
        self.assertEqual(budget, 21*closure.GIB)
        self.assertIn("predicted_working_set_exceeds_budget", reasons)

    def test_m80_cpu_model_prediction_fits_low(self):
        item = closure.task_spec("peec_m80_l064_q8_s10p8")
        self.assertLess(item["estimated_GiB"], 24)
        self.assertFalse(item.get("needs_gpu", False))

    def test_prediction_adds_thirty_percent_to_comparable_peak(self):
        item = closure.task_spec("peec_m80_l064_q8_s10p8")
        state = {"runs": [{"task_id": "peec_m80_l032_q4_s10p8", "run_id": "same_size"},
                           {"task_id": "gpu_m80", "run_id": "different_algorithm"}]}
        with patch.object(closure, "source_peak", return_value=5*closure.GIB):
            prediction = closure.resource_prediction(item, state)
        self.assertEqual(prediction["estimated_working_bytes"], int(6.5*closure.GIB))
        self.assertEqual(prediction["comparable_source_run_ids"], ["same_size"])

    def test_gpu_prediction_does_not_use_combined_historical_scale_peak(self):
        item = closure.task_spec("gpu_m80")
        with patch.object(closure, "source_peak", return_value=56*closure.GIB):
            prediction = closure.resource_prediction(item, {"runs": [{"task_id": "gpu_scale", "run_id": "combined"}]})
        self.assertEqual(prediction["estimated_working_bytes"], 6*closure.GIB)

    def test_run_id_prerequisite_resolves_to_frozen_results(self):
        self.assertEqual(closure.prerequisite_path("closure_123"), ROOT / "outputs" / "closure_123" / "results.json")

    def test_unknown_task_fails_before_dispatch(self):
        with self.assertRaises(ValueError):
            closure.task_spec("peec_m160_l064_q4_s10p8")

    def test_computational_signature_includes_model_source(self):
        item = closure.task_spec("peec_m40_l016_q4_s10p8")
        first, rows = closure.computational_signature(item, closure.DEFAULT_CONFIG)
        self.assertIn("PEEC.wl", [Path(x["path"]).name for x in rows])
        real_digest = closure.digest
        with patch.object(closure, "digest", side_effect=lambda p: "diagnosed-revision" if p.name == "PEEC.wl" else real_digest(p)):
            second, _ = closure.computational_signature(item, closure.DEFAULT_CONFIG)
        self.assertNotEqual(first, second)

    def test_ansys_requires_existing_explicit_environment(self):
        with patch.dict(closure.os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "existing PyAEDT"):
                closure.ansys_python()

    def test_final_interface_stop_survives_code_hash_changes(self):
        args = SimpleNamespace(task="ansys_native_probe_q1", profile="high64gpu", run_id="test_no_dispatch_finalized", interface_revision=2)
        with patch.object(closure, "hardware", return_value=self.high), patch.object(closure, "read", return_value={"finalized_tasks": {args.task: "two actual probes already failed"}}):
            with self.assertRaisesRegex(RuntimeError, "final bounded stop"):
                closure.run_task(args, CFG, closure.DEFAULT_CONFIG)


if __name__ == "__main__":
    unittest.main()
