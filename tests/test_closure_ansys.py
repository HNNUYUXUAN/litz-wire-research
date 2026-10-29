"""Closure contracts without starting an AEDT Desktop or running a solver."""
import copy
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import RunClosureAnsys as closure
import ansys_native3d as native


class ClosureAnsysContracts(unittest.TestCase):
    def setUp(self):
        self.config, _ = closure.native_config("seven", "high")
        self.config.update(base_source_mesh_length_m=50e-6, source_polygon_sides=42,
                           return_mesh_length_m=150e-6, air_mesh_length_m=200e-6)

    def test_mesh_ladder_keeps_geometry_and_reduces_only_source_mesh_length(self):
        variations = closure.two_d_variations(self.config, "2d_mesh")
        for actual, expected in zip([row[2] for row in variations], [50e-6, 37.5e-6, 25e-6]):
            self.assertAlmostEqual(actual, expected)
        for _, config, _ in variations:
            self.assertEqual(config, self.config)
        variations[0][1]["strand_centers_m"][0][0] = 1
        self.assertEqual(self.config["strand_centers_m"][0][0], 0)
        self.assertEqual(variations[1][1]["strand_centers_m"][0][0], 0)

    def test_return_variation_keeps_thickness_outer_domain_and_copper_sources(self):
        _, changed, mesh = closure.two_d_variations(self.config, "2d_return")[0]
        self.assertAlmostEqual(changed["return_outer_radius_m"]-changed["return_inner_radius_m"],
                               self.config["return_outer_radius_m"]-self.config["return_inner_radius_m"])
        self.assertEqual(changed["outer_domain_radius_m"],self.config["outer_domain_radius_m"])
        self.assertEqual(changed["strand_centers_m"],self.config["strand_centers_m"])
        self.assertEqual(mesh,25e-6)

    def test_outer_variation_does_not_move_the_physical_return(self):
        _, changed, _ = closure.two_d_variations(self.config,"2d_outer")[0]
        for key in ("return_inner_radius_m","return_outer_radius_m","strand_centers_m"):
            self.assertEqual(changed[key],self.config[key])
        self.assertAlmostEqual(changed["outer_domain_radius_m"],1.5*self.config["outer_domain_radius_m"])

    def test_budget_presets_cannot_raise_student_limits_or_reduce_reserve(self):
        for preset, working in (("low",24),("high",48)):
            result=closure.apply_budget(self.config,preset)
            self.assertEqual(result["maximum_working_set_GiB"],working)
            self.assertEqual(result["minimum_system_free_GiB"],8)
            self.assertEqual(result["solver_timeout_s"],3600)
            self.assertEqual(result["solver_cores"],4)
            self.assertEqual(result["student_tetrahedra_limit"],64000)
            self.assertEqual(result["student_surface_elements_limit"],8000)

    def test_memory_preflight_fails_before_any_aedt_session(self):
        with patch.object(native,"available_ram",return_value={"total_bytes":64*native.GIB,"free_bytes":9*native.GIB}):
            result=closure.two_d_preflight(self.config,25e-6)
        self.assertEqual(result["execution_status"],"blocked_environment_resource_budget")
        self.assertFalse(result["measured_allocation"])

    def test_2d_preflight_mesh_limit_is_not_relaxed(self):
        with patch.object(native,"available_ram",return_value={"total_bytes":64*native.GIB,"free_bytes":60*native.GIB}):
            result=closure.two_d_preflight(self.config,1e-6)
        self.assertEqual(result["reason"],"predicted_2d_mesh_exceeds_student_limit")

    def test_legacy_short_test_cannot_unlock_native_suite(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"report.json"
            path.write_text(json.dumps({"execution_status":"passed","task":"native_coarse","case":"q1",
                                        "implementation_sha256":"new"}),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"Expected native_suite"):
                closure.prerequisite_report(path,"native_suite","seven","new")
            with self.assertRaisesRegex(ValueError,"differs"):
                closure.prerequisite_report(path,"native_suite","q1","old")

    def test_full_q1_acceptance_unlocks_seven_only_for_the_same_implementation(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"report.json"
            path.write_text(json.dumps({"execution_status":"passed","task":"native_suite","case":"q1",
                                        "full_physical_acceptance":"passed","implementation_sha256":"same"}),encoding="utf-8")
            self.assertEqual(closure.prerequisite_report(path,"native_suite","seven","same")["case"],"q1")

    def test_mesh_area_uses_si_mean_and_rejects_missing_conductors(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"mesh.csv"
            path.write_text("Copper_1 | 12 | 1e-5 | 5e-5 | 3e-5 | 6e-10 | 6e-10 | 6.25e-10 | 0 |\n",encoding="utf-8")
            self.assertAlmostEqual(closure.mesh_2d_areas(path,["Copper_1"])["areas_m2"]["Copper_1"],7.5e-9)
            with self.assertRaises(native.InterfaceFailed):closure.mesh_2d_areas(path,["Copper_1","missing"])

    def test_mesh_archive_requires_actual_student_counts(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);project=folder/"seven.aedt"
            mesh_dir=project.with_suffix(".aedtresults")/"Design.results"/"current.cmesh1";mesh_dir.mkdir(parents=True)
            (mesh_dir/"mesh.msh").write_text("$begin 'mesh'\np[4: 1, 0, 0, 0]\nt[6: 1, 1, 2, 3, 13, 0]\n$end 'mesh'\n",encoding="utf-8")
            stats=folder/"mesh_stats.csv";stats.write_text("Total number of mesh elements: 2001\n",encoding="utf-8")
            with self.assertRaises(native.ResourceBlocked):closure.export_mesh_records(project,stats,folder,2)
            stats.write_text("Total number of mesh elements: 1\n",encoding="utf-8")
            result=closure.export_mesh_records(project,stats,folder,2)
            self.assertEqual(result["actual_counts"]["triangles_2d"],1)
            self.assertTrue((folder/"mesh_records.csv").is_file())
            with self.assertRaisesRegex(native.InterfaceFailed,"surface-triangle"):
                closure.export_mesh_records(project,stats,folder,3)

    def test_sampling_stays_inside_source_copper_and_away_from_3d_terminal_faces(self):
        source=copy.deepcopy(self.config);source["strand_centers_m"]=[[0,0]]
        points=closure.sample_points(source,3)
        radius=source["strand_diameter_m"]/2
        self.assertTrue(all(0<point[2]<source["axial_length_m"] for point in points))
        self.assertEqual(len(points),3*(49+32))
        self.assertTrue(all(math.hypot(point[0],point[1])<radius for point in points[:49]))

    def test_frozen_reference_is_the_explicit_fine_geometry(self):
        config,path=closure.closure_2d_config("full_20261005_handoff","high")
        self.assertEqual(path.parent.name,"field_case_005")
        self.assertEqual(config["source_polygon_sides"],42)
        self.assertAlmostEqual(config["independent_reference_area_m2"],5.47730328197441e-8)
        self.assertEqual(config["source_reference_sha256"],native.sha256(path))

    def test_r2_repairs_a_named_reference_without_changing_the_physical_quantity(self):
        before,_=closure.native_config("q1","high")
        repaired=closure.apply_interface_revision(before,2)
        self.assertEqual(repaired["current_density_expression_kind"],"fundamental")
        self.assertEqual(repaired["current_density_quantity"],"J")
        for key in ("frequency_Hz","conductivity_S_per_m","strand_diameter_m","strand_centers_m","voltage_excitation_model"):
            self.assertEqual(before[key],repaired[key])

    def test_project_freeze_checks_design_content_and_survives_source_overwrite(self):
        class App:
            def save_project(self):return True
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);project=folder/"probe.aedt"
            project.write_text("$begin 'AnsoftProject'\n",encoding="utf-8")
            with self.assertRaisesRegex(native.InterfaceFailed,"expected native design"):
                closure.freeze_project(App(),project,folder)
            project.write_text("DesignName='ClosureExpressionProbe'\n",encoding="utf-8")
            snapshot=closure.freeze_project(App(),project,folder)
            project.write_text("empty released project",encoding="utf-8")
            self.assertEqual(native.sha256(folder/snapshot["file"]),snapshot["sha256"])
            self.assertEqual(native.sha256(folder/snapshot["results_manifest_file"]),snapshot["results_manifest_sha256"])

    def test_failed_probe_lists_all_native_dependents_without_starting_a_solver(self):
        states=closure.dependent_task_states("native_probe","q1","failed_interface_or_solver","probe_r2")
        self.assertEqual([(row["task"],row["case"]) for row in states],
                         [("native_coarse","q1"),("native_suite","q1"),("native_suite","seven")])
        self.assertTrue(all(row["execution_status"]=="not_run" and row["solver_started"] is False for row in states))
        self.assertTrue(all(row["reason"]=="prerequisite_failed_or_stopped" for row in states))

    def test_missing_or_failed_prerequisite_is_a_deliberate_stop(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"report.json"
            with self.assertRaises(closure.DependencyStopped):
                closure.prerequisite_report(path,"native_coarse","q1","same")
            path.write_text(json.dumps({"execution_status":"failed_interface_or_solver"}),encoding="utf-8")
            with self.assertRaises(closure.DependencyStopped):
                closure.prerequisite_report(path,"native_coarse","q1","same")

    def test_gated_main_retains_inputs_environment_and_stop_record_without_aedt(self):
        config,reference=closure.native_config("q1","high")
        def sources(folder,_):
            snapshot=folder/"source_snapshot";snapshot.mkdir()
            file=snapshot/"fixture.py";file.write_text("source fixture",encoding="utf-8")
            native.dump(folder/"source_hashes.json",{file.name:native.sha256(file)})
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/"outputs").mkdir()
            prereq=root/"failed_probe.json";prereq.write_text(json.dumps({"execution_status":"failed_interface_or_solver"}),encoding="utf-8")
            with patch.object(closure,"ROOT",root),patch.object(closure,"native_config",return_value=(config,reference)),patch.object(closure,"archive_sources",side_effect=sources),patch.object(native,"run_one") as solver:
                exit_code=closure.main(["--task","native_coarse","--case","q1","--run-id","gated","--prerequisite",str(prereq),"--interface-revision","2"])
            solver.assert_not_called()
            folder=root/"outputs/gated";report=closure.read_json(folder/"results.json")
            self.assertEqual(exit_code,1);self.assertEqual(report["execution_status"],"not_run")
            self.assertFalse(report["solver_started"])
            self.assertEqual(report["frozen_data_selfcheck"]["execution_status"],"passed")
            self.assertEqual(closure.read_json(folder/"not_run_dependencies.json")["tasks"][0]["execution_status"],"not_run")

    def test_frozen_companion_hash_detects_postfreeze_mutation(self):
        class App:
            def save_project(self):return True
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);project=folder/"probe.aedt"
            project.write_text("DesignName='ClosureExpressionProbe'",encoding="utf-8")
            results=project.with_suffix(".aedtresults");results.mkdir()
            field=results/"field.aedtplt";field.write_text("actual frozen field",encoding="utf-8")
            snapshot=closure.freeze_project(App(),project,folder)
            manifest=closure.read_json(folder/snapshot["results_manifest_file"])
            self.assertEqual(manifest["entries"][0]["sha256"],native.sha256(field))
            field.write_text("changed after release",encoding="utf-8")
            frozen_field=folder/manifest["entries"][0]["file"]
            self.assertEqual(manifest["entries"][0]["sha256"],native.sha256(frozen_field))
            frozen_field.write_text("changed frozen evidence",encoding="utf-8")
            self.assertNotEqual(manifest["entries"][0]["sha256"],native.sha256(frozen_field))

    def test_scalar_field_stop_has_no_samples_and_pins_the_actual_r2_failure(self):
        config,_=closure.closure_2d_config("full_20261005_handoff","high")
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            record=closure.record_2d_field_export_stop(config,folder)
            self.assertEqual(record["execution_status"],"not_run_field_export")
            self.assertEqual(record["entries"],[])
            self.assertEqual(record["source_failure_run_id"],"closure_20261005_ansys_probe_r2")
            self.assertEqual(record["source_failure_report_sha256"],native.sha256(closure.ROOT/config["field_export_stop_reference"]))
            self.assertTrue((folder/"not_run_field_export.json").is_file())
            self.assertFalse(any(folder.glob("*.fld")))

    def test_scalar_prerequisite_unlocks_only_2d_boundary_checks(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"results.json"
            report={"execution_status":closure.SCALAR_PASSED,"scalar_validation_status":"passed",
                    "full_physical_acceptance":"not_run","task":"2d_mesh","case":"seven","implementation_sha256":"same"}
            path.write_text(json.dumps(report),encoding="utf-8")
            self.assertEqual(closure.prerequisite_report(path,"2d_return","seven","same"),report)
            with self.assertRaises(closure.DependencyStopped):
                closure.prerequisite_report(path,"native_coarse","q1","same")
            report["full_physical_acceptance"]="passed"
            path.write_text(json.dumps(report),encoding="utf-8")
            with self.assertRaises(closure.DependencyStopped):
                closure.prerequisite_report(path,"2d_outer","seven","same")

    def test_2d_project_freeze_uses_the_proven_explicit_save_path(self):
        class App:
            def __init__(self):self.saved=[]
            def save_project(self,path=None):self.saved.append(path);return True
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);project=folder/"seven_42gon.aedt"
            project.write_text("DesignName='SevenClosure42gon'",encoding="utf-8")
            app=App();closure.freeze_project(app,project,folder,explicit_save=True)
            self.assertEqual(app.saved,[str(project)])

    def test_second_2d_revision_restores_initial_mesh_and_retains_failure_identity(self):
        config,_=closure.closure_2d_config("full_20261005_handoff","high")
        self.assertIs(config["revert_to_initial_mesh"],True)
        self.assertEqual(config["two_d_scalar_revision"],2)
        self.assertEqual(config["two_d_mesh_revision_reference_sha256"],native.sha256(closure.ROOT/config["two_d_mesh_revision_reference"]))

    def test_2d_freeze_excludes_only_semaphore_locks_and_hashes_actual_entities(self):
        class App:
            def save_project(self,path=None):return True
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);project=folder/"seven.aedt";project.write_text("DesignName='SevenClosure42gon'",encoding="utf-8")
            results=project.with_suffix(".aedtresults");results.mkdir()
            (results/".private.semaphore").write_text("lock marker",encoding="utf-8")
            (results/"solution.asol").write_text("actual solution",encoding="utf-8")
            (results/"mesh.msh").write_text("actual mesh",encoding="utf-8")
            snapshot=closure.freeze_project(App(),project,folder,explicit_save=True)
            manifest=closure.read_json(folder/snapshot["results_manifest_file"])
            self.assertEqual(manifest["excluded_transient_lock_markers"],[str(Path("seven.aedtresults/.private.semaphore"))])
            self.assertEqual(len(manifest["entries"]),2)
            self.assertTrue(all(native.sha256(folder/entry["file"])==entry["sha256"] for entry in manifest["entries"]))
            self.assertFalse((folder/snapshot["frozen_results_directory"]/".private.semaphore").exists())

    def test_all_three_scalar_mesh_cases_continue_without_full_physical_acceptance(self):
        config,reference=closure.closure_2d_config("full_20261005_handoff","high")
        def sources(folder,*_):
            snapshot=folder/"source_snapshot";snapshot.mkdir()
            file=snapshot/"fixture.py";file.write_text("scalar fixture",encoding="utf-8")
            native.dump(folder/"source_hashes.json",{file.name:native.sha256(file)})
        def scalar_case(_,mesh,folder):
            return {"execution_status":closure.SCALAR_PASSED,"scalar_validation_status":"passed",
                    "full_physical_acceptance":"not_run","solver_started":False,"tests":[],
                    "source_Rac_ohm_per_axial_m":.3183,"independent_reference_relative_difference":1e-5}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/"outputs").mkdir()
            with patch.object(closure,"ROOT",root),patch.object(closure,"closure_2d_config",return_value=(config,reference)),patch.object(closure,"archive_sources",side_effect=sources),patch.object(closure,"run_2d",side_effect=scalar_case) as solve,patch.object(closure,"audit_frozen_run",return_value={"execution_status":"passed","solver_started":False}),patch.object(closure,"export_field_samples") as field:
                exit_code=closure.main(["--task","2d_mesh","--run-id","scalar_three","--interface-revision","2"])
            report=closure.read_json(root/"outputs/scalar_three/results.json")
            self.assertEqual(solve.call_count,3);field.assert_not_called()
            self.assertEqual(exit_code,0);self.assertEqual(report["execution_status"],closure.SCALAR_PASSED)
            self.assertEqual(report["full_physical_acceptance"],"not_run")
            self.assertEqual(report["physical_acceptance_status"],"limited_fields_unavailable")
            self.assertTrue(all(row["reason"]=="awaiting_explicit_serial_dispatch" for row in report["dependent_tasks"]))


if __name__=="__main__":
    unittest.main()
