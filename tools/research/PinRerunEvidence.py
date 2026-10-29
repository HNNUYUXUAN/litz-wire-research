#!/usr/bin/env python3
"""Pin completed fresh reruns into the explicit current run index."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file() and (p / "configs/reference_parameters.json").is_file())
INDEX = ROOT / "docs" / "总控" / "当前运行索引.json"
PIN = {
    "analytic": "rerun_20261005_analytic_report",
    "fem2": "rerun_20261005_fem2_report",
    "circuits": "rerun_20261005_circuits_report",
    "geometry": "rerun_20261005_geometry_report",
    "copper": "rerun_20261005_copper_report",
    "peec": "rerun_20261005_peec_report",
    "voxel": "rerun_20261005_voxel_report",
    "voxel_operator_tests": "rerun_20261005_voxel_operator_tests_report",
    "voxel_operator_quadrature": "rerun_20261005_voxel_operator_quadrature_report",
    "gpu_physics": "rerun_20261005_gpu_physics_report",
    "fem3_cylinder": "rerun_20261005_fem3_cylinder_report",
}

def read(path: Path):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return {}

def main():
    idx = read(INDEX)
    for route, run_id in PIN.items():
        run = ROOT / "outputs" / run_id
        result = read(run / "results.json")
        report = read(run / "test_report.json")
        process = read(run / "process_status.json")
        if not result and not report:
            continue
        execution = str(result.get("execution_status") or report.get("execution_status") or "executed")
        physical = "passed_test_scope_only" if report.get("execution_status") == "passed" else ("failed_numerical" if execution == "failed" else "unknown")
        if process.get("process_exit_code") not in (None, 0):
            execution = "failed_process_exit"
        target = idx.setdefault("routes", {}).setdefault(route, {})
        target.update({
            "selected_run_id": run_id,
            "latest_attempt_id": run_id,
            "execution_status": execution,
            "physical_acceptance_status": physical,
            "failure_reason": None if execution not in {"failed", "failed_process_exit"} else ("test_report_failed" if execution == "failed" else "process_exit"),
            "source_model": result.get("source_model") or target.get("source_model"),
            "selection_reason": "fresh report rerun pinned by explicit run_id",
        })
    idx["schema_version"] = max(3, int(idx.get("schema_version", 0)))
    idx["updated_UTC"] = datetime.now(timezone.utc).isoformat()
    idx["refresh_policy"] = "fresh report reruns are pinned explicitly; historical outputs remain immutable"
    INDEX.write_text(json.dumps(idx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("pinned", ", ".join(PIN))

if __name__ == "__main__": main()
