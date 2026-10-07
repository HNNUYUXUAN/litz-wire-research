"""Reproducible local AEDT/PyAEDT validation for the Litz handoff package.

The script separates geometry provenance from solver evidence.  A solver failure is
written to results.json and never converted into a passed physical comparison.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import sys
import traceback
import shutil
from pathlib import Path


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def aggregate_case_status(children):
    """Keep numerical/execution failures visible even if another case is blocked."""
    states = [child.get("execution_status", "not_run") for child in children]
    if any(state.startswith("failed") for state in states):
        return "failed"
    if "blocked_environment_resource_budget" in states:
        return "blocked_environment_resource_budget"
    if states and all(state in {"passed", "executed"} for state in states):
        return "executed"
    return "not_run"


def handoff_dir(root):
    selected = os.environ.get("LITZ_ANSYS_HANDOFF_RUN_ID")
    if selected:
        return root / "outputs" / selected
    candidates = [p.parent for p in (root / "outputs").glob("*/geometry_manifest.json")
                  if (p.parent / "process_status.json").exists()]
    return max(candidates, key=lambda p: p.stat().st_mtime)


def case_records(manifest, case: str):
    if case == "7":
        return [r for r in manifest if r["kind"] == "straight"]
    if case == "640":
        return [r for r in manifest if r["kind"] == "straight640"]
    if case == "curves":
        return [r for r in manifest if r["kind"] in {"crosslayer", "multilevel"}]
    return manifest


def geometry_preflight(root: Path, manifest, records):
    handoff = handoff_dir(root)
    rows = []
    failures = []
    for rec in records:
        kind = rec["kind"]
        solid = handoff / kind / rec["solid_file"]
        centerline = handoff / kind / rec["centerline_file"]
        exists = solid.exists() and centerline.exists()
        units_ok = (
            (kind.startswith("straight") and rec.get("solid_coordinate_units") == "millimetre_declared_in_STEP"
             and abs(float(rec.get("file_length_unit_to_metres", 0)) - 1e-3) < 1e-15)
            or (not kind.startswith("straight") and rec.get("solid_coordinate_units") == "metre_STL_numeric_coordinates"
                and abs(float(rec.get("file_length_unit_to_metres", 0)) - 1.0) < 1e-15)
        )
        row = {
            "kind": kind, "strand_id": rec["strand_id"], "solid": str(solid),
            "centerline": str(centerline), "solid_exists": solid.exists(),
            "centerline_exists": centerline.exists(), "units_declared_ok": units_ok,
            "diameter_m": rec.get("diameter_m"), "arc_length_m": rec.get("arc_length_m"),
        }
        rows.append(row)
        if not exists or not units_ok:
            failures.append(row)
    return rows, failures


def field_case_for(root: Path, strands: int):
    handoff = handoff_dir(root)
    paths = sorted(handoff.glob("field_case_*/port_and_loss.json"))
    if strands == 640:
        paths.sort(key=lambda p: p.parent.name != "field_case_011")
    for p in paths:
        data = load(p)
        if int(data.get("strands", -1)) == strands:
            ports = p.parent / "ports_RMS.json"
            return data, load(ports) if ports.exists() else {}
    return {}, {}


def read_shorttest_solution(app, out, winding_voltages, copper_names):
    catalog = {}
    for report_type in app.post.available_report_types:
        try:
            categories = app.post.available_quantities_categories(report_category=report_type)
            catalog[report_type] = {c: app.post.available_report_quantities(report_category=report_type,
                                          quantities_category=c) for c in categories}
        except Exception as exc:
            catalog[report_type] = {"error": str(exc)}
    dump(out / "post_catalog.json", catalog)
    data = {"winding_currents_RMS_A": {}, "solid_losses_W": {}, "errors": []}
    def quantity(expression):
        solution = app.post.get_solution_data(expressions=expression, setup_sweep_name=app.nominal_adaptive)
        if not solution:
            raise RuntimeError("No solution data: " + expression)
        real = solution.get_expression_data(expression, formula="real", convert_to_SI=True)[1]
        imag = solution.get_expression_data(expression, formula="imag", convert_to_SI=True)[1]
        return complex(real[0], imag[0]), solution.units_data.get(expression)
    for name in winding_voltages:
        try:
            value, unit = quantity("Current(" + name + ")")
            value /= math.sqrt(2)
            data["winding_currents_RMS_A"][name] = {"real": value.real, "imag": value.imag}
        except Exception as exc:
            data["errors"].append(str(exc))
    for name in list(winding_voltages) + [None]:
        expression = "PerWindingSolidLoss(" + name + ")" if name else "SolidLoss"
        try:
            value, unit = quantity(expression)
            data["solid_losses_W"][name or "total"] = value.real
        except Exception as exc:
            data["errors"].append(str(exc))
    currents = {n: complex(v["real"], v["imag"]) for n, v in data["winding_currents_RMS_A"].items()}
    if len(currents) == len(winding_voltages):
        source = sum(i for n, i in currents.items() if n != "ReturnWinding")
        ret = currents["ReturnWinding"]
        data["source_current_RMS_A"] = {"real": source.real, "imag": source.imag}
        data["return_current_RMS_A"] = {"real": ret.real, "imag": ret.imag}
        data["net_current_relative_to_20A"] = abs(source + ret) / 20
        power = sum((winding_voltages[n] * i.conjugate()).real for n, i in currents.items())
        data["input_power_W"] = power
        if "total" in data["solid_losses_W"]:
            data["power_relative_difference"] = abs(power-data["solid_losses_W"]["total"]) / max(abs(power),1e-30)
    dump(out / "port_and_loss.json", data)
    return data


def run_maxwell2d(root: Path, out: Path, strands: int, rows, field_case, ports, short_test=False):
    """Build and solve the straight cross-section in Maxwell 2D AC Magnetic/Az.

    Voltage gradients are the independently generated common-end values from the
    Wolfram field case; Ansys is still responsible for the field/current solution.
    """
    from ansys.aedt.core import Maxwell2d

    project = out / f"maxwell2d_{strands}.aedt"
    app = None
    result = {"solver": "AEDT_Maxwell2D_ACMagnetic", "strands": strands,
              "project": str(project), "execution_status": "started"}
    try:
        from ansys.aedt.core.generic.constants import SolutionsMaxwell2D
        app = Maxwell2d(version="2025.2", solution_type=SolutionsMaxwell2D.ACMagnetic, non_graphical=True,
                        new_desktop=True, close_on_exit=True, student_version=True)
        if app.solution_type != SolutionsMaxwell2D.ACMagnetic:
            raise RuntimeError("Unexpected actual solution type: " + app.solution_type)
        result["actual_solution_type"] = app.solution_type
        app.modeler.model_units = "mm"
        app.materials.add_material("litz_copper").conductivity = 5.8e7
        app.materials.add_material("litz_air").permittivity = 1.0
        app.change_design_settings({"BackgroundMaterialName": "litz_air", "ModelDepth": "1000mm"})
        copper = []
        radius_mm = float(rows[0]["diameter_m"]) * 500.0
        for row in rows:
            rec = next(r for r in rows if r["strand_id"] == row["strand_id"])
            # Port coordinates are available in the manifest row; the row passed here
            # is enriched by the caller with x/y millimetres.
            obj = app.modeler.create_circle([row["x_mm"], row["y_mm"], 0], radius_mm,
                                            name=f"Copper_{row['strand_id']}", material="litz_copper")
            copper.append(obj)
        inner_mm = float(field_case["return_inner_radius_m"]) * 1000.0
        outer_mm = float(field_case["return_outer_radius_m"]) * 1000.0
        outer = app.modeler.create_circle([0, 0, 0], outer_mm, name="ReturnOuter", material="litz_copper")
        inner = app.modeler.create_circle([0, 0, 0], inner_mm, name="ReturnInner")
        app.modeler.subtract(outer, inner, keep_originals=False)
        domain_mm = float(field_case["outer_radius_m"]) * 1000.0 if "outer_radius_m" in field_case else float(field_case.get("outer_domain_radius_m", outer_mm / 1000.0 * 1.5)) * 1000.0
        region = app.modeler.create_circle([0, 0, 0], domain_mm, name="AirRegion", material="litz_air")
        app.modeler.subtract(region, [o.name for o in copper] + [outer.name], keep_originals=True)
        app.assign_vector_potential([max(region.edges, key=lambda edge: edge.length)], vector_value=0)
        if not app.save_project(str(project)) or not project.exists():
            result["project_save_warning"] = "Pre-excitation AEDT project was not written."
        source_v = complex(float(ports.get("source_voltage_gradient_Re_V_per_m", 1.0)),
                           float(ports.get("source_voltage_gradient_Im_V_per_m", 0.0)))
        return_v = complex(float(ports.get("return_voltage_gradient_Re_V_per_m", -1.0)),
                           float(ports.get("return_voltage_gradient_Im_V_per_m", 0.0)))
        voltages = {}
        boundaries = {}
        for obj in copper + [outer]:
            name = "ReturnWinding" if obj == outer else "W_" + obj.name
            voltage = return_v if obj == outer else source_v
            boundary = app.assign_winding(assignment=[obj.name], winding_type="Voltage", is_solid=True,
                          voltage=abs(voltage) * math.sqrt(2), phase=math.degrees(math.atan2(voltage.imag, voltage.real)),
                          parallel_branches=1, current=0, name=name)
            if not boundary:
                raise RuntimeError("Independent solid voltage winding rejected: " + name)
            voltages[name] = voltage
            boundaries[name] = dict(boundary.props)
        app.eddy_effects_on([o.name for o in copper] + [outer.name], enable_eddy_effects=True, enable_displacement_current=False)
        result["voltage_winding_properties"] = boundaries
        result["phasor_conversion"] = "One axial metre; AEDT peak V = sqrt(2) * project RMS V. Returned peak currents divided by sqrt(2)."
        dump(out / "excitation_report.json", result)
        app.save_project(str(project))
        setup = app.create_setup(name="LitzSetup")
        setup.props["Frequency"] = "200kHz"
        setup.props["MaximumPasses"] = 3 if short_test else 10
        setup.props["MinimumPasses"] = 1
        setup.props["PercentError"] = 2 if short_test else 1
        setup.props["OutputPerObjectSolidLoss"] = True
        setup.update()
        result["validation"] = app.validate_simple()
        app.save_project(str(project))
        solved = app.analyze_setup(setup.name, cores=4, use_auto_settings=False, blocking=True)
        result.update({"setup": setup.name, "analyze_setup": bool(solved),
                       "solver_status": "passed" if solved else "failed_solver",
                       "execution_status": "passed" if solved else "failed_solver"})
        if solved:
            result["postprocess"] = read_shorttest_solution(app, out, voltages, [o.name for o in copper] + [outer.name])
            result["postprocess_status"] = "failed_postprocess" if result["postprocess"]["errors"] else "passed"
            if result["postprocess"]["errors"]:
                result["execution_status"] = "failed_postprocess"
            app.export_convergence(setup.name, output_file=str(out / "convergence.csv"))
            app.export_mesh_stats(setup.name, output_file=str(out / "mesh_stats.csv"))
        app.save_project(str(project))
        return result
    except Exception as exc:
        if app is not None:
            try:
                app.save_project(str(project))
            except Exception as save_exc:
                result["project_save_error"] = str(save_exc)
        result.update({"execution_status": "failed_solver_or_license", "error": str(exc),
                       "traceback": traceback.format_exc()})
        return result
    finally:
        if app is not None:
            try:
                app.desktop_class.release_desktop(close_projects=True, close_on_exit=True)
            except Exception:
                pass


def import_curves(out, geometry):
    from ansys.aedt.core import Maxwell3d
    reports = []
    for kind in ("crosslayer", "multilevel"):
        app = None
        report = {"kind": kind, "input_units": "m", "imports": [], "execution_status": "not_run"}
        try:
            from ansys.aedt.core.generic.constants import SolutionsMaxwell3D
            app = Maxwell3d(version="2025.2", solution_type=SolutionsMaxwell3D.ACMagneticAPhi, non_graphical=True,
                            new_desktop=True, close_on_exit=True, student_version=True)
            report["actual_solution_type"] = app.solution_type
            if app.solution_type != SolutionsMaxwell3D.ACMagneticAPhi:
                raise RuntimeError("Unexpected actual solution type: " + app.solution_type)
            app.modeler.model_units = "meter"
            for row in geometry:
                if row["kind"] != kind:
                    continue
                before = set(app.modeler.object_names)
                ok = app.modeler.import_3d_cad(row["solid"], input_file_unit="m", healing=False,
                                              reduce_stl=False, point_coincidence_tolerance=1e-9)
                names = sorted(set(app.modeler.object_names) - before)
                report["imports"].append({"strand_id": row["strand_id"], "success": bool(ok), "objects": names,
                                           "bounding_boxes": {n: app.modeler[n].bounding_box for n in names}})
                dump(out / (kind + "_import_checkpoint.json"), report)
            app.save_project(str(out / (kind + ".aedt")))
            report["limitation"] = "Import alone does not establish closed volume, terminals, finite-end fields or performance. Those acceptance checks remain not_run."
        except Exception as exc:
            report.update(execution_status="blocked_environment_resource_budget", error=str(exc), traceback=traceback.format_exc())
        finally:
            if app is not None:
                try:
                    app.save_project(str(out / (kind + ".aedt")))
                except Exception:
                    pass
                try:
                    app.desktop_class.release_desktop(close_projects=True, close_on_exit=True)
                except Exception:
                    pass
        reports.append(report)
        dump(out / "curve_import_report.json", reports)
    return reports


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--case", choices=["all", "7", "640", "curves"], required=True)
    ap.add_argument("--short-test", action="store_true")
    args = ap.parse_args()
    root, out = Path(args.root), Path(args.out)
    dump(out / "environment.json", {"run_id": out.name, "python": sys.executable,
         "platform": platform.platform(), "case": args.case, "handoff_run_id": handoff_dir(root).name})
    dump(out / "model_assumptions.json", {"sigma_S_per_m": 5.8e7, "frequency_Hz": 200000,
         "phasor": "exp(+j omega t)", "current_RMS_A": 20, "temperature_C": 20,
         "scope": "Common complex voltages from Wolfram; no per-strand forced I/N. Unsupported boundaries stop before solve."})
    (out / "source_snapshot").mkdir(exist_ok=True)
    shutil.copy2(__file__, out / "source_snapshot" / Path(__file__).name)
    if args.case == "all":
        import subprocess
        children = []
        for case in ("7", "640", "curves"):
            child = out / case
            child.mkdir()
            command = [sys.executable, __file__, "--root", str(root), "--out", str(child), "--case", case]
            if args.short_test:
                command.append("--short-test")
            completed = subprocess.run(command, check=False)
            child_result = load(child / "results.json") if (child / "results.json").exists() else {
                "case": case, "execution_status": "failed_process", "error": "Child produced no results.json."}
            child_result["process_exit_code"] = completed.returncode
            if completed.returncode and child_result.get("execution_status") in {"passed", "executed"}:
                child_result["execution_status"] = "failed_process"
            children.append(child_result)
        status = aggregate_case_status(children)
        exit_code = 0 if status == "executed" else 1
        dump(out / "results.json", {"run_id": out.name, "source_model": "Ansys_AEDT_PyAEDT_Litz_validation",
             "execution_status": status, "physical_acceptance_status": "not_run", "cases": children})
        dump(out / "process_status.json", {"run_id": out.name, "process_exit_code": exit_code,
             "finished": __import__("datetime").datetime.now().isoformat()})
        return exit_code
    handoff = handoff_dir(root)
    manifest = load(handoff / "geometry_manifest.json")
    records = case_records(manifest, args.case)
    geometry, failures = geometry_preflight(root, manifest, records)
    dump(out / "geometry_report.json", {"case": args.case, "records": geometry,
                                        "failure_count": len(failures),
                                        "execution_status": "passed" if not failures else "failed_geometry_preflight"})
    result = {
        "run_id": out.name, "case": args.case, "source_model": "Ansys_AEDT_PyAEDT_Litz_validation",
        "execution_status": "passed" if not failures else "failed_geometry_preflight",
        "solver_version": "2025.2 Student", "pyaedt_version": "1.8.0",
        "records": len(records), "geometry_failures": len(failures),
        "platform": platform.platform(), "python": sys.version,
    }
    if failures:
        result["error"] = "Geometry files or explicit SI unit declarations failed preflight."
    else:
        straight = [r for r in records if r["kind"].startswith("straight")]
        if straight:
            strands = 640 if args.case == "640" else 7 if args.case == "7" else None
            if strands:
                field_case, ports = field_case_for(root, strands)
                enriched = []
                for rec in straight:
                    x, y = rec["port_start"][:2]
                    enriched.append({**rec, "x_mm": float(x) * 1000.0, "y_mm": float(y) * 1000.0})
                result["field_source_run_id"] = ports.get("source_run_id")
                result["maxwell"] = run_maxwell2d(root, out, strands, enriched, field_case, ports, args.short_test)
                result["execution_status"] = "executed" if result["maxwell"]["execution_status"] == "passed" else "failed"
                result["physical_acceptance_status"] = "not_run"
                result["limitation"] = "Fixed Wolfram voltage short test is not a 20 A constrained Ansys solve. CalibrateAnsysShortTest.py supplies two basis solves and a verification solve. Mesh/boundary sensitivity remains required for physical acceptance."
        elif args.case in {"curves", "all"}:
            result["curve_import"] = import_curves(out, geometry)
            result["execution_status"] = "blocked_environment_resource_budget" if any(r["execution_status"] == "blocked_environment_resource_budget" for r in result["curve_import"]) else "not_run"
            result["limitation"] = "Curved STL geometry is preflighted; finite-end Maxwell 3D is not forced when the Student solver/import path is unavailable."
    dump(out / "results.json", result)
    dump(out / "environment.json", {"run_id": out.name, "python": sys.executable,
                                     "platform": platform.platform(), "case": args.case,
                                     "handoff_run_id": handoff.name})
    exit_code = 0 if result["execution_status"] in {"passed", "executed"} else 1
    dump(out / "process_status.json", {"run_id": out.name, "process_exit_code": exit_code,
                                       "finished": __import__("datetime").datetime.now().isoformat()})
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
