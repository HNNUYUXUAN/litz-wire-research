"""Read a saved solved short-test without re-running the solver."""
import argparse
import math
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path
from ansys.aedt.core import Maxwell2d
from ansys.aedt.core.generic.constants import SolutionsMaxwell2D
from ansys_validate import load, dump, read_shorttest_solution

ap = argparse.ArgumentParser()
ap.add_argument("--source", required=True)
ap.add_argument("--out", required=True)
args = ap.parse_args()
source, out = Path(args.source).resolve(), Path(args.out).resolve()
out.mkdir(exist_ok=False)
project = source / "maxwell2d_7.aedt"
app = None
result = {"run_id": out.name, "source_model": "Ansys_Maxwell2D_saved_solution_postprocess",
          "source_run_id": source.name, "source_project": str(project), "execution_status": "running",
          "physical_full_acceptance": "not_run"}
try:
    for script in (Path(__file__), Path(__file__).with_name("ansys_validate.py")):
        shutil.copy2(script, out / script.name)
    report = load(source / "excitation_report.json")
    voltages = {}
    for name, props in report["voltage_winding_properties"].items():
        amplitude = float(props["Voltage"].removesuffix("V")) / math.sqrt(2)
        phase = math.radians(float(props["Phase"].removesuffix("deg")))
        voltages[name] = amplitude * complex(math.cos(phase), math.sin(phase))
    app = Maxwell2d(project=str(project), version="2025.2", solution_type=SolutionsMaxwell2D.ACMagnetic,
                    non_graphical=True, new_desktop=True, student_version=True, close_on_exit=True)
    if app.solution_type != SolutionsMaxwell2D.ACMagnetic:
        raise RuntimeError("Unexpected actual solution type: " + app.solution_type)
    data = read_shorttest_solution(app, out, voltages, [])
    result.update(execution_status="passed" if not data["errors"] else "failed_postprocess",
                  actual_solution_type=app.solution_type, postprocess=data)
except Exception as exc:
    result.update(execution_status="failed", error=str(exc), traceback=traceback.format_exc())
    print(result["traceback"], file=sys.stderr)
finally:
    if app is not None:
        try:
            app.desktop_class.release_desktop(close_projects=True, close_on_exit=True)
        except Exception as exc:
            result["desktop_release_error"] = str(exc)
    dump(out / "results.json", result)
    exit_code = 0 if result["execution_status"] == "passed" else 1
    dump(out / "process_status.json", {"process_exit_code": exit_code, "finished": datetime.now().isoformat()})
raise SystemExit(exit_code)
