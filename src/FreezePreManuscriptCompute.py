"""Pin explicit finite-campaign evidence and check the high-host release gate.

Pin is performed before the final read-only archive audit. Release never rewrites
the pinned index or audited state, and never executes a physical solver.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

import PreManuscriptClosure as closure

ROOT = closure.ROOT
TERMINAL = {
    "baseline_reused", "completed_scope_pass", "completed_scope_fail",
    "completed_scientific_scope_wrapper_exit_unknown", "completed_data_verification",
    "completed_data_export", "completed_recovery_limited",
    "failed_interface_budget_exhausted", "failed_numerical_budget_exhausted",
    "failed_fixed_mesh_validation_budget_exhausted",
    "not_run_failed_prerequisite", "not_run_not_required", "not_completed_time_budget",
    "blocked_environment_resource_budget",
}


def safe_run(run_id):
    if not isinstance(run_id, str) or not closure.RUN_RE.fullmatch(run_id):
        raise ValueError("Explicit safe run ID required")
    directory = ROOT / "outputs" / run_id
    if not directory.is_dir():
        raise FileNotFoundError(directory)
    return directory


def report_checks(report):
    rows = report.get("tests", report.get("checks", []))
    return list(rows.values()) if isinstance(rows, dict) else rows


def process_evidence(directory):
    path = directory / "process_status.json"
    process = closure.read(path)
    if isinstance(process, dict):
        return process, {"path": path.relative_to(ROOT).as_posix(), "sha256": closure.digest(path)}
    path = directory / "wrapper_resource_observation.json"
    observation = closure.read(path)
    wrapper_exit = observation.get("wrapper_exit_code", observation.get("wrapper_process_exit_code")) if isinstance(observation, dict) else None
    if not isinstance(observation, dict) or "kernel_exit_code" not in observation or not isinstance(wrapper_exit, int):
        raise ValueError("Missing original process status or explicit wrapper/unknown-native-exit evidence: " + str(directory))
    return {"process_exit_code": observation["kernel_exit_code"], "wrapper_exit_code": wrapper_exit}, {
        "path": path.relative_to(ROOT).as_posix(), "sha256": closure.digest(path),
        "scope": "native exit unknown; observed wrapper failure retained; no process status invented"}


def validate_selection(selection):
    config = closure.read(closure.DEFAULT_CONFIG)
    required = {row["task_id"] for row in closure.inventory(config)}
    decisions = selection.get("task_finalizations", {})
    if required != set(decisions):
        raise ValueError("Final task coverage differs: " + repr({"missing": sorted(required-set(decisions)),
                                                               "unknown": sorted(set(decisions)-required)}))
    for task, row in decisions.items():
        if row.get("final_status") not in TERMINAL or not row.get("reason"):
            raise ValueError("Task lacks a supported terminal state/reason: " + task)
        if not row.get("source_run_ids"):
            raise ValueError("Task lacks evidence references: " + task)
        for run in row["source_run_ids"]:
            safe_run(run)
    routes = [pin["route"] for pin in selection.get("route_pins", [])]
    if len(routes) != len(set(routes)):
        raise ValueError("Duplicate explicit closure route")
    for pin in selection.get("route_pins", []):
        if not closure.RUN_RE.fullmatch(pin["route"]) or not pin["route"].startswith("closure_"):
            raise ValueError("Closure routes must be additive explicit names")
        run = safe_run(pin["run_id"])
        for name in ("results.json", "test_report.json"):
            if not isinstance(closure.read(run / name), dict):
                raise ValueError("Missing readable original " + name + " in " + str(run))
        process_evidence(run)
        if not pin.get("physical_acceptance_status") or not pin.get("scope"):
            raise ValueError("Every route requires explicit acceptance and applicability")
        if pin["physical_acceptance_status"].startswith("passed"):
            report = closure.read(run / "test_report.json")
            if report.get("execution_status") != "passed":
                raise ValueError("A passing scoped conclusion lacks a passing original report: " + pin["route"])
    return decisions


def make_folder(run_id):
    if not closure.RUN_RE.fullmatch(run_id):
        raise ValueError("Invalid run ID")
    folder = ROOT / "outputs" / run_id
    folder.mkdir(exist_ok=False)
    closure.snapshot(folder, closure.DEFAULT_CONFIG)
    return folder


def pin(selection_path, run_id):
    selection = closure.read(selection_path)
    decisions = validate_selection(selection)
    folder = make_folder(run_id)
    shutil.copy2(selection_path, folder / "selection.json")
    shutil.copy2(closure.INDEX, folder / "index_before.json")
    index = closure.read(closure.INDEX)
    for item in selection["route_pins"]:
        directory = safe_run(item["run_id"])
        result = closure.read(directory / "results.json")
        checks = report_checks(closure.read(directory / "test_report.json"))
        process, process_source = process_evidence(directory)
        native_exit = process.get("process_exit_code")
        execution = result.get("execution_status", "unknown")
        if native_exit is None:
            execution = "unknown"
        elif native_exit != 0:
            execution = "failed_process_exit"
        row = {
            "selected_run_id": item["run_id"], "latest_attempt_id": item["run_id"],
            "run_id": item["run_id"], "execution_status": execution,
            "physical_acceptance_status": item["physical_acceptance_status"],
            "scientific_execution_status": item.get("scientific_execution_status", result.get("execution_status", "unknown")),
            "source_model": result.get("source_model", "bounded_closure"),
            "failure_reason": item.get("failure_reason", result.get("failure_reason")),
            "scope": item["scope"], "process_exit": native_exit, "checks": checks,
            "process_evidence": process_source, "wrapper_exit_code": process.get("wrapper_exit_code"),
            "selection_reason": "explicit finite pre-manuscript campaign; historical routes preserved",
            "related_run_ids": item.get("related_run_ids", []),
            "metrics": item.get("metrics", {}),
            "parameter_source_files": item.get("parameter_source_files", []),
            "parameter_scope": item.get("parameter_scope"),
            "figures": [p.relative_to(ROOT).as_posix() for p in directory.rglob("*.svg")],
            "files": [p.relative_to(ROOT).as_posix() for p in directory.rglob("*") if p.is_file()],
        }
        index.setdefault("routes", {})[item["route"]] = row
    index["updated_UTC"] = closure.now()
    index["closure_selection"] = {
        "run_id": run_id, "selection_path": (folder / "selection.json").relative_to(ROOT).as_posix(),
        "selection_sha256": closure.digest(folder / "selection.json"),
        "compute_status": "finite_tasks_finalized_low_profile_delivery_pending",
    }
    closure.write(closure.INDEX, index)
    # Use the same state lock as runtime registration. No solver is started here.
    with closure.state_lock():
        state = closure.read(closure.STATE, {})
        state.setdefault("finalized_tasks", {}).update(decisions)
        state["updated_at_UTC"] = closure.now()
        state["final_selection_run_id"] = run_id
        closure.write(closure.STATE, state)
    shutil.copy2(closure.INDEX, folder / "index_after.json")
    closure.write(folder / "results.json", {"run_id": run_id, "source_model": "explicit_closure_evidence_pinning",
                  "execution_status": "executed_data_export", "physical_acceptance_status": "not_applicable",
                  "index_sha256": closure.digest(closure.INDEX), "terminal_task_count": len(decisions),
                  "new_route_count": len(selection["route_pins"]), "solver_executed": False})
    closure.write(folder / "process_status.json", {"process_exit_code": 0, "finished_UTC": closure.now()})
    print(json.dumps({"run_id": run_id, "pinned_routes": len(selection["route_pins"]), "terminal_tasks": len(decisions)}))
    return 0


def active_owned_processes(selection):
    script = "Get-CimInstance Win32_Process | Select-Object ProcessId,Name,@{n='created_UTC';e={$_.CreationDate.ToUniversalTime().ToString('o')}} | ConvertTo-Json -Compress"
    result = subprocess.run([closure.powershell(), "-NoProfile", "-Command", script], capture_output=True, text=True, check=True)
    processes = json.loads(result.stdout)
    if isinstance(processes, dict):
        processes = [processes]
    active = {int(p["ProcessId"]): p for p in processes}
    owned, remaining = [], []
    inspected_ansys_runs = set()
    source_runs = set(selection.get("campaign_run_ids", []))
    for run in source_runs:
        immediate = closure.read(safe_run(run) / "process_ownership.json", {})
        if immediate.get("process_id") and immediate.get("created_UTC"):
            pid = int(immediate["process_id"])
            current = active.get(pid)
            record = {"run_id": run, **immediate, "active_same_creation_time": bool(current and
                abs((closure.datetime.fromisoformat(current["created_UTC"].replace("Z", "+00:00")) -
                     closure.datetime.fromisoformat(immediate["created_UTC"].replace("Z", "+00:00"))).total_seconds()) < .01)}
            owned.append(record)
            if record["active_same_creation_time"]:
                remaining.append(record)
        summary = closure.read(safe_run(run) / "resource_summary.json", {})
        for old in summary.get("owned_processes", []):
            pid = int(old["process_id"])
            current = active.get(pid)
            record = {"run_id": run, **old, "active_same_creation_time": bool(current and
                abs((closure.datetime.fromisoformat(current["created_UTC"].replace("Z", "+00:00")) -
                     closure.datetime.fromisoformat(old["created_UTC"].replace("Z", "+00:00"))).total_seconds()) < .01)}
            owned.append(record)
            if record["active_same_creation_time"]:
                remaining.append(record)
        environment = closure.read(safe_run(run) / "environment.json", {})
        if environment.get("process_id") and not summary.get("owned_processes"):
            pid = int(environment["process_id"])
            current = active.get(pid)
            record = {"run_id": run, "process_id": pid, "name": "wolfram",
                      "ownership_evidence": "original stage environment.json process_id",
                      "historical_creation_time": None,
                      "active_owned_pid_name": bool(current and "wolfram" in current["Name"].lower())}
            owned.append(record)
            if record["active_owned_pid_name"]:
                remaining.append(record)
        retained = closure.read(safe_run(run) / "release_and_retained_artifacts.json", {})
        pids = retained.get("owned_aedt_pids", [])
        if retained.get("owned_aedt_pid") is not None:
            pids = [*pids, retained["owned_aedt_pid"]]
        for pid in pids:
            current = active.get(int(pid))
            # These native runs additionally record an immediate post-release absence
            # check. A same-PID AEDT still present now is a release-gate failure.
            record = {"run_id": run, "process_id": pid, "name": "ansysedt",
                      "ownership_evidence": "saved release_and_retained_artifacts.json",
                      "historical_creation_time": None,
                      "active_owned_pid_name": bool(current and "ansysedt" in current["Name"].lower())}
            owned.append(record)
            inspected_ansys_runs.add(run)
            if retained.get("owned_processes_still_present") or record["active_owned_pid_name"]:
                remaining.append(record)
    for evidence in selection.get("Ansys_cleanup_evidence", []):
        path = ROOT / evidence["path"]
        if closure.digest(path) != evidence["sha256"]:
            raise ValueError("Ansys process audit SHA changed")
        document = closure.read(path, {})
        if not document.get("source_files"):
            raise ValueError("Ansys process audit lacks original source hashes")
        for source in document["source_files"]:
            if closure.digest(ROOT / source["path"]) != source["sha256"]:
                raise ValueError("Ansys process ownership source SHA changed")
        for entry in document.get("records", []):
            if not entry.get("release_log_source") or not entry.get("owned_aedt_pids") or entry.get("saved_PID_source_consistency") != "passed":
                raise ValueError("Ansys audit lacks original ownership source/PID")
            sources = [entry["release_log_source"], *entry.get("resource_curve_sources", [])]
            for source in sources:
                if closure.digest(ROOT / source["path"]) != source["sha256"]:
                    raise ValueError("Ansys process ownership source SHA changed")
            for pid in entry.get("owned_aedt_pids", []):
                current = active.get(int(pid))
                record = {"run_id": entry["run_id"], "process_id": pid,
                          "ownership_evidence": evidence["path"], "historical_creation_time": None,
                          "active_owned_pid_name": bool(current and "ansysedt" in current["Name"].lower())}
                owned.append(record)
                inspected_ansys_runs.add(entry["run_id"])
                if record["active_owned_pid_name"]:
                    remaining.append(record)
    expected_ansys = set()
    for task in ("ansys_2d_mesh_seven", "ansys_native_probe_q1"):
        expected_ansys.update(selection["task_finalizations"][task]["source_run_ids"])
    if not expected_ansys.issubset(inspected_ansys_runs):
        raise ValueError("Ansys process-exit audit omits attempted runs: " + repr(sorted(expected_ansys-inspected_ansys_runs)))
    return {"checked_at_UTC": closure.now(), "scope": "recorded process IDs plus creation times; unrelated apps retained",
            "records": owned, "remaining": remaining,
            "Ansys_cleanup_evidence": selection.get("Ansys_cleanup_evidence", []),
            "Ansys_ownership_scope": "saved PID/name/release logs and current absence; historical creation times were not saved",
            "Ansys_attempted_runs_checked": sorted(expected_ansys)}


def release(selection_path, run_id, audit_run):
    selection = closure.read(selection_path)
    decisions = validate_selection(selection)
    index = closure.read(closure.INDEX, {})
    if closure.digest(selection_path) != index.get("closure_selection", {}).get("selection_sha256"):
        raise ValueError("Release selection differs from the explicitly pinned selection")
    state = closure.read(closure.STATE, {})
    if any(state.get("finalized_tasks", {}).get(task) != row for task, row in decisions.items()):
        raise ValueError("Release decisions differ from the finalized task state")
    attempted = {row["run_id"] for row in state.get("runs", []) if row.get("run_id")}
    declared_attempts = set(selection.get("campaign_run_ids", []))
    if not attempted.issubset(declared_attempts):
        raise ValueError("Process release coverage omits recorded campaign attempts: " + repr(sorted(attempted-declared_attempts)))
    audit = safe_run(audit_run)
    inventory = closure.read(audit / "archive_inventory.json", {})
    audit_result = closure.read(audit / "results.json", {})
    audit_process = closure.read(audit / "process_status.json", {})
    if audit_process.get("process_exit_code") != 0 or inventory.get("unstable_or_unavailable_paths") or inventory.get("LFS_pointer_paths"):
        raise ValueError("Final raw archive audit did not pass")
    if not inventory.get("files"):
        raise ValueError("Empty final archive inventory")
    matrix = closure.read(audit / "audit_matrix.json", {})
    if matrix.get("errors") or closure.read(audit / "test_report.json", {}).get("execution_status") != "passed":
        raise ValueError("Final baseline/source audit is incomplete")
    frozen_index = matrix.get("frozen_index_sha256", audit_result.get("frozen_index_sha256"))
    if frozen_index != closure.digest(closure.INDEX):
        raise ValueError("Final audit no longer matches the pinned index")
    if matrix.get("closure_state_snapshot_sha256") != closure.digest(closure.STATE):
        raise ValueError("Final audit no longer matches the task state")
    for entry in inventory["files"]:
        original = ROOT / entry["path"]
        if not original.is_file() or original.stat().st_size != entry["bytes"] or original.stat().st_mtime_ns != entry["mtime_ns"]:
            raise ValueError("An audited original changed after final hashing: " + entry["path"])
    verification = decisions["frozen_physics_verify"]
    if verification["final_status"] != "completed_data_verification":
        raise ValueError("Raw numerical readback has not passed")
    accepted = verification.get("accepted_validation_run_id")
    if accepted not in verification["source_run_ids"]:
        raise ValueError("Explicit accepted aggregate validation evidence required")
    raw = safe_run(accepted)
    if closure.read(raw / "process_status.json", {}).get("process_exit_code") != 0 or closure.read(raw / "test_report.json", {}).get("execution_status") != "passed":
        raise ValueError("Accepted original-cache verification process/checks failed: " + str(accepted))
    combined = closure.read(raw / "frozen_physics_validation.json", {})
    expected_cases = selection.get("raw_numeric_case_run_ids", [])
    if not expected_cases or combined.get("execution_status") != "passed_original_numeric_agreement" or set(combined.get("ReferenceRuns", [])) != set(expected_cases):
        raise ValueError("Accepted numeric readback does not cover the explicitly frozen physical cases")
    if combined.get("selected_case_count") != len(expected_cases):
        raise ValueError("Accepted numeric readback case count differs")
    process = active_owned_processes(selection)
    if process["remaining"]:
        raise ValueError("Recorded campaign processes remain active: " + repr(process["remaining"]))
    folder = make_folder(run_id)
    shutil.copy2(selection_path, folder / "selection.json")
    closure.write(folder / "process_release_check.json", process)
    closure.write(folder / "results.json", {
        "run_id": run_id, "source_model": "pre_manuscript_high_host_release_gate", "execution_status": "executed",
        "physical_acceptance_status": "mixed_scopes_and_preserved_failures", "high_compute_ready_to_release": True,
        "terminal_tasks": decisions, "frozen_index_sha256": frozen_index,
        "raw_archive_inventory": {"run_id": audit_run, "path": (audit / "archive_inventory.json").relative_to(ROOT).as_posix(),
                                  "sha256": closure.digest(audit / "archive_inventory.json"), "files": len(inventory["files"])},
        "next_required_profile": "low32", "low_profile_acceptance_status": "pending_actual_host_switch",
        "remaining_work": ["actual 8-logical-processor/32-GiB/no-GPU environment acceptance",
                           "frozen JSON/CSV export and chart rebuild", "archive-mode Notebook evaluated output and Markdown delivery",
                           "directory-with-spaces restore and transferable package checks", "public candidate redistribution inventory"],
        "research_boundaries": selection.get("research_boundaries", []), "solver_executed": False,
    })
    closure.write(folder / "test_report.json", {"execution_status": "passed", "tests": [
        {"id": "all_finite_compute_tasks_have_terminal_state", "passed": True},
        {"id": "final_archive_hashes_and_LFS_entities", "passed": True},
        {"id": "index_matches_final_audit", "passed": True},
        {"id": "recorded_owned_solver_processes_exited", "passed": True}]})
    closure.write(folder / "process_status.json", {"process_exit_code": 0, "finished_UTC": closure.now()})
    print(json.dumps({"run_id": run_id, "high_compute_ready_to_release": True, "low_profile_acceptance_status": "pending_actual_host_switch"}))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=("pin", "release"), required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--audit-run")
    args = parser.parse_args()
    return pin(args.selection, args.run_id) if args.action == "pin" else release(args.selection, args.run_id, args.audit_run)


if __name__ == "__main__":
    raise SystemExit(main())
