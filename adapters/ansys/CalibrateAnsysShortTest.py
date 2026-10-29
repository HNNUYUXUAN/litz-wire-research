"""Two voltage basis solves and an independent +20/-20 A verification solve.

Independent solid windings share the source voltage. No strand current is forced.
All three solves revert to the initial mesh with one pass: this is a short test,
not mesh or boundary convergence. Original project and results remain immutable.
"""
import argparse
import cmath
import math
import shutil
import platform
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
import numpy as np
from ansys.aedt.core import Maxwell2d
from ansys.aedt.core.generic.constants import SolutionsMaxwell2D, unit_converter
from ansys.aedt.core.generic.numbers_utils import decompose_variable_value
from ansys_validate import dump, read_shorttest_solution

ap = argparse.ArgumentParser()
ap.add_argument("--source", required=True)
ap.add_argument("--out", required=True)
args = ap.parse_args()
source, out = Path(args.source).resolve(), Path(args.out).resolve()
out.mkdir(exist_ok=False)
dump(out / "environment.json", {"python": sys.version, "python_executable": sys.executable,
     "platform": platform.platform(), "timestamp": datetime.now().isoformat(), "AEDT": "2025.2 Student"})
dump(out / "parameters.json", {"source_run_id": source.name, "frequency_Hz": 200000,
     "target_source_current_RMS_A": 20, "target_return_current_RMS_A": -20,
     "voltage_excitation_convention": "peak = sqrt(2) * RMS", "mesh_passes": 1,
     "cores": 4, "full_physical_acceptance": "not_run"})
project = out / "maxwell2d_7.aedt"
app = None
started = time.monotonic()
report = {"run_id": out.name, "source_model": "Ansys_Maxwell2D_common_voltage_port_short_test",
          "source_run_id": source.name, "execution_status": "running", "solves": [],
          "scope": "One-pass fixed initial-mesh port constraint short test; full mesh/boundary acceptance not_run."}
try:
    shutil.copy2(source / project.name, project)
    for script in (Path(__file__), Path(__file__).with_name("ansys_validate.py")):
        shutil.copy2(script, out / script.name)
    app = Maxwell2d(project=str(project), version="2025.2", solution_type=SolutionsMaxwell2D.ACMagnetic,
                    non_graphical=True, new_desktop=True, student_version=True, close_on_exit=True)
    if app.solution_type != SolutionsMaxwell2D.ACMagnetic:
        raise RuntimeError("Unexpected actual solution type: " + app.solution_type)
    setup = app.get_setup("LitzSetup")
    frequency, frequency_unit = decompose_variable_value(setup.props["Frequency"])
    depth, depth_unit = decompose_variable_value(app.model_depth)
    frequency_hz = unit_converter(frequency, "Freq", frequency_unit, "Hz")
    depth_m = unit_converter(depth, "Length", depth_unit, "meter")
    if not math.isclose(frequency_hz, 200000, rel_tol=1e-12) or not math.isclose(depth_m, 1, rel_tol=1e-12):
        raise RuntimeError("Source must use 200 kHz and one axial metre.")
    report["source_model_check"] = {"frequency_Hz": frequency_hz, "axial_depth_m": depth_m}
    setup.props["MaximumPasses"] = 1
    setup.props["MinimumPasses"] = 1
    setup.props["PercentError"] = 20
    setup.update()
    windings = [b for b in app.boundaries if b.type in {"Winding", "Winding Group"}]
    if len(windings) != 8 or not all(b.props["IsSolid"] for b in windings):
        raise RuntimeError("Expected seven independent solid source windings and one solid return.")
    def solve(label, vs, vr):
        folder = out / label
        folder.mkdir()
        voltages = {}
        for winding in windings:
            value = vr if winding.name == "ReturnWinding" else vs
            winding.props["Voltage"] = str(abs(value) * math.sqrt(2)) + "V"
            winding.props["Phase"] = str(math.degrees(cmath.phase(value))) + "deg"
            winding.update()
            voltages[winding.name] = value
        app.save_project()
        if not app.analyze_setup(setup.name, cores=4, use_auto_settings=False, revert_to_initial_mesh=True):
            raise RuntimeError("Solve failed: " + label)
        data = read_shorttest_solution(app, folder, voltages, [])
        if data["errors"]:
            raise RuntimeError("Postprocess failed: " + str(data["errors"]))
        app.export_mesh_stats(setup.name, output_file=str(folder / "mesh_stats.csv"))
        app.export_convergence(setup.name, output_file=str(folder / "convergence.csv"))
        report["solves"].append({"label": label, "source_voltage_RMS_V": {"real": vs.real, "imag": vs.imag},
                                  "return_voltage_RMS_V": {"real": vr.real, "imag": vr.imag}, "data": data})
        dump(out / "checkpoint.json", report)
        return data
    def terminal_currents(data):
        return np.array([
            complex(data[n]["real"], data[n]["imag"]) for n in ("source_current_RMS_A", "return_current_RMS_A")])
    basis_source = solve("basis_source", 1+0j, 0+0j)
    basis_return = solve("basis_return", 0+0j, 1+0j)
    admittance = np.column_stack([terminal_currents(basis_source), terminal_currents(basis_return)])
    voltage = np.linalg.solve(admittance, np.array([20+0j, -20+0j]))
    actual = solve("verify_20A", complex(voltage[0]), complex(voltage[1]))
    residual = float(np.linalg.norm(terminal_currents(actual)-[20, -20])/np.linalg.norm([20, -20]))
    power_error = actual["power_relative_difference"]
    tests = [{"id": "total_complex_current_constraint", "actual": residual, "tolerance": 1e-8,
              "execution_status": "passed" if residual <= 1e-8 else "failed"},
             {"id": "input_power_equals_solid_loss", "actual": power_error, "tolerance": 1e-3,
              "execution_status": "passed" if power_error <= 1e-3 else "failed"}]
    report.update(execution_status="passed" if all(t["execution_status"] == "passed" for t in tests) else "failed_numerical",
                  terminal_admittance_condition_number=float(np.linalg.cond(admittance)),
                  total_current_relative_residual=residual, tests=tests, actual_solution_type=app.solution_type)
    dump(out / "test_report.json", tests)
    dump(out / "results.json", report)
    app.save_project()
except Exception as exc:
    report.update(execution_status="failed", error=str(exc), traceback=traceback.format_exc())
    print(report["traceback"], file=sys.stderr)
finally:
    if app is not None:
        try:
            app.desktop_class.release_desktop(close_projects=True, close_on_exit=True)
        except Exception as exc:
            report["desktop_release_error"] = str(exc)
    exit_code = 0 if report["execution_status"] == "passed" else 1
    report["elapsed_s"] = time.monotonic() - started
    dump(out / "results.json", report)
    dump(out / "process_status.json", {"process_exit_code": exit_code, "finished": datetime.now().isoformat()})
raise SystemExit(exit_code)
