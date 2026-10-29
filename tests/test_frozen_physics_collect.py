"""Only synthetic saved-report fixtures; no WXF deserialization or solver."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import CollectFrozenPhysicsValidation as collector


class FrozenPhysicsCollection(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.parent = "validation_fixture"
        self.raw = "raw_fixture"
        self.case_id = "case_fixture"
        self.case = self.make_case(self.raw, self.case_id)
        self.save_parent([self.case])
        self.selection = {"schema_version": 1, "required_raw_run_ids": [self.raw],
                          "selected_reports": [{"raw_run_id": self.raw, "verification_run_id": self.parent,
                                                "case_id": self.case_id, "case_report_sha256": self.case_sha()}],
                          "partial_parent_failures": {}}
        self.selection_path = self.root / "selection.json"
        self.output = self.root / "outputs" / "collector_fixture"

    @staticmethod
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value) + "\n", encoding="utf-8")

    def make_case(self, raw, case_id, kind="PEEC"):
        role_names = {"original_complete_saved_model_or_solution": "model.wxf",
                      "original_stage_numeric_CSV": "currents.csv",
                      "original_model_source_before_stage": "source_snapshot/src/model.wl",
                      "original_case_scalar_and_current_JSON": "case.json",
                      "original_case_input_parameters": "parameters.json",
                      "original_run_provenance": "run_manifest.json"}
        if kind == "CPU_GPU":
            role_names["original_saved_GPU_matrix_and_solution"] = "GPU_solution.wxf"
        sources = []
        for role, name in role_names.items():
            path = self.root / "outputs" / raw / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(("synthetic fixture bytes never interpreted: " + name).encode())
            sources.append({"path": path.relative_to(self.root).as_posix(), "role": role,
                            "sha256": self.sha(path), "bytes": path.stat().st_size})
        required = {"required_model_source_snapshot_declarations", "phasor_convention"}
        bases = {"PEEC": "longitudinal volume filaments", "CPU_GPU": "saved CPU/GPU longitudinal volume-filament PEEC",
                 "RT0": "RT0 face flux, three current components"}
        if kind == "PEEC":
            required |= {"every_current_ReIm_WXF_to_JSON", "every_current_ReIm_WXF_to_CSV",
                         "port_voltage_ReIm_WXF_to_JSON", "loss_WXF_to_JSON", "Rac_WXF_to_JSON"}
        elif kind == "RT0":
            required |= {"every_face_flux_ReIm_WXF_to_CSV", "every_face_axis_grid_WXF_to_CSV",
                         "every_cell_phi_ReIm_WXF_to_CSV", "every_cell_J_from_original_face_flux_to_CSV",
                         "port_current_ReIm_WXF_to_JSON", "port_voltage_ReIm_WXF_to_JSON", "loss_WXF_to_JSON"}
        else:
            required |= {"all_GPU_currents_WXF_to_JSON", "every_GPU_current_ReIm", "every_CPU_current_ReIm",
                         "GPU_voltage_ReIm_WXF_to_JSON", "every_original_filament_id", collector.MATRIX_ID}
        checks = [{"id": name, "execution_status": "passed", "kind": "numerical_agreement",
                   "maximum_normalized_error": 0., "relative_tolerance": 2e-14, "absolute_tolerance": 1e-30,
                   "unit": "SI RMS", "source": "synthetic fixture", "values_compared": 2}
                  for name in sorted(required)]
        if kind == "CPU_GPU":
            matrix = next(row for row in checks if row["id"] == collector.MATRIX_ID)
            matrix.update(kind="arithmetic_reduction_agreement", relative_tolerance=1e-12,
                          direct_value_relative_tolerance=2e-14, saved_physical_matrix_error_threshold=1e-10,
                          original_formula="original Flatten norm ratio", verification_formula="128-row norm ratio",
                          tolerance_reason="floating-point reduction order")
        return {"run_id": raw, "case_id": case_id, "validation_status": collector.PASSED,
                "checks": checks, "source_files": sources, "missing_or_error": None, "solver_executed": False,
                "scope": {"basis": bases[kind], "phasor": "exp(+j omega t)", "current_convention": "RMS",
                          "JSON_vector_coverage": "synthetic complete Re/Im fixture", "new_physics_solved": False},
                "source_case_execution_status": "failed_wrapper_but_original_values_saved",
                "source_physical_acceptance_status": "limited_original_physical_scope",
                "source_run_status": {"original_process_exit_code": 1},
                "physical_acceptance_status": "not_applicable_original_cache_agreement_only"}

    def save_parent(self, cases, exit_code=0):
        folder = self.root / "outputs" / self.parent
        tool = folder / "source_snapshot" / "src" / "VerifyFrozenPhysics.wls"
        tool.parent.mkdir(parents=True, exist_ok=True)
        tool.write_bytes(b"synthetic validation tool snapshot; no solver")
        passed = exit_code == 0
        report = {"ReferenceRuns": [row["run_id"] for row in cases], "cases": cases, "unverified_reference_runs": [],
                  "execution_status": collector.PASSED if passed else "not_verified_or_failed_original_evidence",
                  "solver_executed": False, "new_physics_solved": False, "verifier_source_sha256": self.sha(tool)}
        self.write(folder / "frozen_validation" / "frozen_physics_validation.json", report)
        self.write(folder / "frozen_validation" / "test_report.json",
                   {"execution_status": "passed" if passed else "failed_or_incomplete",
                    "tests": [{"id": row["run_id"] + "/" + row["case_id"],
                               "execution_status": "passed" if row["validation_status"] == collector.PASSED else "failed_or_incomplete"}
                              for row in cases]})
        self.write(folder / "process_status.json", {"process_exit_code": exit_code})
        self.write(folder / "frozen_verifier_child_process.json",
                   {"process_exit_code": exit_code, "ReferenceRuns": report["ReferenceRuns"], "solver_executed": False})
        self.write(folder / "run_manifest.json", {"snapshot_time": "before_stage_execution",
                   "sources": [{"path": "src\\VerifyFrozenPhysics.wls", "sha256": self.sha(tool)}]})
        for row in cases:
            self.write(folder / "frozen_validation" / "cases" / (row["run_id"] + "__" + row["case_id"] + ".json"), row)

    def case_path(self):
        return self.root / "outputs" / self.parent / "frozen_validation" / "cases" / (self.raw + "__" + self.case_id + ".json")

    def case_sha(self):
        return self.sha(self.case_path())

    def collect(self):
        self.write(self.selection_path, self.selection)
        return collector.collect(self.selection_path, self.output, self.root)

    def replace_case(self):
        self.save_parent([self.case])
        self.selection["selected_reports"][0]["case_report_sha256"] = self.case_sha()

    def test_pass_and_original_physical_and_wrapper_status_remain(self):
        report = self.collect()
        self.assertEqual(report["execution_status"], collector.PASSED)
        self.assertEqual(report["selected_case_count"], 1)
        self.assertEqual(report["cases"][0]["source_physical_acceptance_status"], "limited_original_physical_scope")
        self.assertEqual(report["cases"][0]["source_run_status"]["original_process_exit_code"], 1)
        self.assertFalse((self.output / "process_status.json").exists())
        self.assertEqual(json.loads((self.output / "test_report.json").read_text())["execution_status"], "passed")

    def test_rt0_complete_complex_coverage(self):
        self.case = self.make_case(self.raw, self.case_id, "RT0")
        self.replace_case()
        self.assertEqual(self.collect()["cases"][0]["validation_kind"], "RT0")

    def test_gpu_reduction_contract_passes(self):
        self.case = self.make_case(self.raw, self.case_id, "CPU_GPU")
        self.replace_case()
        self.assertEqual(self.collect()["cases"][0]["validation_kind"], "CPU_GPU")

    def test_selected_case_hash_tamper_fails(self):
        self.case_path().write_text("{}\n")
        self.assertIn("SHA256 mismatch", self.collect()["failure_reason"])

    def test_original_source_hash_tamper_fails(self):
        path = self.root / self.case["source_files"][0]["path"]
        path.write_bytes(b"tampered original result")
        self.assertIn("SHA256 mismatch", self.collect()["failure_reason"])

    def test_binary_lfs_pointer_fails_before_parse(self):
        path = self.root / self.case["source_files"][0]["path"]
        path.write_bytes(collector.LFS_PREFIX + b"\noid sha256:abc\n")
        self.assertIn("Git LFS pointer", self.collect()["failure_reason"])

    def test_missing_raw_file_fails(self):
        (self.root / self.case["source_files"][0]["path"]).unlink()
        self.assertNotEqual(self.collect()["execution_status"], collector.PASSED)

    def test_missing_required_raw_run_fails(self):
        self.selection["required_raw_run_ids"].append("unselected_raw")
        self.assertIn("coverage differs", self.collect()["failure_reason"])

    def test_duplicate_selected_raw_fails(self):
        self.selection["selected_reports"].append(copy.deepcopy(self.selection["selected_reports"][0]))
        self.assertIn("Duplicate selected", self.collect()["failure_reason"])

    def test_selected_failed_check_fails(self):
        self.case["checks"][0]["execution_status"] = "failed"
        self.replace_case()
        self.assertIn("failed/incomplete checks", self.collect()["failure_reason"])

    def test_missing_complex_coverage_fails(self):
        self.case["checks"] = [row for row in self.case["checks"] if row["id"] != "every_current_ReIm_WXF_to_JSON"]
        self.replace_case()
        self.assertIn("complex/unit coverage", self.collect()["failure_reason"])

    def test_widened_direct_tolerance_fails(self):
        next(row for row in self.case["checks"] if row["id"] == "every_current_ReIm_WXF_to_JSON")["relative_tolerance"] = 1e-12
        self.replace_case()
        self.assertIn("tolerance was widened", self.collect()["failure_reason"])

    def test_missing_actual_exit_fails(self):
        self.write(self.root / "outputs" / self.parent / "process_status.json", {})
        self.assertIn("exit code missing", self.collect()["failure_reason"])

    def test_validation_source_snapshot_mismatch_fails(self):
        path = self.root / "outputs" / self.parent / "source_snapshot" / "src" / "VerifyFrozenPhysics.wls"
        path.write_bytes(b"changed validator source")
        self.assertIn("SHA256 mismatch", self.collect()["failure_reason"])

    def partial_case(self):
        failed = self.make_case("old_gpu_failed", "gpu_case", "CPU_GPU")
        failed["validation_status"] = "failed_original_numeric_agreement"
        next(row for row in failed["checks"] if row["id"] == collector.MATRIX_ID)["execution_status"] = "failed"
        self.save_parent([self.case, failed], exit_code=1)
        self.selection["partial_parent_failures"] = {self.parent: {"expected_process_exit_code": 1,
                  "allowed_failed_check_ids": [collector.MATRIX_ID], "expected_failed_raw_run_ids": ["old_gpu_failed"]}}

    def test_partial_parent_failure_explicitly_preserved(self):
        self.partial_case()
        report = self.collect()
        self.assertEqual(report["execution_status"], collector.PASSED)
        parent = report["verification_batches"][0]
        self.assertEqual(parent["actual_parent_process_exit_code"], 1)
        self.assertEqual(parent["original_parent_execution_status"], "not_verified_or_failed_original_evidence")
        self.assertTrue(parent["partial_parent_failure_explicitly_preserved"])
        self.assertEqual(parent["unselected_failed_cases"][0]["raw_run_id"], "old_gpu_failed")
        self.assertFalse(parent["parent_failed_outcome_changed"])

    def test_partial_parent_without_explicit_contract_fails(self):
        self.partial_case()
        self.selection["partial_parent_failures"] = {}
        self.assertIn("explicit partial-parent", self.collect()["failure_reason"])

    def test_partial_parent_extra_failure_fails(self):
        self.partial_case()
        self.selection["partial_parent_failures"][self.parent]["allowed_failed_check_ids"] = ["other_failure"]
        self.assertIn("differ from explicit", self.collect()["failure_reason"])

    def test_missing_original_gpu_archive_hash_fails(self):
        self.case = self.make_case(self.raw, self.case_id, "CPU_GPU")
        self.case["source_files"] = [row for row in self.case["source_files"] if row["role"] != "original_saved_GPU_matrix_and_solution"]
        self.replace_case()
        self.assertIn("GPU matrix/current/voltage archive", self.collect()["failure_reason"])

    def test_existing_runner_scaffold_is_allowed(self):
        self.output.mkdir(parents=True)
        self.write(self.output / "environment.json", {"fixture": "runner snapshot"})
        self.assertEqual(self.collect()["execution_status"], collector.PASSED)

    def test_existing_result_is_protected(self):
        self.output.mkdir(parents=True)
        self.output.joinpath("results.json").write_text("protected")
        with self.assertRaises(FileExistsError):
            self.collect()
        self.assertEqual(self.output.joinpath("results.json").read_text(), "protected")


if __name__ == "__main__":
    unittest.main()
