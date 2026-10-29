"""Small Windows ownership contract, using only self-owned Python sleep children."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
from ctypes import wintypes
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def retained_exit(child):
    get_exit = ctypes.WinDLL("kernel32", use_last_error=True).GetExitCodeProcess
    get_exit.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    get_exit.restype = wintypes.BOOL
    code = wintypes.DWORD()
    if not get_exit(child._handle, ctypes.byref(code)):
        raise ctypes.WinError(ctypes.get_last_error())
    return code.value


def current_pid(closure, pid):
    script = (f"Get-CimInstance Win32_Process -Filter 'ProcessId = {int(pid)}' | "
              "Select-Object ProcessId,Name,@{n='created_UTC';e={$_.CreationDate.ToUniversalTime().ToString('o')}} | ConvertTo-Json -Compress")
    result = subprocess.run([closure.powershell(), "-NoProfile", "-Command", script], capture_output=True, text=True, check=True)
    return json.loads(result.stdout) if result.stdout.strip() else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="closure_20261005_custom_observer_failure_fixture_01")
    args = parser.parse_args()
    folder = ROOT / "outputs" / args.run_id
    folder.mkdir(exist_ok=False)
    sources = []
    for relative in ("src/PreManuscriptClosure.py", "src/FreezePreManuscriptCompute.py", "tests/TestCustomObserverFailure.py"):
        path = ROOT / relative
        frozen = folder / "source_snapshot" / relative
        frozen.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, frozen)
        sources.append({"path": relative, "sha256": digest(frozen), "frozen_path": frozen.relative_to(folder).as_posix()})
    command = [sys.executable, "-c", "import time; time.sleep(120)"]
    write(folder / "parameters.json", {"run_id": args.run_id, "command": command,
          "observer_mock": "OSError('fixture_observer_failure')", "budget_bytes": 1024**3,
          "wrong_creation_offset_seconds": 1, "maximum_owned_sleep_children": 2,
          "solver_started": False, "Wolfram_started": False, "Ansys_started": False,
          "frozen_before_first_child": True, "timestamp_UTC": datetime.now(timezone.utc).isoformat()})
    sys.path.insert(0, str(ROOT / "src"))
    import PreManuscriptClosure as closure

    checks, children, evidence = [], [], []

    def check(name, passed, details):
        checks.append({"name": name, "passed": bool(passed), "evidence": details})

    original_native_creation = closure.native_child_creation

    def capture_creation(child):
        born = original_native_creation(child)
        children.append((child, born))
        return born

    observer = folder / "observer_failure"
    observer.mkdir()
    try:
        with patch.object(closure, "observe_processes", side_effect=OSError("fixture_observer_failure")), \
                patch.object(closure, "native_child_creation", side_effect=capture_creation):
            monitored = closure.run_custom_monitored(command, observer, os.environ.copy(), 1024**3)
        status = closure.read(observer / "process_status.json", {})
        ownership = closure.read(observer / "process_ownership.json", {})
        cleanup = closure.read(observer / "monitor_cleanup.json", {})
        summary = closure.read(observer / "resource_summary.json", {})
        check("observer_failure_returns_monitor2", monitored.returncode == 2, {"actual_returncode": monitored.returncode})
        check("observer_failure_type_preserved", status.get("failure", {}).get("type") == "OSError" and
              cleanup.get("failure", {}).get("message") == "fixture_observer_failure", {"process_status": status, "monitor_cleanup": cleanup})
        check("child_actual_exit137_preserved_separately", status.get("process_exit_code") == 137 and
              status.get("monitor_exit_code") == 2 and cleanup.get("observed_child_exit_code") == 137,
              {"child_exit": status.get("process_exit_code"), "monitor_exit": status.get("monitor_exit_code"), "cleanup_exit": cleanup.get("observed_child_exit_code")})
        check("ownership_creation_saved_before_observer", ownership.get("created_UTC") == summary.get("native_root_creation_UTC") and
              bool(ownership.get("created_UTC")), {"ownership": ownership, "summary_native_root_creation_UTC": summary.get("native_root_creation_UTC")})
        check("cleanup_ownership_PID_matches_original_root", ownership.get("process_id") == cleanup.get("root_process_id") and
              any(row.get("process_id") == ownership.get("process_id") and row.get("terminated_original_Popen_handle") is True for row in cleanup.get("cleanup", [])),
              {"ownership_process_id": ownership.get("process_id"), "cleanup": cleanup})
        check("failed_observer_does_not_fabricate_resource_curve", summary.get("peak_sampled_process_tree_working_bytes") is None and
              summary.get("resource_scope") == "monitor failed; complete resource curve unavailable",
              {"peak": summary.get("peak_sampled_process_tree_working_bytes"), "scope": summary.get("resource_scope")})
        if not children:
            raise RuntimeError("Observer fixture did not capture its own child")
        monitored_child, monitored_creation = children[0]
        actual_exit = retained_exit(monitored_child)
        evidence.append({"case": "observer_failure", "process_id": monitored_child.pid, "created_UTC": monitored_creation.isoformat(),
                         "actual_exit_code_original_handle": actual_exit, "cleanup_evidence_path": "observer_failure/monitor_cleanup.json"})
        check("observer_actual_exit137_original_retained_handle", actual_exit == 137, evidence[-1])
        active = current_pid(closure, monitored_child.pid)
        check("observer_original_root_PID_absent", active is None, {"process_id": monitored_child.pid, "current_CIM": active})

        with (folder / "direct_child_log.txt").open("w", encoding="utf-8") as log:
            direct = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            direct_created = original_native_creation(direct)
            children.append((direct, direct_created))
            wrong = closure.terminate_known_process(direct.pid, (direct_created + timedelta(seconds=1)).isoformat())
            check("wrong_creation_refused_and_direct_child_alive", wrong is False and direct.poll() is None,
                  {"process_id": direct.pid, "terminate_return": wrong, "actual_poll": direct.poll()})
            correct = closure.terminate_known_process(direct.pid, direct_created.isoformat())
            direct_return = direct.wait(timeout=10)
            direct_exit = retained_exit(direct)
            evidence.append({"case": "direct_native_stop", "process_id": direct.pid, "created_UTC": direct_created.isoformat(),
                             "terminate_return": correct, "actual_Popen_returncode": direct_return,
                             "actual_exit_code_original_handle": direct_exit})
            check("correct_creation_accepted_actual_exit137", correct is True and direct_return == 137 and direct_exit == 137, evidence[-1])
        active = current_pid(closure, direct.pid)
        check("direct_original_root_PID_absent", active is None, {"process_id": direct.pid, "current_CIM": active})
    except BaseException as exc:
        check("fixture_exception", False, {"type": type(exc).__name__, "message": str(exc)})
    finally:
        for child, born in children:
            cleanup_action = None
            if child.poll() is None:
                cleanup_action = closure.terminate_known_process(child.pid, born.isoformat())
                if not cleanup_action:
                    # Only this fixture's retained Popen handle is eligible.
                    child.kill()
                    cleanup_action = "fixture_original_handle_fallback"
            child_return = child.wait(timeout=10)
            check("fixture_owned_cleanup:" + str(child.pid), child_return == 137,
                  {"process_id": child.pid, "actual_returncode": child_return, "cleanup_action": cleanup_action})

    for source in sources:
        current = digest(ROOT / source["path"])
        check("source_unchanged_during_fixture:" + source["path"], current == source["sha256"],
              {"current_sha256": current, "frozen_sha256": source["sha256"]})
    failed = [row for row in checks if not row["passed"]]
    report = {"run_id": args.run_id, "source_model": "self_owned_Python_observer_failure_and_native_stop_contract",
              "execution_status": "failed" if failed else "passed", "physical_acceptance_status": "not_applicable",
              "solver_started": False, "Wolfram_started": False, "Ansys_started": False,
              "source_files": sources, "check_count": len(checks), "failed_check_count": len(failed), "checks": checks,
              "owned_fixture_processes": evidence, "scope": "Two self-owned Python sleep subprocesses; actual source monitor and same-handle native stop; OS PID absence checks",
              "cleanup_root_creation_scope": "Root cleanup entry uses the original retained Popen handle; creation is independently saved in process_ownership and resource_summary and PID matches monitor_cleanup",
              "timestamp_UTC": datetime.now(timezone.utc).isoformat()}
    write(folder / "test_report.json", report)
    write(folder / "artifact_hashes.json", {"files": [{"path": path.relative_to(folder).as_posix(), "sha256": digest(path)}
          for path in folder.rglob("*") if path.is_file() and path.name != "artifact_hashes.json"]})
    print(json.dumps({"run_id": args.run_id, "check_count": len(checks), "failed_check_count": len(failed),
                      "owned_fixture_PIDs": [child.pid for child, _ in children]}))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
