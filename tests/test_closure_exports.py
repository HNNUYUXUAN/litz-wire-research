"""Integrity/availability tests for archived data; fixtures never run a solver."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import VerifyClosureEvidence as verifier
import ExportResearchManifest as exporter


class ClosureExports(unittest.TestCase):
    def test_derived_cache_checks_original_conversion_process_evidence(self):
        self.write(self.bundle / "json_normalization.json", {"source_index_sha256": self.manifest["source_index_sha256"], "solver_executed": False, "files": []})
        self.write(self.bundle / "unit_clarifications.json", {"source_index_sha256": self.manifest["source_index_sha256"], "solver_executed": False, "overrides": []})
        self.write(self.bundle / "source_export_evidence/process_status.json", {"process_exit_code": 0})
        self.write(self.bundle / "source_export_evidence/export_process_status.json", {"processes": [{"stage": "ExportClosureEvidence.wls", "route": "analytic", "process_exit_code": 0}]})
        self.assertEqual(self.check()["execution_status"], "passed")
        self.write(self.bundle / "source_export_evidence/export_process_status.json", {"processes": [{"stage": "ExportClosureEvidence.wls", "route": "analytic", "process_exit_code": 1}]})
        self.assertEqual(self.check()["execution_status"], "failed")

    def test_nested_case_omissions_are_included_in_integrity_audit(self):
        data = {"cases": [{"mesh": {"elements": [{"connectivity": {"representation": "retained_in_original_WXF", "source_key": "data/cases/1/mesh/elements/1/connectivity", "reason": "bounded original retention"}}]}}]}
        self.assertEqual(len(list(verifier.omissions(data))), 1)

    def test_compound_unit_override_changes_labels_and_preserves_values(self):
        from litz_research.frozen_units import infer_unit, normalize_zeros
        for key, unit in [("Jdc_A_per_m2", "A/m^2"), ("Jz_RMS_A_per_m2", "A/m^2 RMS"), ("conductivity_S_per_m", "S/m"), ("u_nodes_V_per_m", "V/m"), ("rho_ohm_m", "ohm m"), ("Linternal_H_per_m", "H/axial_m"), ("loss_W_per_axial_m", "W/axial_m")]:
            self.assertEqual(infer_unit("data/"+key, "analytic")[0], unit)
        self.assertIsNone(infer_unit("data/anonymous_field", "analytic")[0])
        value = {"u_nodes_V_per_m": {"representation": "complex_re_im", "real": .4, "imag": -.2, "unit": "m"}}
        record = {"unit": "V/m", "rule_id": "voltage_gradient"}
        corrected = exporter.apply_unit_overrides(value, "routes/x/data.json", {"routes/x/data.json": {"data/u_nodes_V_per_m": record}})
        self.assertEqual(corrected["u_nodes_V_per_m"]["unit"], "V/m")
        self.assertEqual(corrected["u_nodes_V_per_m"]["real"], .4)
        self.assertEqual(value["u_nodes_V_per_m"]["unit"], "m")
        metadata = {"u_nodes_V_per_m": {"representation": {"description": "custom JSON metadata"}, "value": .4}}
        self.assertEqual(exporter.apply_unit_overrides(metadata, "routes/x/data.json", {"routes/x/data.json": {"data/u_nodes_V_per_m": record}}), metadata)
        text, changes = normalize_zeros('{"value":0.e-50,"literal":"0.e-50"}')
        self.assertEqual(json.loads(text), {"value": 0., "literal": "0.e-50"})
        self.assertEqual(len(changes), 1)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bundle = self.root / "outputs" / "closure_fixture"
        self.source = self.root / "outputs" / "source_fixture"
        self.route_dir = self.bundle / "routes" / "analytic"
        (self.route_dir / "arrays").mkdir(parents=True)
        self.source.mkdir(parents=True)
        self.source.joinpath("results.wxf").write_bytes(b"synthetic binary fixture; never parsed as WXF")
        self.write(self.source / "results.json", {"source_model": "fixture_only", "execution_status": "failed", "elapsed_seconds": 1, "metrics": {"Rac_ohm_per_m": .02}})
        self.write(self.source / "test_report.json", {"execution_status": "passed", "tests": [{"id": f"check_{i}", "execution_status": "passed"} for i in range(80)]})
        self.write(self.source / "parameters.json", {"frequency_Hz": 200000})
        self.write(self.source / "process_status.json", {"process_exit_code": 1})
        self.write(self.source / "environment.json", {"WolframVersion": "fixture", "gpu": {"name": "fixture", "path": "C:\\Users\\fixture\\SDK"}, "license_id": "private", "username": "private"})
        pin = {"selected_run_id": "source_fixture", "execution_status": "failed", "physical_acceptance_status": "failed_numerical"}
        self.write(self.bundle / "source_index.json", {"routes": {"analytic": pin}})
        self.index_hash = verifier.digest(self.bundle / "source_index.json")
        self.array = {"representation": "numeric_csv", "path": "routes/analytic/arrays/currents.csv", "dimensions": [2], "element_count": 2, "complex": True, "unit": "A RMS", "source_key": "data/cases/1/currents_RMS_A"}
        self.route_dir.joinpath("arrays/currents.csv").write_text("flat_index_1based,real,imag\n1,10,1\n2,10,-1\n", encoding="utf-8")
        self.write(self.route_dir / "data.json", {"cases": [{"Rac_ohm_per_m": .02, "currents_RMS_A": self.array}], "unsupported": {"representation": "not_exportable", "reason": "synthetic unsupported object retained in source"}})
        self.meta = {"route": "analytic", "run_id": "source_fixture", "source_model": "fixture_only", "execution_status": "failed", "physical_acceptance_status": "failed_numerical", "process_exit": 1, "export_status": "exported", "source_index_sha256": self.index_hash, "data": "routes/analytic/data.json", "solver_executed": False, "metrics": {"elapsed_seconds": 1}, "source_files": [{"path": p.relative_to(self.root).as_posix(), "sha256": verifier.digest(p)} for p in self.source.iterdir()]}
        self.meta.update(source_inventory_policy="recursive_original_files", numerical_roundtrip_required=True,
                         numerical_roundtrip="routes/analytic/numerical_roundtrip.json")
        bounds = {"passed": True, "maximum_absolute_error": 0, "maximum_relative_error": 0,
                  "maximum_normalized_error": 0, "absolute_tolerance": 1e-30, "relative_tolerance": 2e-14}
        self.roundtrip = {"route": "analytic", "run_id": "source_fixture", "source_index_sha256": self.index_hash,
                          "source_payload_path": "outputs/source_fixture/results.wxf",
                          "source_payload_sha256": verifier.digest(self.source / "results.wxf"),
                          "passed": True, "solver_executed": False,
                          "JSON_scalar_readback": {**bounds, "numeric_scalars_compared": 8, "keys_and_list_lengths_verified": True},
                          "arrays": [{**bounds, "csv_path": self.array["path"], "source_key": self.array["source_key"],
                                      "dimensions": [2], "element_count": 2, "complex": True, "indices_verified": True,
                                      "original_WXF_anchors": [{"flat_index_1based": 1, "real": 10, "imag": 1},
                                                               {"flat_index_1based": 2, "real": 10, "imag": -1}]}]}
        self.write(self.route_dir / "numerical_roundtrip.json", self.roundtrip)
        self.write(self.bundle / "export_process_status.json", {"processes": [{"stage": "conversion", "process_exit_code": 0}]})
        self.refresh()

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def refresh(self):
        self.write(self.route_dir / "export_metadata.json", self.meta)
        assets = [{"path": p.relative_to(self.bundle).as_posix(), "sha256": verifier.digest(p), "kind": "numeric_array" if p.suffix == ".csv" else "metadata_or_scalar_data"} for p in self.route_dir.rglob("*") if p.is_file()]
        self.manifest = {"schema_version": 1, "source_index": "source_index.json", "source_index_sha256": self.index_hash, "routes": {"analytic": {"run_id": "source_fixture", "export_status": "exported", "metadata": "routes/analytic/export_metadata.json", "assets": assets, "solver_executed": False}}}
        self.write(self.bundle / "closure_manifest.json", self.manifest)

    def check(self):
        return verifier.verify(self.bundle, self.root, "low32", require_process=True)

    def test_complete_export_passes_without_physical_upgrade(self):
        result = self.check()
        self.assertEqual(result["execution_status"], "passed", result["errors"])
        self.assertEqual(result["counts"]["numeric_arrays"], 1)
        self.assertEqual(result["low32_real_device_acceptance"], "pending")

    def test_missing_numeric_cache_fails_without_solver_fallback(self):
        self.route_dir.joinpath("arrays/currents.csv").unlink()
        with patch("subprocess.Popen", side_effect=AssertionError("no process may start")):
            self.assertEqual(self.check()["execution_status"], "failed")
            with self.assertRaises(OSError):
                verifier.rebuild_figures(self.bundle)

    def test_changed_source_is_detected(self):
        self.source.joinpath("results.wxf").write_bytes(b"changed")
        self.assertTrue(any("source SHA256 mismatch" in e for e in self.check()["errors"]))

    def test_unresolved_LFS_pointer_fails_even_with_matching_hash(self):
        p = self.source / "results.wxf"
        p.write_bytes(verifier.LFS_PREFIX+b"\noid sha256:"+b"0"*64+b"\nsize 1000\n")
        for source in self.meta["source_files"]:
            if source["path"].endswith("results.wxf"):
                source["sha256"] = verifier.digest(p)
        self.refresh()
        self.assertTrue(any("LFS pointer" in e for e in self.check()["errors"]))

    def test_original_run_snapshot_hash_is_not_replaced_by_new_inventory(self):
        snapshot = self.source / "source_snapshot/src/example.wl"
        snapshot.parent.mkdir(parents=True)
        snapshot.write_text("original", encoding="utf-8")
        declaration = self.source / "run_manifest.json"
        self.write(declaration, {"sources": [{"path": "src/example.wl", "sha256": verifier.digest(snapshot)}]})
        snapshot.write_text("modified", encoding="utf-8")
        for path in (snapshot, declaration):
            self.meta["source_files"].append({"path": path.relative_to(self.root).as_posix(), "sha256": verifier.digest(path)})
        self.refresh()
        self.assertTrue(any("original run source snapshot hash mismatch" in e for e in self.check()["errors"]))

    def test_index_hash_and_pin_must_match(self):
        self.write(self.bundle / "source_index.json", {"routes": {"analytic": {"selected_run_id": "another_run"}}})
        self.assertEqual(self.check()["execution_status"], "failed")

    def test_array_shape_and_numeric_content_are_checked(self):
        self.array["dimensions"] = [3]
        data = {"currents_RMS_A": self.array}
        self.write(self.route_dir / "data.json", data)
        self.refresh()
        self.assertTrue(any("dimensions/count" in e for e in self.check()["errors"]))

    def test_source_paths_cannot_escape_root(self):
        self.meta["source_files"][0]["path"] = "../private/file"
        self.refresh()
        self.assertEqual(self.check()["execution_status"], "failed")

    def test_cached_redraw_needs_only_CSV(self):
        with patch("subprocess.Popen", side_effect=AssertionError("no process may start")):
            report = verifier.rebuild_figures(self.bundle)
        self.assertEqual(len(report["figures"]), 1)
        self.assertEqual(report["figures"][0]["source_csv_sha256"], verifier.digest(self.route_dir / "arrays/currents.csv"))
        self.assertFalse(report["solver_executed"])

    def test_exporter_keeps_all_checks_and_redacts_machine_paths(self):
        with patch.object(exporter, "ROOT", self.root):
            manifest = exporter.build(self.bundle)
        route = manifest["routes"][0]
        self.assertEqual(route["physical_acceptance_status"], "failed_numerical")
        self.assertEqual(len(route["checks"]), 80)
        self.assertEqual(route["metrics"]["Rac_ohm_per_m"], .02)
        env = verifier.read(self.root / "web/public/assets/source_fixture/environment.json")
        self.assertNotIn("license_id", env)
        self.assertNotIn("username", env)
        self.assertNotIn("C:\\Users", json.dumps(env))
        data = verifier.read(self.root / "web/public/assets/source_fixture/cache/data.json")
        self.assertTrue(data["cases"][0]["currents_RMS_A"]["path"].startswith("/assets/source_fixture/cache/"))

    def test_incomplete_bundle_exporter_rejects_missing_data(self):
        self.route_dir.joinpath("data.json").unlink()
        with patch.object(exporter, "ROOT", self.root), self.assertRaises(ValueError):
            exporter.build(self.bundle)

    def test_archive_build_and_exit_evidence_are_explicit(self):
        self.bundle.joinpath("export_process_status.json").unlink()
        result = verifier.verify(self.bundle, self.root, require_notebooks=True, require_process=True)
        self.assertTrue(any("archive_notebooks" in e for e in result["errors"]))
        self.assertTrue(any("process exit" in e for e in result["errors"]))

    def test_numeric_roundtrip_cannot_be_replaced_by_hash_only(self):
        self.route_dir.joinpath("numerical_roundtrip.json").unlink()
        self.refresh()
        self.assertTrue(any("roundtrip" in e for e in self.check()["errors"]))

    def test_updated_CSV_hash_does_not_hide_original_numeric_mismatch(self):
        self.route_dir.joinpath("arrays/currents.csv").write_text("flat_index_1based,real,imag\n1,11,1\n2,10,-1\n", encoding="utf-8")
        self.refresh()
        self.assertTrue(any("original WXF anchor" in e for e in self.check()["errors"]))

    def test_roundtrip_error_and_source_hash_bindings_are_enforced(self):
        self.roundtrip["arrays"][0]["maximum_normalized_error"] = 1.1
        self.roundtrip["source_payload_sha256"] = "0" * 64
        self.write(self.route_dir / "numerical_roundtrip.json", self.roundtrip)
        self.refresh()
        errors = self.check()["errors"]
        self.assertTrue(any("exceeds declared tolerance" in e for e in errors))
        self.assertTrue(any("not in original inventory" in e for e in errors))

    def test_recursive_original_raw_binary_requires_hash_but_no_public_dense_copy(self):
        raw = self.source / "archive/cases/9856/CPU_model.wxf"
        raw.parent.mkdir(parents=True)
        raw.write_bytes(b"synthetic retained dense binary; never imported")
        self.refresh()
        self.assertTrue(any("recursive original inventory incomplete" in e for e in self.check()["errors"]))
        self.meta["source_files"].append({"path": raw.relative_to(self.root).as_posix(), "sha256": verifier.digest(raw)})
        self.refresh()
        self.assertEqual(self.check()["execution_status"], "passed")
        with patch.object(exporter, "ROOT", self.root):
            public = exporter.build(self.bundle)
        self.assertFalse(any(a["path"].endswith("CPU_model.wxf") for a in public["assets"]))

    def test_recursive_cases_preserve_names_and_scope_specific_status(self):
        for case in ("a", "b"):
            raw = self.source / "cases" / case / "case.json"
            self.write(raw, {"execution_status": "passed_scalar_validation_fields_unavailable",
                             "scalar_validation_status": "passed", "full_physical_acceptance": "not_run",
                             "Rac_ohm_per_m": .02 if case == "a" else .03})
            cached = self.route_dir / "custom" / "cases" / case / "case.json"
            self.write(cached, verifier.read(raw))
            self.meta["source_files"].append({"path": raw.relative_to(self.root).as_posix(), "sha256": verifier.digest(raw)})
        self.refresh()
        for asset in self.manifest["routes"]["analytic"]["assets"]:
            if "/custom/" in asset["path"]:
                asset.update(kind="preserved_custom_data", source_relative_path=asset["path"].split("/custom/", 1)[1])
        self.write(self.bundle / "closure_manifest.json", self.manifest)
        self.assertEqual(self.check()["execution_status"], "passed")
        with patch.object(exporter, "ROOT", self.root):
            route = exporter.build(self.bundle)["routes"][0]
        records = [r for r in route["numerical_cases"] if "source_relative_path" in r]
        self.assertEqual({r["source_relative_path"] for r in records}, {"cases/a/case.json", "cases/b/case.json"})
        self.assertTrue(all(r["validation_scopes"]["scalar_validation_status"] == "passed" for r in records))

    def test_legitimate_new_execution_tokens_are_preserved(self):
        for status in ("passed_scalar_validation_fields_unavailable", "failed_interface_or_solver",
                       "stopped_resource_or_time_budget", "not_completed_time_budget"):
            execution, physical, _ = exporter.status_for("closure", {"execution_status": status,
                                                       "physical_acceptance_status": "limited_fields_unavailable"}, {}, {})
            self.assertEqual(execution, status)
            self.assertEqual(physical, "limited_fields_unavailable")

    def test_scalar_metrics_do_not_truncate_after_32_keys(self):
        original = {f"metric_{i}": i for i in range(80)}
        self.assertEqual(exporter.compact_metrics(original), original)

    def test_imposed_field_parameters_override_generic_transport_current(self):
        self.meta["effective_parameters"] = {"frequency_Hz": 200000, "net_transport_current_RMS_A": 0,
                                             "current_RMS_A": 0, "total_current_RMS_A": 0,
                                             "uniform_external_Bz_RMS_T": .001}
        self.refresh()
        self.assertEqual(self.check()["execution_status"], "passed")
        with patch.object(exporter, "ROOT", self.root):
            physics = exporter.build(self.bundle)["routes"][0]["physics"]
        self.assertEqual(physics["total_current_rms_a"], 0)
        self.assertEqual(physics["uniform_external_Bz_rms_t"], .001)
        self.assertIn("not_applicable", physics["Rac_from_P_over_I2"])
        self.meta["effective_parameters"]["current_RMS_A"] = 20
        self.refresh()
        self.assertTrue(any("transport current overrides" in error for error in self.check()["errors"]))

    def test_pinned_wrapper_process_evidence_is_preserved_without_exit(self):
        observation = self.source / "wrapper_resource_observation.json"
        self.write(observation, {"native_exit_known": False, "observed_wrapper_failure": True})
        evidence = {"path": observation.relative_to(self.root).as_posix(), "sha256": verifier.digest(observation),
                    "scope": "observed wrapper failure; native exit unknown"}
        index = verifier.read(self.bundle / "source_index.json")
        index["routes"]["analytic"]["process_evidence"] = evidence
        self.write(self.bundle / "source_index.json", index)
        self.index_hash = verifier.digest(self.bundle / "source_index.json")
        self.meta["source_index_sha256"] = self.index_hash
        self.roundtrip["source_index_sha256"] = self.index_hash
        self.write(self.route_dir / "numerical_roundtrip.json", self.roundtrip)
        self.meta["pinned_process_evidence"] = evidence
        self.meta["source_files"].append({"path": evidence["path"], "sha256": evidence["sha256"]})
        cached = self.route_dir / "custom" / observation.name
        self.write(cached, verifier.read(observation))
        self.refresh()
        self.assertEqual(self.check()["execution_status"], "passed")
        self.meta["pinned_process_evidence"] = None
        self.refresh()
        self.assertTrue(any("pinned process evidence was changed" in error for error in self.check()["errors"]))

    def test_two_explicit_routes_with_same_run_keep_both_cache_namespaces(self):
        pin = verifier.read(self.bundle / "source_index.json")["routes"]["analytic"]
        self.write(self.bundle / "source_index.json", {"routes": {"analytic": pin, "shared_alias": pin}})
        index_hash = verifier.digest(self.bundle / "source_index.json")
        self.meta["source_index_sha256"] = index_hash
        self.roundtrip["source_index_sha256"] = index_hash
        self.write(self.route_dir / "numerical_roundtrip.json", self.roundtrip)
        self.index_hash = index_hash
        self.refresh()
        alias = self.bundle / "routes/shared_alias"
        shutil.copytree(self.route_dir, alias)
        for path in alias.rglob("*.json"):
            value = json.loads(path.read_text(encoding="utf-8").replace("routes/analytic/", "routes/shared_alias/"))
            if isinstance(value, dict) and "route" in value:
                value["route"] = "shared_alias"
            self.write(path, value)
        assets = [{"path": p.relative_to(self.bundle).as_posix(), "sha256": verifier.digest(p),
                   "kind": "numeric_array" if p.suffix == ".csv" else "metadata_or_scalar_data"}
                  for p in alias.rglob("*") if p.is_file()]
        self.manifest["routes"]["shared_alias"] = {"run_id": "source_fixture", "export_status": "exported",
             "metadata": "routes/shared_alias/export_metadata.json", "assets": assets, "solver_executed": False}
        self.write(self.bundle / "closure_manifest.json", self.manifest)
        self.assertEqual(self.check()["execution_status"], "passed")
        with patch.object(exporter, "ROOT", self.root):
            manifest = exporter.build(self.bundle)
        for route in ("analytic", "shared_alias"):
            path = self.root / "web/public/assets/source_fixture/cache" / route / "data.json"
            self.assertTrue(path.exists())
            value = verifier.read(path)
            self.assertIn(f"/cache/{route}/", value["cases"][0]["currents_RMS_A"]["path"])
            public_route = next(row for row in manifest["routes"] if row["route"] == route)
            self.assertIn(f"/assets/source_fixture/cache/{route}/", public_route["numerical_cases"][0]["currents_RMS_A"]["path"])
        for asset in manifest["assets"]:
            public_path = self.root / "web/public" / asset["path"].lstrip("/")
            self.assertEqual(verifier.digest(public_path), asset["sha256"])


if __name__ == "__main__":
    unittest.main()
