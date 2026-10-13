"""Bounded, independently calibrated seven-strand/straight APhi closure tasks.

No package installation, CAD import, or change to an existing project is made.
Each invocation owns a new run directory and a new AEDT Desktop. Native probe
only loads field expressions; all solve tasks must be dispatched serially.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import csv
from datetime import datetime, timezone
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
import traceback

import ansys_native3d as native
from ansys_validate import dump, read_shorttest_solution

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file() and (p / "configs/reference_parameters.json").is_file())
TASKS = ("preflight", "2d_mesh", "2d_return", "2d_outer", "native_probe", "native_coarse", "native_suite")
LIMITS = {"triangles_2d": 2000, "tetrahedra_3d": 64000, "surface_triangles_3d": 8000, "cores": 4}
SCALAR_PASSED = "passed_scalar_validation_fields_unavailable"
NATIVE_STOP_RUN_ID = "closure_20261005_ansys_probe_r2"


class DependencyStopped(ValueError):
    """A gated task is deliberately not dispatched to AEDT."""


def read_json(path):
    from litz_research.common import resolve_read_path
    return json.loads(resolve_read_path(ROOT,path).read_text(encoding="utf-8-sig"))


def apply_budget(config, budget):
    config = copy.deepcopy(config)
    config.update(maximum_working_set_GiB=48.0 if budget == "high" else 24.0,
                  minimum_system_free_GiB=8.0, solver_timeout_s=3600, solver_cores=4,
                  student_tetrahedra_limit=64000, student_surface_elements_limit=8000)
    return config


def apply_interface_revision(config, revision):
    config = copy.deepcopy(config)
    config["closure_interface_revision"] = revision
    if revision == 2:
        config["current_density_expression_kind"] = "fundamental"
        config["current_density_quantity"] = "J"
        config["interface_repair_reason"] = "R1 used NameOfExpression on an undefined vector display string. PyAEDT CLC passes named references verbatim. R2 uses the Maxwell fundamental current-density quantity J, retaining scalar component before Real/Imag and retaining independent physical J integrals."
    return config


def freeze_project(app, project, folder, explicit_save=False):
    saved = app.save_project(str(project)) if explicit_save else app.save_project()
    native.require(saved, "Saved project snapshot could not be written.")
    if not project.is_file():
        raise native.InterfaceFailed("Saved project snapshot has no actual source file.")
    text = project.read_bytes()
    if b"ClosureExpressionProbe" not in text and b"SevenClosure42gon" not in text and b"NativeStraightAPhi" not in text:
        raise native.InterfaceFailed("Saved project lacks the expected native design; file existence alone is not acceptance.")
    frozen = folder / (project.stem + "_saved_before_release.aedt")
    shutil.copy2(project, frozen)
    results = project.with_suffix(".aedtresults")
    frozen_results = frozen.with_suffix(".aedtresults")
    excluded = sorted(str(path.relative_to(folder)) for path in results.rglob("*")
                      if path.is_file() and path.name.lower().endswith(".semaphore")) if explicit_save else []
    if results.is_dir():
        shutil.copytree(results, frozen_results, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("*.semaphore") if explicit_save else None)
    entries = [{"file": str(path.relative_to(folder)), "bytes": path.stat().st_size,
                "sha256": native.sha256(path)} for path in sorted(frozen_results.rglob("*")) if path.is_file()] if frozen_results.is_dir() else []
    manifest = folder / "native_project_results_manifest.json"
    dump(manifest, {"source_project": project.name, "source_results_directory": results.name,
                   "frozen_results_directory": frozen_results.name,
                   "entries": entries, "excluded_transient_lock_markers": excluded,
                   "exclusion_scope": "Only *.semaphore runtime lock markers are omitted for 2D explicit-save freezing; all actual field/mesh/result entities are copied and hashed.",
                   "scope": "Complete existing native companion files at pre-release save; no field solve is performed by freezing."})
    return {"file": frozen.name, "sha256": native.sha256(frozen),
            "source_project": project.name, "source_results_directory": project.with_suffix(".aedtresults").name,
            "frozen_results_directory": frozen_results.name,
            "results_manifest_file": manifest.name, "results_manifest_sha256": native.sha256(manifest),
            "scope": "Immutable pre-release project snapshot and copied companion results share the frozen project basename for later native reopening."}


def native_config(case, budget):
    path = ROOT / "configs" / ("native3d_q1_straight.json" if case == "q1" else "native3d_7_straight.json")
    return apply_budget(native.read_config(path), budget), path


def closure_2d_config(handoff_run_id, budget):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", handoff_run_id):
        raise ValueError("Invalid handoff run ID.")
    handoff = ROOT / "outputs" / handoff_run_id
    reference_path = handoff / "field_case_005" / "port_and_loss.json"
    from litz_research.common import resolve_read_path
    reference_path=resolve_read_path(ROOT,reference_path)
    reference = read_json(reference_path)
    manifest = read_json(handoff / "geometry_manifest.json")
    strands = sorted((row for row in manifest if row["kind"] == "straight"), key=lambda row: row["strand_id"])
    if len(strands) != 7 or reference["strands"] != 7 or reference["circle_segments"] != 42:
        raise ValueError("Closure requires the archived seven-strand 42-side fine reference field_case_005.")
    config, _ = native_config("seven", budget)
    stopped = ROOT / "outputs" / NATIVE_STOP_RUN_ID / "results.json"
    stopped=resolve_read_path(ROOT,stopped)
    stop_report = read_json(stopped)
    if (stop_report.get("task") != "native_probe" or stop_report.get("interface_revision") != 2
            or stop_report.get("solver_started") is not False
            or stop_report.get("execution_status") != "failed_interface_or_solver"):
        raise ValueError("The bounded 2D scalar route requires the retained failed R2 native loader evidence.")
    mesh_revision = ROOT / "outputs" / "closure_20261005_ansys_2dmesh_01" / "results.json"
    mesh_revision=resolve_read_path(ROOT,mesh_revision)
    config.update(strand_centers_m=[row["port_start"][:2] for row in strands],
                  strand_ids=[row["strand_id"] for row in strands],
                  strand_diameter_m=reference["diameter_m"], axial_length_m=1.0,
                  return_inner_radius_m=reference["return_inner_radius_m"],
                  return_outer_radius_m=reference["return_outer_radius_m"],
                  outer_domain_radius_m=reference["outer_radius_m"],
                  source_polygon_sides=42, base_source_mesh_length_m=50e-6,
                  return_mesh_length_m=150e-6, air_mesh_length_m=200e-6,
                  return_radius_sensitivity_factor=1.2, outer_domain_sensitivity_factor=1.5,
                  source_model="Ansys_Maxwell2D_42gon_seven_common_voltage_closure",
                  source_run_id=handoff_run_id, source_reference_file=str(reference_path.relative_to(ROOT)),
                  source_reference_sha256=native.sha256(reference_path),
                  closure_schema_version=2, two_d_scalar_revision=2, revert_to_initial_mesh=True,
                  two_d_mesh_revision_reference=str(mesh_revision.relative_to(ROOT)),
                  two_d_mesh_revision_reference_sha256=native.sha256(mesh_revision),
                  two_d_scalar_revision_reason="Second and final bounded 2D revision: failed mesh_01 changed actual coordinates/connectivity with revert_to_initial_mesh=False. Restore True as in successful CalibrateAnsysShortTest.py while retaining strict native mesh identity and final20A verification. Explicit project SaveAs matches the historical Maxwell2D path. Freeze omits only runtime *.semaphore locks and records them. Shared J/B expression loader stays not_run after native R2; no native interface revision is made.",
                  field_export_mode="not_run_after_shared_loader_stop",
                  field_export_stop_reference=str(stopped.relative_to(ROOT)),
                  field_export_stop_reference_sha256=native.sha256(stopped),
                  independent_reference_Rac_ohm_per_m=reference["bundle_Rac_ohm_per_m"],
                  independent_reference_area_m2=reference["polygonal_bundle_area_m2"],
                  independent_reference=reference,
                  source_selection_reason="Fixed field_case_005 strand centers and 42-sided copper geometry for independent fine-reference comparison. All three closure meshes keep this geometry fixed. Legacy 704-element native-circle short test remains a separate archived geometry and is not used as a pure mesh-convergence predecessor.")
    return config, reference_path


def scalar_gate_passed(report):
    return (report.get("execution_status") == SCALAR_PASSED
            and report.get("scalar_validation_status") == "passed"
            and report.get("full_physical_acceptance") == "not_run")


def record_2d_field_export_stop(config, folder):
    """Record unavailable standalone fields without invoking AEDT postprocessing."""
    if config.get("field_export_mode") != "not_run_after_shared_loader_stop":
        raise ValueError("The 2D scalar closure must explicitly retain the shared-loader stop.")
    record = {"schema_version": 2, "source_model": "bounded_2D_scalar_validation_field_export_stop",
              "execution_status": "not_run_field_export", "entries": [], "solver_started": False,
              "reason": "Standalone J/B samples were not attempted after the shared LoadNamedExpressions loader failed in native R2; the bounded native interface attempts are exhausted.",
              "source_failure_run_id": NATIVE_STOP_RUN_ID,
              "source_failure_report": config["field_export_stop_reference"],
              "source_failure_report_sha256": config["field_export_stop_reference_sha256"],
              "scope": "Standard scalar winding-current/solid-loss reports and actual mesh statistics remain independently validated. No standalone J/B samples are supplied. Native project/result files are retained when saving succeeds."}
    dump(folder / "field_export_manifest.json", record)
    dump(folder / "not_run_field_export.json", record)
    return record


def two_d_variations(config, task):
    if task == "2d_mesh":
        return [(f"mesh_factor_{factor:g}", copy.deepcopy(config), config["base_source_mesh_length_m"] * factor)
                for factor in (1.0, 0.75, 0.5)]
    changed = copy.deepcopy(config)
    if task == "2d_return":
        thickness = config["return_outer_radius_m"] - config["return_inner_radius_m"]
        changed["return_inner_radius_m"] *= config["return_radius_sensitivity_factor"]
        changed["return_outer_radius_m"] = changed["return_inner_radius_m"] + thickness
        if changed["return_outer_radius_m"] >= config["outer_domain_radius_m"]:
            raise ValueError("Return variation must fit within the unchanged outer boundary.")
    elif task == "2d_outer":
        changed["outer_domain_radius_m"] *= config["outer_domain_sensitivity_factor"]
    else:
        raise ValueError("Unknown 2D variation task.")
    return [(task, changed, config["base_source_mesh_length_m"] * 0.5)]


def two_d_preflight(config, mesh_length):
    radius = config["strand_diameter_m"] / 2
    source_area = 7 * math.pi * radius ** 2
    return_area = math.pi * (config["return_outer_radius_m"] ** 2 - config["return_inner_radius_m"] ** 2)
    air_area = math.pi * config["outer_domain_radius_m"] ** 2 - source_area - return_area
    estimate = math.ceil(2 * (source_area / mesh_length ** 2
                             + return_area / config["return_mesh_length_m"] ** 2
                             + air_area / config["air_mesh_length_m"] ** 2) + 7 * config["source_polygon_sides"])
    ram = native.available_ram()
    working = int(2 * native.GIB + 50000 * estimate)
    reason = None
    if estimate > LIMITS["triangles_2d"]:
        reason = "predicted_2d_mesh_exceeds_student_limit"
    elif working > min(config["maximum_working_set_GiB"] * native.GIB,
                       ram["free_bytes"] - 8 * native.GIB):
        reason = "predicted_working_memory_exceeds_available_budget"
    return {"execution_status": "blocked_environment_resource_budget" if reason else "passed",
            "reason": reason, "estimated_triangles": estimate, "estimated_working_bytes": working,
            "measured_allocation": False, "estimate_scope": "Area/length heuristic with fixed strand boundary count; actual mesh count is verified independently and Student's license remains enforced.", **ram}


def prerequisite_report(path, task, case, implementation_hash):
    if task in {"preflight", "native_probe", "2d_mesh"}:
        return None
    if path is None:
        raise DependencyStopped("A preceding closure report is required for this task.")
    try:
        report = read_json(path)
    except (OSError, ValueError) as exc:
        raise DependencyStopped("Prerequisite report is missing or unreadable; no AEDT task is dispatched.") from exc
    if not (scalar_gate_passed(report) if task.startswith("2d_") else report.get("execution_status") == "passed"):
        raise DependencyStopped("Prerequisite did not pass; later closure tasks remain not_run.")
    expected = "2d_mesh" if task.startswith("2d_") else "native_probe" if task == "native_coarse" else "native_coarse" if case == "q1" else "native_suite"
    expected_case = "q1" if task.startswith("native_") else "seven"
    if report.get("task") != expected or report.get("case") != expected_case:
        raise DependencyStopped(f"Expected {expected}/{expected_case} prerequisite.")
    if report.get("implementation_sha256") != implementation_hash:
        raise DependencyStopped("Prerequisite implementation differs; revalidate the changed closure entrypoint.")
    if task == "native_suite" and case == "seven" and report.get("full_physical_acceptance") != "passed":
        raise DependencyStopped("Seven-strand native suite requires full Q1 native physical acceptance.")
    return report


def dependent_task_states(task, case, status, run_id):
    dependencies = {
        ("native_probe", "q1"): [("native_coarse", "q1"), ("native_suite", "q1"), ("native_suite", "seven")],
        ("native_coarse", "q1"): [("native_suite", "q1"), ("native_suite", "seven")],
        ("native_suite", "q1"): [("native_suite", "seven")],
        ("2d_mesh", "seven"): [("2d_return", "seven"), ("2d_outer", "seven")],
    }
    return [{"task": dependent, "case": dependent_case, "execution_status": "not_run",
             "solver_started": False, "blocking_run_id": run_id,
             "reason": "awaiting_explicit_serial_dispatch" if status == "passed" or (task.startswith("2d_") and status == SCALAR_PASSED) else "prerequisite_failed_or_stopped",
             "prerequisite_execution_status": status}
            for dependent, dependent_case in dependencies.get((task, case), [])]


def audit_frozen_run(out, report):
    """Read-only consistency check of an Ansys run, including stopped runs."""
    errors = []
    checked = 0
    def verify_file(path, expected=None, allow_empty=False):
        nonlocal checked
        if not path.is_file() or (path.stat().st_size == 0 and not allow_empty):
            errors.append("missing_or_empty:" + str(path.relative_to(out))); return
        checked += 1
        if expected and native.sha256(path) != expected:
            errors.append("hash_mismatch:" + str(path.relative_to(out)))
    for name in ("parameters.json", "environment.json", "model_assumptions.json", "results.json", "test_report.json", "process_status.json", "not_run_dependencies.json"):
        verify_file(out / name)
    hashes = read_json(out / "source_hashes.json") if (out / "source_hashes.json").is_file() else {}
    if not hashes:
        errors.append("source_snapshot_manifest_missing")
    for name, expected in hashes.items():
        verify_file(out / "source_snapshot" / name, expected)
    if (out / "parameters.json").is_file():
        config = read_json(out / "parameters.json")
        expected_budget = 48.0 if report.get("budget") == "high" else 24.0
        if (config.get("maximum_working_set_GiB") != expected_budget or config.get("minimum_system_free_GiB") != 8
                or config.get("solver_timeout_s") != 3600 or config.get("solver_cores") != 4):
            errors.append("runtime_budget_invariants_differ")
    for case in report.get("cases", []):
        folder = out / case["label"]
        verify_file(folder / "results.json")
        if case.get("execution_status") == "passed" or scalar_gate_passed(case):
            snapshot = case.get("saved_project_snapshot")
            if snapshot:
                verify_file(folder / snapshot["file"], snapshot["sha256"])
                manifest_path = folder / snapshot["results_manifest_file"]
                verify_file(manifest_path, snapshot["results_manifest_sha256"])
                if manifest_path.is_file():
                    manifest = read_json(manifest_path)
                    if case.get("solver_started") and not manifest.get("entries"):
                        errors.append("completed_solve_has_no_native_results_companion:" + case["label"])
                    for entry in manifest.get("entries", []):
                        verify_file(folder / entry["file"], entry["sha256"], allow_empty=entry["bytes"] == 0)
            elif case.get("saved_before_release_project"):
                verify_file(folder / case["saved_before_release_project"], case["saved_before_release_project_sha256"])
            else:
                errors.append("passed_case_has_no_frozen_project:" + case["label"])
        for sample in folder.rglob("resource_curve.jsonl"):
            for line in sample.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                if row.get("owned_working_bytes", 0) < 0 or row.get("free_RAM_bytes", 0) < 0:
                    errors.append("invalid_resource_sample:" + str(sample.relative_to(out)))
                if row.get("low_budget_samples", 0) >= 3 and not (sample.parent / "resource_stop.json").is_file():
                    errors.append("missing_resource_stop_evidence:" + str(sample.relative_to(out)))
        if case.get("solver_started"):
            for solve in case.get("solves", []):
                solve_folder = folder / solve["label"]
                verify_file(solve_folder / "mesh_stats.csv")
                verify_file(solve_folder / "actual_mesh_statistics.json")
                verify_file(solve_folder / "mesh_nodes_SI.csv")
                verify_file(solve_folder / "mesh_records.csv")
                statistics = read_json(solve_folder / "actual_mesh_statistics.json") if (solve_folder / "actual_mesh_statistics.json").is_file() else {}
                for kind, count in statistics.get("actual_counts", {}).items():
                    if kind in LIMITS and count > LIMITS[kind]:
                        errors.append("actual_student_limit_exceeded:" + solve["label"] + ":" + kind)
            if case.get("execution_status") == "passed" or scalar_gate_passed(case):
                verify_folder = folder / "verify_20A"
                manifest_path = verify_folder / "field_export_manifest.json"
                verify_file(manifest_path)
                if manifest_path.is_file():
                    manifest = read_json(manifest_path)
                    if scalar_gate_passed(case):
                        verify_file(verify_folder / "not_run_field_export.json")
                        if (manifest.get("execution_status") != "not_run_field_export" or manifest.get("entries") != []
                                or manifest.get("source_failure_run_id") != NATIVE_STOP_RUN_ID
                                or manifest.get("source_failure_report_sha256") != config.get("field_export_stop_reference_sha256")):
                            errors.append("scalar_field_unavailability_not_explicit:" + case["label"])
                    else:
                        if manifest.get("execution_status") != "passed" or len(manifest.get("entries", [])) != 12:
                            errors.append("incomplete_J_B_real_imag_samples:" + case["label"])
                        for entry in manifest.get("entries", []):
                            verify_file(verify_folder / entry["raw_file"], entry["sha256"])
                            verify_file(verify_folder / entry["csv_file"], entry["csv_sha256"])
                        verify_file(verify_folder / "field_sample_points.pts")
                        verify_file(verify_folder / "field_sample_points_SI.csv")
    return {"source_model": "closure_Ansys_frozen_run_selfcheck", "execution_status": "passed" if not errors else "failed",
            "checked_files": checked, "errors": errors, "solver_started": False,
            "scope": "Checks retained data, source hashes, configured/runtime budget evidence and actual Student mesh limits. It performs no AEDT call or field solve."}


def export_mesh_records(project, stats_file, folder, dimension):
    """Preserve native mesh records in CSV without guessing undocumented markers."""
    identity = native.mesh_identity(project, stats_file)
    count = identity.pop("tetrahedra")
    counts = {"triangles_2d" if dimension == 2 else "tetrahedra_3d": count}
    limit = LIMITS["triangles_2d" if dimension == 2 else "tetrahedra_3d"]
    if count > limit:
        raise native.ResourceBlocked("Actual Student mesh element limit exceeded.")
    results = project.with_suffix(".aedtresults")
    nodes, records, surface = [], [], set()
    for entry in identity["files"]:
        file = results / entry["relative_path"]
        text = file.read_text(encoding="utf-8", errors="replace")
        for kind, arity, values in re.findall(r"\b([A-Za-z_]\w*)\[(\d+):\s*([^\]]+)\]", text):
            numbers = [part.strip() for part in values.split(",")]
            if kind == "p" and len(numbers) == 4:
                nodes.append([entry["relative_path"], *numbers])
            else:
                records.append([entry["relative_path"], kind, arity, ",".join(numbers)])
            if dimension == 3 and kind.lower() in {"tri", "triangle", "st", "sf"} and len(numbers) >= 4:
                surface.add((entry["relative_path"], kind, numbers[0]))
        if dimension == 3:
            for value in re.findall(r"(?:n_surface_triangles|n_surf_tris|n_surface_elements)\s*=\s*(\d+)", text, flags=re.I):
                counts["surface_triangles_3d"] = max(counts.get("surface_triangles_3d", 0), int(value))
    if not nodes or not records:
        raise native.InterfaceFailed("Actual mesh coordinate/connectivity CSV export is empty.")
    if dimension == 3:
        raw_stats = stats_file.read_text(encoding="utf-8", errors="replace")
        matches = re.findall(r"(?:Total number of surface(?: mesh)? elements|Total number of surface triangles)\s*[:=]\s*([\d,]+)", raw_stats, re.I)
        if matches:
            counts["surface_triangles_3d"] = max(int(value.replace(",", "")) for value in matches)
        elif surface:
            counts["surface_triangles_3d"] = len(surface)
        if "surface_triangles_3d" not in counts:
            raise native.InterfaceFailed("Actual 3D surface-triangle count unavailable; cannot certify the 8000-element Student gate from a heuristic estimate.")
        if counts["surface_triangles_3d"] > LIMITS["surface_triangles_3d"]:
            raise native.ResourceBlocked("Actual Student surface-triangle limit exceeded.")
    for name, header, rows in (("mesh_nodes_SI.csv", ["mesh_file", "node_id", "x_m", "y_m", "z_m"], nodes),
                               ("mesh_records.csv", ["mesh_file", "record_kind", "declared_arity", "native_values"], records)):
        with (folder / name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream); writer.writerow(header); writer.writerows(rows)
    identity.update(actual_counts=counts, dimension=dimension,
                    marker_semantics="Native record fields retained verbatim. No undocumented material/facet interpretation is assumed.")
    dump(folder / "actual_mesh_statistics.json", identity)
    return identity


def mesh_verifier(app, project, stats_file, folder):
    return export_mesh_records(project, stats_file, folder, 3)


def mesh_2d_areas(stats_file, names):
    # AEDT mesh-statistics mean element areas are SI; sum(area)=count*mean.
    rows = {}
    for line in stats_file.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = [part.strip() for part in line.split("|")]
        if parts and parts[0] in names and len(parts) >= 8:
            rows[parts[0]] = int(parts[1].replace(",", "")) * float(parts[7].replace("D", "E"))
    if set(rows) != set(names) or any(not math.isfinite(value) or value <= 0 for value in rows.values()):
        raise native.InterfaceFailed("Missing/nonfinite per-conductor actual mesh area.")
    return {"source_model": "AEDT_mesh_stats_count_times_mean_area", "areas_m2": rows,
            "precision_scope": "Mean areas are rounded by AEDT mesh statistics; retained as geometry diagnostics, not CAD exactness."}


def sample_points(config, dimension):
    points = []
    radius = config["strand_diameter_m"] / 2
    zs = [0.0] if dimension == 2 else [config["axial_length_m"] * fraction for fraction in (0.05, 0.5, 0.95)]
    for z in zs:
        for x, y in config["strand_centers_m"]:
            points.append([x, y, z])
            for radial in (0.5, 0.9, 0.98):
                for angle in range(16):
                    theta = angle * math.pi / 8
                    points.append([x + radial * radius * math.cos(theta), y + radial * radius * math.sin(theta), z])
        rr = (config["return_inner_radius_m"] + config["return_outer_radius_m"]) / 2
        points.extend([[rr * math.cos(angle * math.pi / 16), rr * math.sin(angle * math.pi / 16), z] for angle in range(32)])
    return points


def export_field_samples(app, config, folder, dimension=3):
    """Archive real/imaginary scalar field samples plus native field files."""
    folder.mkdir(parents=True, exist_ok=True)
    points = sample_points(config, dimension)
    points_file = folder / "field_sample_points.pts"
    with points_file.open("w", encoding="utf-8") as stream:
        stream.write("Unit=m\n")
        stream.writelines(" ".join(format(v, ".17g") for v in point) + "\n" for point in points)
    with (folder / "field_sample_points_SI.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream); writer.writerow(["x_m", "y_m", "z_m"]); writer.writerows(points)
    result = {"source_model": "AEDT_real_imag_field_point_samples", "dimension": dimension,
              "point_count": len(points), "entries": [], "execution_status": "running",
              "phasor": "AEDT field expressions are peak phasors; J/B CSV values explicitly converted to RMS by sqrt(2).",
              "scope": "Interior conductor samples at specified radial positions; scalar integral FLD files are retained separately. These samples are not a complete continuous field."}
    design = "Maxwell 3D" if dimension == 3 else "Maxwell 2D"
    for field, quantity, units in (("J", "Fundamental_Quantity('J')", "A_per_m2_RMS"),
                                   ("B", "Fundamental_Quantity('B')", "T_RMS")):
        for axis in "XYZ":
            for component, operation in (("real", "Real"), ("imag", "Imag")):
                name = f"ClosureSample_{field}{axis}_{component}"
                definition = {"name": name, "description": "Unintegrated real/imag field samples",
                              "design_type": [design], "fields_type": ["Fields"], "solution_type": "",
                              "primary_sweep": "Freq", "assignment": "", "assignment_type": ["Solid"],
                              "operations": [quantity, f"Operation('Scalar{axis}')", f"Operation('{operation}')"],
                              "dependent_expressions": [], "report": ["Data Table"]}
                expression = native.require(app.post.fields_calculator.add_expression(definition, name=name), "Field sample expression rejected: " + name)
                file = folder / (name + ".fld")
                native.require(app.post.export_field_file(quantity=expression, solution=app.nominal_adaptive,
                               output_file=str(file), sample_points_file=str(points_file), export_in_si_system=True,
                               intrinsics={"Freq": "200000Hz", "Phase": "0deg"}), "Field sample export rejected: " + name)
                if not file.is_file():
                    raise native.InterfaceFailed("Field exporter did not write an actual file: " + name)
                numeric = []
                for line in file.read_text(encoding="utf-8", errors="replace").splitlines():
                    try:
                        values = [float(value.replace("D", "E")) for value in line.split()]
                    except ValueError:
                        continue
                    if len(values) == 4 and all(math.isfinite(value) for value in values):
                        numeric.append([*values[:3], values[3] / math.sqrt(2)])
                if len(numeric) != len(points):
                    raise native.InterfaceFailed("Scalar field point export is incomplete/nonfinite: " + name)
                csv_file = folder / (name + ".csv")
                with csv_file.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.writer(stream); writer.writerow(["x_m", "y_m", "z_m", units]); writer.writerows(numeric)
                result["entries"].append({"field": field, "axis": axis, "component": component,
                                          "raw_file": file.name, "csv_file": csv_file.name, "units": units,
                                          "sha256": native.sha256(file), "csv_sha256": native.sha256(csv_file), "execution_status": "passed"})
                dump(folder / "field_export_manifest.json", result)
    result["execution_status"] = "passed"
    dump(folder / "field_export_manifest.json", result)
    return result


def native_probe(config, folder):
    from ansys.aedt.core import Maxwell3d
    from ansys.aedt.core.generic.constants import SolutionsMaxwell3D
    folder.mkdir(exist_ok=False)
    app = None
    project = folder / "native_probe.aedt"
    report = {"source_model": "Ansys_native_APhi_J_expression_load_probe", "execution_status": "running",
              "solver_started": False, "full_physical_acceptance": "not_run", "tests": []}
    try:
        resource = native.preflight(config, config["mesh_lengths_m"][0]); dump(folder / "resource_preflight.json", resource)
        if resource["execution_status"] != "passed":
            raise native.ResourceBlocked(resource["reason"])
        app = Maxwell3d(project=str(project), design="ClosureExpressionProbe", version="2025.2",
                        solution_type=SolutionsMaxwell3D.ACMagneticAPhi, non_graphical=True,
                        new_desktop=True, close_on_exit=True, student_version=True)
        if app.solution_type != SolutionsMaxwell3D.ACMagneticAPhi:
            raise native.InterfaceFailed("Unexpected actual solution type: " + app.solution_type)
        report["actual_solution_type"] = app.solution_type
        with native.ResourceMonitor(app, folder, config) as monitor:
            _, _, _, ends, geometry, _ = native.geometry_model(app, config)
            native.assign_terminals(app, config, ends)
            expressions = native.current_density_expressions(app, config, ends)
            report["saved_project_snapshot"] = freeze_project(app, project, folder)
        if monitor.reason:
            raise native.ResourceBlocked(monitor.reason)
        if not project.is_file():
            raise native.InterfaceFailed("Probe save returned without an actual project.")
        report.update(execution_status="passed", geometry=geometry, expressions=expressions,
                      project_exists=True, project_sha256=native.sha256(project),
                      scope="All configured Jz surface, three-component volume Joule, and side-normal squared-current expressions loaded in actual APhi. No field solution or numerical acceptance is implied.")
    except native.ResourceBlocked as exc:
        report.update(execution_status="blocked_environment_resource_budget", error=str(exc), traceback=traceback.format_exc())
    except Exception as exc:
        report.update(execution_status="failed_interface_or_solver", error=str(exc), traceback=traceback.format_exc())
    finally:
        if app is not None:
            try:
                report["saved_project_snapshot"] = freeze_project(app, project, folder)
                report["project_exists"] = project.is_file()
            except Exception as exc:
                report["project_save_error"] = str(exc)
            try:
                app.desktop_class.release_desktop(close_projects=True, close_on_exit=True)
            except Exception as exc:
                report["desktop_release_error"] = str(exc)
        dump(folder / "results.json", report)
    return report


def run_2d(config, mesh_length, folder):
    from ansys.aedt.core import Maxwell2d
    from ansys.aedt.core.generic.constants import SolutionsMaxwell2D
    import numpy as np
    folder.mkdir(exist_ok=False)
    project, app = folder / "seven_42gon.aedt", None
    report = {"source_model": config["source_model"], "execution_status": "running", "solves": [],
              "tests": [], "solver_started": False, "full_physical_acceptance": "not_run"}
    dump(folder / "parameters.json", {**config, "source_mesh_length_m": mesh_length})
    started = time.monotonic()
    try:
        resource = two_d_preflight(config, mesh_length); dump(folder / "resource_preflight.json", resource)
        if resource["execution_status"] != "passed":
            raise native.ResourceBlocked(resource["reason"])
        app = Maxwell2d(project=str(project), design="SevenClosure42gon", version="2025.2",
                        solution_type=SolutionsMaxwell2D.ACMagnetic, non_graphical=True,
                        new_desktop=True, close_on_exit=True, student_version=True)
        if app.solution_type != SolutionsMaxwell2D.ACMagnetic:
            raise native.InterfaceFailed("Actual 2D solution type is not AC Magnetic.")
        report["actual_solution_type"] = app.solution_type
        app.modeler.model_units = "mm"
        material = app.materials.add_material("closure_copper"); material.conductivity = 5.8e7; material.permeability = 1.0
        air = app.materials.add_material("closure_air"); air.conductivity = 0.0; air.permittivity = 1.0; air.permeability = 1.0
        native.require(app.change_design_settings({"BackgroundMaterialName": "closure_air", "ModelDepth": "1000mm"}), "2D depth/background rejected.")
        sources = []
        for sid, (x, y) in zip(config["strand_ids"], config["strand_centers_m"]):
            sources.append(native.require(app.modeler.create_circle([1000*x, 1000*y, 0], config["strand_diameter_m"]*500,
                               num_sides=42, name="Copper_"+sid, material="closure_copper"), "Source polygon rejected."))
        ret = native.require(app.modeler.create_circle([0,0,0], config["return_outer_radius_m"]*1000, name="ReturnCopper", material="closure_copper"), "Return rejected.")
        void = native.require(app.modeler.create_circle([0,0,0], config["return_inner_radius_m"]*1000, name="ReturnVoid"), "Return void rejected.")
        native.require(app.modeler.subtract(ret, void, keep_originals=False), "Return subtract rejected.")
        region = native.require(app.modeler.create_circle([0,0,0], config["outer_domain_radius_m"]*1000, name="AirRegion", material="closure_air"), "Air region rejected.")
        native.require(app.modeler.subtract(region, [obj.name for obj in sources]+[ret.name], keep_originals=True), "Air subtract rejected.")
        native.require(app.assign_vector_potential([max(region.edges, key=lambda edge: edge.length)], vector_value=0), "Az exterior rejected.")
        windings = {}
        for obj in sources+[ret]:
            name = "ReturnWinding" if obj == ret else "W_"+obj.name
            windings[name] = native.require(app.assign_winding([obj.name], winding_type="Voltage", is_solid=True,
                                    voltage="0V", phase="0deg", parallel_branches=1, name=name), "Solid voltage winding rejected.")
        native.require(app.eddy_effects_on([obj.name for obj in sources]+[ret.name], enable_eddy_effects=True, enable_displacement_current=False), "Copper eddy setting rejected.")
        native.require(app.mesh.assign_length_mesh([obj.name for obj in sources], inside_selection=True,
                       maximum_length=f"{mesh_length*1000:.17g}mm", maximum_elements=None, name="SourceMesh"), "Source mesh rejected.")
        for obj, length, name in ((ret, config["return_mesh_length_m"], "ReturnMesh"), (region, config["air_mesh_length_m"], "AirMesh")):
            native.require(app.mesh.assign_length_mesh([obj.name], inside_selection=True, maximum_length=f"{length*1000:.17g}mm", maximum_elements=None, name=name), name+" rejected.")
        setup = native.require(app.create_setup(name="ClosureSetup"), "2D setup rejected.")
        setup.props.update(Frequency="200000Hz", MaximumPasses=1, MinimumPasses=1, PercentError=1, OutputPerObjectSolidLoss=True)
        native.require(setup.update(), "2D setup update rejected.")
        native.require(app.save_project(str(project)), "2D initial project save rejected.")
        if not project.is_file() or not app.validate_simple():
            raise native.InterfaceFailed("Actual 2D project save/validation failed.")
        fixed_identity = None

        def solve(label, vs, vr):
            nonlocal fixed_identity
            solve_folder = folder / label; solve_folder.mkdir()
            voltages = {}
            for name, boundary in windings.items():
                value = vr if name == "ReturnWinding" else vs
                props = native.voltage_parameters(value)
                boundary.props["Voltage"] = props["Voltage"]; boundary.props["Phase"] = props["phase"]
                native.require(boundary.update(), "Winding voltage update rejected: "+name); voltages[name] = value
            dump(solve_folder / "ports_RMS.json", {name: native.complex_record(value) for name,value in voltages.items()})
            native.require(app.save_project(str(project)), "2D project save before solve rejected.")
            report["solver_started"] = True; dump(folder / "checkpoint.json", report)
            with native.ResourceMonitor(app, solve_folder, config) as monitor:
                solved = app.analyze_setup(setup.name, cores=4, use_auto_settings=False,
                                           revert_to_initial_mesh=config["revert_to_initial_mesh"], blocking=True)
            if monitor.reason:
                raise native.ResourceBlocked(monitor.reason)
            native.require(solved, "Actual 2D field solution failed.")
            native.require(app.export_mesh_stats(setup.name, output_file=str(solve_folder / "mesh_stats.csv")), "Mesh statistics export failed.")
            native.require(app.export_convergence(setup.name, output_file=str(solve_folder / "convergence.csv")), "Convergence export failed.")
            identity = export_mesh_records(project, solve_folder / "mesh_stats.csv", solve_folder, 2)
            if fixed_identity is not None and fixed_identity != identity["identity_sha256"]:
                raise native.NumericalFailed("Actual coordinate/connectivity mesh changed between voltage basis solves.")
            fixed_identity = identity["identity_sha256"]
            data = read_shorttest_solution(app, solve_folder, voltages, [obj.name for obj in sources]+[ret.name])
            if data["errors"]:
                raise native.InterfaceFailed("2D postprocessing failed: "+str(data["errors"]))
            report["solves"].append({"label": label, "mesh_identity": identity, "data": data})
            dump(folder / "checkpoint.json", report)
            return data

        def currents(data):
            return np.array([complex(data[key]["real"], data[key]["imag"]) for key in ("source_current_RMS_A", "return_current_RMS_A")])
        basis_s, basis_r = solve("basis_source", 1+0j, 0j), solve("basis_return", 0j, 1+0j)
        admittance = np.column_stack([currents(basis_s), currents(basis_r)])
        condition = float(np.linalg.cond(admittance))
        if not math.isfinite(condition) or condition > 1e12:
            raise native.NumericalFailed("Ill-conditioned actual 2D port admittance.")
        voltage = np.linalg.solve(admittance, np.array([20+0j,-20+0j]))
        actual = solve("verify_20A", complex(voltage[0]), complex(voltage[1]))
        area = mesh_2d_areas(folder / "verify_20A" / "mesh_stats.csv", [obj.name for obj in sources]+[ret.name])
        dump(folder / "actual_mesh_areas.json", area)
        source_area = sum(area["areas_m2"][obj.name] for obj in sources)
        source_loss = sum(actual["solid_losses_W"][name] for name in windings if name != "ReturnWinding")
        source_rac = source_loss / 400
        strand_i = [complex(actual["winding_currents_RMS_A"][name]["real"],actual["winding_currents_RMS_A"][name]["imag"]) for name in windings if name != "ReturnWinding"]
        port_error = float(np.linalg.norm(currents(actual)-[20,-20])/np.linalg.norm([20,-20]))
        report["tests"] = [native.check("actual_20A_complex_port_constraint",port_error,1e-8),
                           native.check("input_power_equals_reported_solid_loss",actual["power_relative_difference"],1e-3),
                           native.check("actual_mesh_area_matches_frozen_42gon_copper",abs(source_area/config["independent_reference_area_m2"]-1),1e-3)]
        report.update(source_Rac_ohm_per_axial_m=source_rac, source_loss_W_per_axial_m=source_loss,
                      return_loss_W_per_axial_m=actual["solid_losses_W"]["ReturnWinding"], source_Rdc_ohm_per_axial_m=1/(5.8e7*source_area),
                      source_Rac_Rdc=source_rac*5.8e7*source_area, source_copper_area_m2=source_area,
                      source_copper_volume_m3_per_axial_m=source_area, mean_arc_length_growth=1.0,
                      strand_currents_RMS_A=[native.complex_record(value) for value in strand_i],
                      complex_current_deviation_relative=float(np.linalg.norm(np.array(strand_i)-20/7)/np.linalg.norm(strand_i)),
                      terminal_admittance_S=[[native.complex_record(complex(value)) for value in row] for row in admittance],
                      terminal_admittance_condition=condition, source_voltage_RMS_V=native.complex_record(complex(voltage[0])),
                      return_voltage_RMS_V=native.complex_record(complex(voltage[1])),
                      independent_reference_relative_difference=abs(source_rac/config["independent_reference_Rac_ohm_per_m"]-1))
        dump(folder / "port_summary_RMS.json", {key: report[key] for key in ("source_voltage_RMS_V","return_voltage_RMS_V","terminal_admittance_S","strand_currents_RMS_A","source_Rac_ohm_per_axial_m","source_Rdc_ohm_per_axial_m")})
        with (folder / "strand_currents_RMS.csv").open("w",encoding="utf-8",newline="") as stream:
            writer=csv.writer(stream);writer.writerow(["strand_id","real_A_RMS","imag_A_RMS"])
            writer.writerows([sid,value.real,value.imag] for sid,value in zip(config["strand_ids"],strand_i))
        report["field_exports"] = record_2d_field_export_stop(config,folder / "verify_20A")
        scalar_passed = all(test["execution_status"]=="passed" for test in report["tests"])
        report.update(execution_status=SCALAR_PASSED if scalar_passed else "failed_numerical",
                      scalar_validation_status="passed" if scalar_passed else "failed",
                      physical_acceptance_status="limited_fields_unavailable", closure_schema_version=2)
        native.require(app.save_project(str(project)), "Final solved 2D project save failed.")
        report["project_sha256"] = native.sha256(project)
    except native.ResourceBlocked as exc:
        report.update(execution_status="blocked_environment_resource_budget",error=str(exc),traceback=traceback.format_exc())
    except native.NumericalFailed as exc:
        report.update(execution_status="failed_numerical",error=str(exc),traceback=traceback.format_exc())
    except Exception as exc:
        report.update(execution_status="failed_interface_or_solver",error=str(exc),traceback=traceback.format_exc())
    finally:
        if app is not None:
            try:
                report["saved_project_snapshot"] = freeze_project(app, project, folder, explicit_save=True)
                report["project_exists"]=project.is_file()
            except Exception as exc:
                report["project_save_error"]=str(exc)
            try:
                app.desktop_class.release_desktop(close_projects=True,close_on_exit=True)
            except Exception as exc:
                report["desktop_release_error"]=str(exc)
        report["elapsed_seconds"]=time.monotonic()-started
        dump(folder / "results.json",report);dump(folder / "test_report.json",{"tests":report["tests"]})
    return report


def archive_sources(out, reference_path, stop_reference=None, mesh_revision_reference=None):
    snapshot=out / "source_snapshot";snapshot.mkdir()
    for path in (Path(__file__),ROOT / "src/ansys_native3d.py",ROOT / "src/ansys_validate.py",reference_path):
        shutil.copy2(path,snapshot / path.name)
    if stop_reference is not None:
        shutil.copy2(stop_reference,snapshot / "native_probe_r2_results.json")
    if mesh_revision_reference is not None:
        shutil.copy2(mesh_revision_reference,snapshot / "two_d_mesh_01_results.json")
        shutil.copy2(ROOT / "src/CalibrateAnsysShortTest.py",snapshot / "CalibrateAnsysShortTest.py")
    dump(out / "source_hashes.json",{path.name:native.sha256(path) for path in snapshot.iterdir()})


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task",choices=TASKS,required=True)
    parser.add_argument("--case",choices=("q1","seven"),default="seven")
    parser.add_argument("--run-id",required=True)
    parser.add_argument("--budget",choices=("low","high"),default="high")
    parser.add_argument("--prerequisite")
    parser.add_argument("--handoff-run-id",default="full_20261005_handoff")
    parser.add_argument("--interface-revision",type=int,choices=(1,2),default=1,
                        help="Maximum two explicit interface revisions; no automatic solver retry.")
    args=parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9_-]+",args.run_id):
        parser.error("run-id must contain only ASCII letters, digits, underscores and hyphens")
    out=ROOT / "outputs" / args.run_id;out.mkdir(exist_ok=False)
    implementation_hash=native.sha256(Path(__file__))
    report={"run_id":args.run_id,"task":args.task,"case":args.case,"source_model":"Ansys_bounded_closure",
            "execution_status":"running","full_physical_acceptance":"not_run","cases":[],"tests":[],
            "implementation_sha256":implementation_hash,"interface_revision":args.interface_revision,
            "started_UTC":datetime.now(timezone.utc).isoformat(),"solver_started":False,"budget":args.budget}
    started=time.monotonic();exit_code=1
    try:
        if args.task.startswith("2d_") and args.case!="seven":
            raise ValueError("Only seven-strand 2D closure is supported.")
        if args.task in {"native_probe","native_coarse"} and args.case!="q1":
            raise ValueError("Native probe/coarse gate starts with Q1 only.")
        two_d=args.task.startswith("2d_")
        config,reference_path=closure_2d_config(args.handoff_run_id,args.budget) if two_d else native_config(args.case,args.budget)
        config=apply_interface_revision(config,args.interface_revision)
        if two_d:
            archive_sources(out,reference_path,ROOT / config["field_export_stop_reference"],ROOT / config["two_d_mesh_revision_reference"])
            report.update(closure_schema_version=2, two_d_scalar_revision=config["two_d_scalar_revision"],
                          physical_acceptance_status="limited_fields_unavailable", scalar_validation_status="not_run",
                          field_export_mode=config["field_export_mode"], field_export_stop_reference=config["field_export_stop_reference"])
        else:
            archive_sources(out,reference_path)
        dump(out / "parameters.json",config)
        report["source_config_sha256"]=native.sha256(reference_path)
        report["prerequisite"]=str(Path(args.prerequisite).resolve()) if args.prerequisite else None
        versions={}
        for package in ("pyaedt","numpy","scipy","psutil"):
            with contextlib.suppress(importlib.metadata.PackageNotFoundError):versions[package]=importlib.metadata.version(package)
        dump(out / "environment.json",{"python":sys.version,"platform":platform.platform(),"packages":versions,
             "requested_AEDT":"2025.2 Student","RAM":native.available_ram(),"source_git_commit":subprocess.run(
                  ["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True).stdout.strip()})
        dump(out / "model_assumptions.json",{"conventions":"SI, exp(+j omega t), RMS,20C,no independent external field",
             "student_hard_limits":LIMITS,"budget":args.budget,"geometry":config.get("source_selection_reason",config.get("scope")),
             "physical_terminals":"Ideal common voltage; physical termination metal is not modelled.",
             "power_scope":"Reported 2D solid losses close the discretized port system; native 3D additionally integrates independent J surface/volume quantities.",
             "field_export_mode":config.get("field_export_mode","full_field_expression_export"),
             "two_d_scalar_revision_reason":config.get("two_d_scalar_revision_reason")})
        prereq=prerequisite_report(args.prerequisite,args.task,args.case,implementation_hash)
        if native.interface_failure_streak(out,report["source_config_sha256"],implementation_hash)>=2:
            raise native.ResourceBlocked("Unchanged interface failed twice; stop before starting another AEDT session.")
        with (out / "run_log.txt").open("w",encoding="utf-8",buffering=1) as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
            if args.task=="preflight":
                report["cases"]=[{"label":label,"resource_preflight":native.preflight(case_config,mesh)} for label,case_config,mesh in native.case_variations(config,"suite")]
                report["execution_status"]="preflight_only";exit_code=0
            elif args.task=="native_probe":
                result=native_probe(config,out / "probe");result["label"]="probe";report["cases"].append(result)
                report["execution_status"]=result["execution_status"]
            else:
                variations=two_d_variations(config,args.task) if two_d else native.case_variations(config,"pilot" if args.task=="native_coarse" else "suite")
                for index,(label,case_config,mesh) in enumerate(variations):
                    print("START",label,"mesh_length_m",mesh,flush=True)
                    result=run_2d(case_config,mesh,out / label) if two_d else native.run_one(case_config,mesh,out / label,mesh_verifier=mesh_verifier,field_exporter=export_field_samples,project_freezer=freeze_project)
                    result["label"]=label;report["cases"].append(result);report["solver_started"] |= result.get("solver_started",False)
                    print("FINISH",label,result["execution_status"],flush=True);dump(out / "checkpoint.json",report)
                    if not (scalar_gate_passed(result) if two_d else result["execution_status"]=="passed"):
                        report["execution_status"]=result["execution_status"];report["stop_reason"]="case gate failed; later cases remain not_run"
                        report["remaining_cases"]=[{"label":later_label,"mesh_length_m":later_mesh,"execution_status":"not_run","solver_started":False,
                                                    "blocking_case":label,"reason":"preceding_case_gate_failed"} for later_label,_,later_mesh in variations[index+1:]]
                        break
                else:
                    if args.task=="native_suite":
                        report["tests"]=native.summary_tests(config,report["cases"])
                        if len(report["tests"])<5:raise native.NumericalFailed("Native full acceptance requires mesh, return, outer and both length tests.")
                    elif args.task=="2d_mesh":
                        medium,fine=report["cases"][-2:]
                        report["tests"]=[native.check("finest_mesh_Rac_change",abs(fine["source_Rac_ohm_per_axial_m"]/medium["source_Rac_ohm_per_axial_m"]-1),.01),
                                         native.check("independent_same_source_geometry_Rac",fine["independent_reference_relative_difference"],.01)]
                    elif args.task in {"2d_return","2d_outer"}:
                        baseline=prereq["cases"][-1]
                        if config["source_reference_sha256"]!=read_json(Path(args.prerequisite).resolve().parent / "parameters.json")["source_reference_sha256"]:
                            raise ValueError("Boundary sensitivity must use the same frozen fine reference.")
                        report["tests"]=[native.check(args.task+"_Rac_sensitivity",abs(report["cases"][0]["source_Rac_ohm_per_axial_m"]/baseline["source_Rac_ohm_per_axial_m"]-1),.01)]
                    accepted=all(test["execution_status"]=="passed" for test in report["tests"])
                    report["execution_status"]=(SCALAR_PASSED if two_d else "passed") if accepted else "failed_numerical"
                    if two_d:
                        report["scalar_validation_status"]="passed" if accepted else "failed"
                    if args.task=="native_suite" and report["execution_status"]=="passed":report["full_physical_acceptance"]="passed"
            if report["execution_status"]=="passed" or scalar_gate_passed(report):exit_code=0
    except DependencyStopped as exc:
        report.update(execution_status="not_run", stop_reason="prerequisite_gate", error=str(exc), solver_started=False)
    except native.ResourceBlocked as exc:
        report.update(execution_status="blocked_environment_resource_budget",error=str(exc),traceback=traceback.format_exc())
    except native.NumericalFailed as exc:
        report.update(execution_status="failed_numerical",error=str(exc),traceback=traceback.format_exc())
    except Exception as exc:
        report.update(execution_status="failed_configuration_or_interface",error=str(exc),traceback=traceback.format_exc())
    finally:
        report.update(elapsed_seconds=time.monotonic()-started,finished_UTC=datetime.now(timezone.utc).isoformat())
        report["dependent_tasks"]=dependent_task_states(args.task,args.case,report["execution_status"],args.run_id)
        dump(out / "not_run_dependencies.json",{"origin_run_id":args.run_id,"tasks":report["dependent_tasks"],"stop_policy":"Failed prerequisites never dispatch dependent AEDT tasks. Passed prerequisites still require explicit serial dispatch."})
        dump(out / "results.json",report);dump(out / "test_report.json",{"tests":report["tests"],"case_tests":{case["label"]:case.get("tests",[]) for case in report["cases"]}})
        dump(out / "process_status.json",{"process_exit_code":exit_code,"finished_UTC":report["finished_UTC"]})
        try:
            frozen_audit=audit_frozen_run(out,report)
        except Exception as exc:
            frozen_audit={"execution_status":"failed","error":str(exc),"traceback":traceback.format_exc(),"solver_started":False}
        dump(out / "frozen_data_selfcheck.json",frozen_audit)
        report["frozen_data_selfcheck"]=frozen_audit
        if (report["execution_status"]=="passed" or scalar_gate_passed(report)) and frozen_audit["execution_status"]!="passed":
            report.update(execution_status="failed_frozen_data_selfcheck",full_physical_acceptance="not_run" if args.task.startswith("2d_") else "not_verified")
            exit_code=1
            report["dependent_tasks"]=dependent_task_states(args.task,args.case,report["execution_status"],args.run_id)
            dump(out / "not_run_dependencies.json",{"origin_run_id":args.run_id,"tasks":report["dependent_tasks"],"stop_policy":"Frozen data selfcheck failed; dependent AEDT tasks remain not_run."})
        dump(out / "results.json",report)
        dump(out / "process_status.json",{"process_exit_code":exit_code,"finished_UTC":report["finished_UTC"]})
    print(json.dumps({"run_id":args.run_id,"task":args.task,"execution_status":report["execution_status"],"process_exit_code":exit_code},ensure_ascii=False))
    return exit_code


if __name__=="__main__":
    raise SystemExit(main())
