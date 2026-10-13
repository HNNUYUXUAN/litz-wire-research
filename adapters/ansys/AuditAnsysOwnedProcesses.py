"""Source-bound, read-only OS/archive audit of the four finite Ansys attempts.

Creates one new audit directory. It never opens AEDT, starts a field solver,
terminates a process, or changes an existing attempt's output.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file() and (p / "configs/reference_parameters.json").is_file())
RUNS = (
    "closure_20261005_ansys_probe_r1",
    "closure_20261005_ansys_probe_r2",
    "closure_20261005_ansys_2dmesh_01",
    "closure_20261005_ansys_2dmesh_02",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id):
        parser.error("Explicit safe run ID required")
    out = ROOT / "outputs" / args.run_id
    out.mkdir(exist_ok=False)
    source_files = {}

    def source(path):
        rel = path.relative_to(ROOT).as_posix()
        record = {"path": rel, "bytes": path.stat().st_size, "sha256": digest(path)}
        source_files[rel] = record
        return record

    records = []
    checks = []
    for run_id in RUNS:
        directory = ROOT / "outputs" / run_id
        log_path = directory / "run_log.txt"
        log = log_path.read_text(encoding="utf-8", errors="replace")
        log_pids = sorted({int(pid) for pid in re.findall(r"version started with process ID (\d+)", log)})
        curves = sorted(directory.rglob("resource_curve.jsonl"))
        samples = [json.loads(line) for path in curves for line in path.read_text(encoding="utf-8").splitlines()]
        curve_pids = sorted({int(row["owned_aedt_pid"]) for row in samples})
        process_path = directory / "process_status.json"
        result_path = directory / "results.json"
        process, result = read(process_path), read(result_path)
        released = "Desktop has been released and closed." in log
        identity_ok = len(log_pids) == 1 and log_pids == curve_pids
        checks.append({"id": run_id + "_saved_PID_and_release_evidence", "execution_status": "passed" if identity_ok and released else "failed"})
        record = {
            "run_id": run_id, "owned_aedt_pids": log_pids,
            "saved_PID_source_consistency": "passed" if identity_ok else "failed",
            "historical_process_creation_time_UTC": None,
            "historical_creation_time_evidence_status": "not_recorded",
            "historical_child_process_ids": None,
            "historical_child_PID_evidence_status": "not_recorded",
            "historical_release_log_present": released,
            "release_log_source": source(log_path),
            "resource_curve_sources": [source(path) for path in curves],
            "original_process_status_source": source(process_path),
            "original_result_source": source(result_path),
            "original_process_exit_code": process.get("process_exit_code"),
            "original_execution_status": result.get("execution_status"),
            "field_solver_started": result.get("solver_started"),
            "scope": "The saved AEDT Desktop PID is bound to original log/resource files. Historical OS creation time and child IDs were not retained; no creation-time ownership match is claimed.",
        }
        retained = directory / "release_and_retained_artifacts.json"
        if retained.is_file():
            record["immediate_release_audit_source"] = source(retained)
            record["immediate_release_audit"] = read(retained)
        records.append(record)
    all_pids = sorted({pid for record in records for pid in record["owned_aedt_pids"]})
    filter_text = " OR ".join("ProcessId = " + str(pid) for pid in all_pids)
    script = ("@(Get-CimInstance Win32_Process -Filter '" + filter_text + "' | Select-Object ProcessId,Name,"
              "@{n='created_UTC';e={$_.CreationDate.ToUniversalTime().ToString('o')}}) | ConvertTo-Json -Compress")
    os_check_started = now()
    command = [shutil.which("powershell") or "powershell", "-NoProfile", "-Command", script]
    current = subprocess.run(command, capture_output=True, text=True, check=True, timeout=30)
    current_rows = json.loads(current.stdout) if current.stdout.strip() else []
    if isinstance(current_rows, dict):
        current_rows = [current_rows]
    current_by_pid = {int(row["ProcessId"]): row for row in current_rows}
    write(out / "current_cim_check.json", {"command": command, "process_exit_code": current.returncode,
          "checked_started_UTC": os_check_started, "checked_finished_UTC": now(), "records": current_rows,
          "scope": "Current Get-CimInstance PID/name/OS-creation-time snapshot only; current OS timestamps are never used to fabricate absent historical creation times."})
    for record in records:
        present = [current_by_pid[pid] for pid in record["owned_aedt_pids"] if pid in current_by_pid]
        record["current_PID_name_check"] = present
        record["current_known_PID_absence_status"] = "passed" if not present else "failed_PID_present_ownership_requires_review"
        checks.append({"id": record["run_id"] + "_current_known_PID_absent", "execution_status": "passed" if not present else "failed"})
    checks.append({"id": "exact_four_attempts_have_source_bound_PID_records", "execution_status": "passed" if len(records) == 4 and len(all_pids) == 4 else "failed"})
    verified = all(check["execution_status"] == "passed" for check in checks)
    snapshot = out / "source_snapshot"
    snapshot.mkdir()
    shutil.copy2(Path(__file__), snapshot / Path(__file__).name)
    payload = {"run_id": args.run_id, "source_model": "source_bound_finite_Ansys_Desktop_exit_audit",
        "source_run_ids": list(RUNS), "execution_status": "executed_data_verification" if verified else "failed_data_verification",
        "physical_acceptance_status": "not_applicable", "solver_executed": False,
        "historical_run_outcomes_preserved": True, "owned_aedt_pids": all_pids, "records": records,
        "source_files": list(source_files.values()), "current_CIM_source": source(out / "current_cim_check.json"),
        "historical_creation_time_scope": "Missing for all four AEDT Desktop records. Original release messages and known PID absence are verified; neither historical creation-time identity nor unrecorded child-process exit is claimed.",
        "known_PID_absence_status": "passed" if verified else "failed_or_incomplete",
        "source_script": source(Path(__file__)), "checked_at_UTC": now()}
    write(out / "owned_process_exit.json", payload)
    write(out / "test_report.json", {"execution_status": "passed" if verified else "failed", "tests": checks})
    write(out / "environment.json", {"python": sys.version, "platform": platform.platform(), "solver_executed": False})
    write(out / "results.json", {"run_id": args.run_id, "source_model": payload["source_model"],
          "execution_status": payload["execution_status"], "physical_acceptance_status": "not_applicable",
          "owned_process_audit": "owned_process_exit.json", "owned_process_audit_sha256": digest(out / "owned_process_exit.json"),
          "known_desktop_PID_absence_status": payload["known_PID_absence_status"], "solver_executed": False})
    write(out / "process_status.json", {"process_exit_code": 0 if verified else 1, "finished_UTC": now()})
    print(json.dumps({"run_id": args.run_id, "execution_status": payload["execution_status"], "known_AEDT_PID_absence": all_pids, "historical_creation_times": "not_recorded", "solver_executed": False}))
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
