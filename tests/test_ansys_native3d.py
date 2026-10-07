"""Pure Python failure/physics-interface checks; no AEDT application is launched."""
import copy
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import ansys_native3d as native


class Native3DChecks(unittest.TestCase):
    def setUp(self):
        self.config = native.read_config(native.ROOT / "configs" / "native3d_q1_straight.json")

    def test_explicit_peak_voltage_and_phase(self):
        amplitude = complex(-3, 4)
        props = native.voltage_parameters(amplitude)
        self.assertTrue(props["Voltage"].endswith("V"))
        self.assertAlmostEqual(float(props["Voltage"][:-1]), math.sqrt(2) * 5)
        self.assertAlmostEqual(float(props["phase"][:-3]), math.degrees(math.atan2(4, -3)))
        self.assertEqual(native.voltage_parameters(0j)["phase"], "0deg")

    def test_independent_bessel_reference_and_q1_constraint(self):
        self.assertLess(abs(native.round_wire_rac(self.config) / 0.020016203627649 - 1), 1e-10)
        geometry = native.physical_geometry(self.config)
        self.assertFalse(geometry["meets_5_mm2_nominal_constraint"])
        self.assertAlmostEqual(geometry["nominal_dc_current_density_A_per_mm2"], 20 / math.pi)

    def test_fair_sensitivity_dimensions(self):
        cases = {label: (config, mesh) for label, config, mesh in native.case_variations(self.config, "suite")}
        self.assertEqual(len(cases), 7)
        returned, _ = cases["return_distance"]
        self.assertEqual(returned["outer_domain_radius_m"], self.config["outer_domain_radius_m"])
        self.assertAlmostEqual(returned["return_outer_radius_m"] - returned["return_inner_radius_m"],
                               self.config["return_outer_radius_m"] - self.config["return_inner_radius_m"])
        outer, _ = cases["outer_domain"]
        self.assertEqual(outer["return_inner_radius_m"], self.config["return_inner_radius_m"])
        self.assertEqual(outer["return_outer_radius_m"], self.config["return_outer_radius_m"])

    def test_runtime_budget_not_a_hardware_maximum(self):
        with patch.object(native, "available_ram", return_value={"total_bytes": 64 * native.GIB, "free_bytes": native.GIB}):
            report = native.preflight(self.config, self.config["mesh_lengths_m"][0])
        self.assertEqual(report["execution_status"], "blocked_environment_resource_budget")
        self.assertFalse(report["measured_allocation"])

    def test_configuration_does_not_allow_touching_strands(self):
        config = copy.deepcopy(self.config)
        config["strand_centers_m"] = [[0, 0], [0, 0]]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "touch"):
                native.read_config(path)

    def test_mesh_identity_excludes_timestamp_and_preserves_connectivity(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "native3d.aedt"
            folder = project.with_suffix(".aedtresults") / "Design.results" / "mesh.cmesh1"
            folder.mkdir(parents=True)
            mesh = folder / "mesh.msh"
            stats = Path(temp) / "mesh_stats.csv"
            stats.write_text("Total number of mesh elements: 17\n", encoding="utf-8")
            body = "$begin 'mesh'\nverbose=false\np[4: 1, 0, 0, 0]\ntet[5: 1, 1, 2, 3, 4]\n$end 'mesh'\n"
            mesh.write_text("$begin '$base_index$'\ntime=1\n$end '$base_index$'\n" + body, encoding="utf-8")
            first = native.mesh_identity(project, stats)
            mesh.write_text("$begin '$base_index$'\ntime=2\n$end '$base_index$'\n" + body, encoding="utf-8")
            second = native.mesh_identity(project, stats)
            self.assertEqual(first["identity_sha256"], second["identity_sha256"])
            mesh.write_text(body.replace("1, 2, 3, 4", "1, 2, 3, 5"), encoding="utf-8")
            third = native.mesh_identity(project, stats)
            self.assertNotEqual(first["identity_sha256"], third["identity_sha256"])

    def test_missing_actual_mesh_is_a_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(native.InterfaceFailed, "cannot be certified"):
                native.mesh_identity(Path(temp) / "missing.aedt", Path(temp) / "missing.csv")

    def test_pilot_does_not_unlock_multistrand_gate(self):
        config = copy.deepcopy(self.config)
        config["strand_centers_m"] = [[0, 0], [0.001, 0]]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "pilot.json"
            path.write_text(json.dumps({"execution_status": "passed", "full_physical_acceptance": "not_run"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "has not passed"):
                native.prerequisite_check(config, path)

    def test_current_density_calculator_stacks_are_scalar_first(self):
        from ansys.aedt.core.visualization.post.field_calculator_expressions import _resolve_stack_depth
        captured = []
        def expression(app, name, operations, assignment=None):
            captured.append((name, operations))
            return name
        with patch.object(native, "make_expression", expression):
            native.current_density_expressions(None, self.config, {"Source": {"near": 1, "far": 2, "sides": [3]}})
        self.assertEqual(len(captured), 6)
        for name, operations in captured:
            self.assertEqual(_resolve_stack_depth(operations), 1, name)
            self.assertEqual(operations[0], "NameOfExpression('<Jx,Jy,Jz>')")
            if "_Jz_" in name:
                self.assertEqual(operations[1], "Operation('ScalarZ')")
                self.assertIn(operations[2], {"Operation('Real')", "Operation('Imag')"})

    def test_unchanged_interface_failure_budget_resets_after_repair(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            for index in (1, 2):
                path = parent / str(index)
                path.mkdir()
                native.dump(path / "results.json", {"source_config_sha256": "a", "implementation_sha256": "b",
                                                       "execution_status": "failed_interface_or_solver"})
            self.assertEqual(native.interface_failure_streak(parent / "new", "a", "b"), 2)
            self.assertEqual(native.interface_failure_streak(parent / "new", "a", "repaired"), 0)


if __name__ == "__main__":
    unittest.main()
