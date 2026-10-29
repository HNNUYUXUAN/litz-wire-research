"""Finite computational closure with explicit source selection and resource profiles.

No cloud configuration or package installation is performed. Computation can run
on the current high profile; low-profile acceptance requires a real low host.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file() and (p / "configs/reference_parameters.json").is_file())
GIB = 1024**3
INDEX = ROOT / "docs" / "总控" / "当前运行索引.json"
STATE = ROOT / "outputs" / "prewrite_closure_state.json"
DEFAULT_CONFIG = ROOT / "configs" / "prewrite_closure.json"
RUN_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def read(path: Path, fallback=None):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return fallback


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def digest(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024**2), b""):
            h.update(block)
    return h.hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def new_id(task="batch"):
    return "closure_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + "_" + re.sub(r"[^A-Za-z0-9_-]", "_", task)


def powershell():
    candidate = shutil.which("pwsh") or shutil.which("powershell")
    if not candidate:
        raise RuntimeError("PowerShell is unavailable")
    return candidate


def hardware():
    script = (
        "$c=Get-CimInstance Win32_ComputerSystem;"
        "$o=Get-CimInstance Win32_OperatingSystem;"
        "@{RAM_bytes=[int64]$c.TotalPhysicalMemory;logical_processors=[int]$c.NumberOfLogicalProcessors;"
        "free_RAM_bytes=[int64]$o.FreePhysicalMemory*1024;os=$o.Caption}|ConvertTo-Json -Compress"
    )
    script = "[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);" + script
    result = subprocess.run([powershell(), "-NoProfile", "-Command", script], capture_output=True, text=True, encoding="utf-8", check=True)
    row = json.loads(result.stdout)
    row["gpu"] = None
    smi = shutil.which("nvidia-smi")
    if smi:
        probe = subprocess.run([smi, "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"],
                               capture_output=True, text=True, timeout=20)
        if probe.returncode == 0 and probe.stdout.strip():
            pieces = next(csv.reader([probe.stdout.strip().splitlines()[0]]))
            if len(pieces) == 3:
                row["gpu"] = {"name": pieces[0].strip(), "memory_MiB": float(pieces[1]), "free_MiB": float(pieces[2])}
    return row


def selected_runs():
    return {key: value.get("selected_run_id") for key, value in read(INDEX, {}).get("routes", {}).items()}


def source_peak(run_id):
    path = ROOT / "outputs" / str(run_id) / "resource_curve.csv"
    peak = 0
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                try:
                    peak = max(peak, float(row.get("kernel_working_bytes") or row.get("working_set_bytes") or 0))
                except (ValueError, TypeError):
                    pass
    summary = read(ROOT / "outputs" / str(run_id) / "resource_summary.json", {})
    peak = max(peak, float(summary.get("peak_sampled_process_tree_working_bytes") or 0))
    return peak


def observe_processes():
    script = ("$os=Get-CimInstance Win32_OperatingSystem; $rows=@(Get-CimInstance Win32_Process | ForEach-Object {"
              "$p=Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue; if($p -and [Math]::Abs(($p.StartTime.ToUniversalTime()-$_.CreationDate.ToUniversalTime()).TotalSeconds) -lt .01){"
              "@{process_id=[int]$_.ProcessId;parent_id=[int]$_.ParentProcessId;name=$_.Name;"
              "created_UTC=$_.CreationDate.ToUniversalTime().ToString('o');working_bytes=[int64]$p.WorkingSet64;CPU_seconds=$p.CPU}}});"
              "@{processes=$rows;free_RAM_bytes=[int64]$os.FreePhysicalMemory*1024}|ConvertTo-Json -Depth 5 -Compress")
    script = "[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);" + script
    result = subprocess.run([powershell(), "-NoProfile", "-Command", script], capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(result.stdout)


def native_handle_creation(handle):
    import ctypes
    from ctypes import wintypes
    get_times = ctypes.WinDLL("kernel32", use_last_error=True).GetProcessTimes
    get_times.argtypes = [wintypes.HANDLE, *([ctypes.POINTER(wintypes.FILETIME)]*4)]
    get_times.restype = wintypes.BOOL
    values = [wintypes.FILETIME() for _ in range(4)]
    if not get_times(handle, *(ctypes.byref(value) for value in values)):
        raise ctypes.WinError(ctypes.get_last_error())
    ticks = (values[0].dwHighDateTime << 32) | values[0].dwLowDateTime
    return datetime.fromtimestamp((ticks-116444736000000000)/10000000, timezone.utc)


def native_child_creation(child):
    return native_handle_creation(child._handle)


def terminate_known_process(pid, created_UTC):
    import ctypes
    from ctypes import wintypes
    library = ctypes.WinDLL("kernel32", use_last_error=True)
    library.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    library.OpenProcess.restype = wintypes.HANDLE
    library.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    library.TerminateProcess.restype = wintypes.BOOL
    library.CloseHandle.argtypes = [wintypes.HANDLE]
    library.CloseHandle.restype = wintypes.BOOL
    handle = library.OpenProcess(0x1001, False, int(pid))
    if not handle:
        return False
    try:
        expected = datetime.fromisoformat(created_UTC.replace("Z", "+00:00"))
        if abs((native_handle_creation(handle)-expected).total_seconds()) > .00001:
            return False
        return bool(library.TerminateProcess(handle, 137))
    finally:
        library.CloseHandle(handle)


def run_custom_monitored(command, folder, process_env, budget):
    """Always preserve ownership and clean this command if observation fails."""
    context = {}
    failure = None
    result = None
    cleanup = []
    try:
        result = _run_custom_monitored(command, folder, process_env, budget, context)
    except BaseException as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        child = context.get("child")
        for row in context.get("owned", {}).values():
            if child is not None and row["process_id"] == child.pid:
                continue
            try:
                stopped = terminate_known_process(row["process_id"], row["created_UTC"])
                cleanup.append({"process_id": row["process_id"], "created_UTC": row["created_UTC"], "terminated_matching_handle": stopped})
            except OSError as exc:
                cleanup.append({"process_id": row["process_id"], "cleanup_error": str(exc)})
        if child is not None and child.poll() is None:
            import ctypes
            from ctypes import wintypes
            terminate = ctypes.WinDLL("kernel32", use_last_error=True).TerminateProcess
            terminate.argtypes = [wintypes.HANDLE, wintypes.UINT]
            terminate.restype = wintypes.BOOL
            stopped = bool(terminate(child._handle, 137))
            cleanup.append({"process_id": child.pid, "terminated_original_Popen_handle": stopped})
            child.wait(timeout=10)
        write(folder / "monitor_cleanup.json", {"checked_at_UTC": now(), "failure": failure, "cleanup": cleanup,
              "root_process_id": child.pid if child else None, "observed_child_exit_code": child.returncode if child else None,
              "ownership_scope": "only original Popen handle and recorded PID/creation identities"})
    if failure:
        child = context.get("child")
        write(folder / "process_status.json", {"process_exit_code": child.returncode if child else None,
              "monitor_exit_code": 2, "failure": failure, "finished_UTC": now(), "command": command,
              "exit_origin": "actual child returncode; monitor exception reported separately"})
        write(folder / "resource_summary.json", {"run_id": folder.name, "resource_stop_reason": "monitor_exception",
              "peak_sampled_process_tree_working_bytes": None, "CPU_seconds": None,
              "native_root_creation_UTC": context.get("root_creation"),
              "owned_processes": [{k: row[k] for k in ("process_id", "name", "created_UTC")} for row in context.get("history", [])],
              "process_exit_code": child.returncode if child else None, "monitor_exit_code": 2,
              "resource_scope": "monitor failed; complete resource curve unavailable"})
        return subprocess.CompletedProcess(command, 2)
    return result


def _run_custom_monitored(command, folder, process_env, budget, context):
    """Stdlib-only child monitoring for conversion and source-hash verification."""
    owned, history, cpu, rows = {}, [], {}, []
    started = time.monotonic()
    stop = None
    low_samples = 0
    with (folder / "run_log.txt").open("w", encoding="utf-8") as log:
        child = subprocess.Popen(command, cwd=ROOT, env=process_env, stdout=log, stderr=subprocess.STDOUT)
        context.update(child=child, owned=owned, history=history)
        root_creation = native_child_creation(child)
        context["root_creation"] = root_creation.isoformat()
        write(folder / "process_ownership.json", {"process_id": child.pid, "created_UTC": root_creation.isoformat(),
              "ownership_evidence": "original retained Popen process handle", "written_at_UTC": now()})
        while True:
            observation = observe_processes()
            active = {int(row["process_id"]): row for row in observation["processes"]}
            if child.pid in active and child.pid not in owned:
                row = active[child.pid]
                born = datetime.fromisoformat(row["created_UTC"].replace("Z", "+00:00"))
                if abs((born-root_creation).total_seconds()) < .01:
                    owned[child.pid] = row
                    history.append(row)
            changed = True
            while changed:
                changed = False
                for pid, row in active.items():
                    parent = owned.get(int(row["parent_id"]))
                    current_parent = active.get(int(row["parent_id"]))
                    valid_parent = parent and current_parent and parent["created_UTC"] == current_parent["created_UTC"]
                    if valid_parent:
                        born = datetime.fromisoformat(row["created_UTC"].replace("Z", "+00:00"))
                        parent_born = datetime.fromisoformat(current_parent["created_UTC"].replace("Z", "+00:00"))
                        valid_parent = born >= parent_born
                    if valid_parent and (pid not in owned or owned[pid]["created_UTC"] != row["created_UTC"]):
                        owned[pid] = row
                        history.append(row)
                        changed = True
            members = [active[pid] for pid, row in owned.items() if pid in active and active[pid]["created_UTC"] == row["created_UTC"]]
            memory = sum(int(row["working_bytes"]) for row in members)
            for row in members:
                cpu[(row["process_id"], row["created_UTC"])] = row.get("CPU_seconds") or 0
            elapsed = time.monotonic()-started
            rows.append({"timestamp": now(), "kernel_working_bytes": memory, "cpu_seconds": sum(cpu.values()),
                         "system_free_bytes": observation["free_RAM_bytes"], "owned_process_ids": ",".join(str(row["process_id"]) for row in members),
                         "elapsed_seconds": elapsed})
            with (folder / "resource_curve.csv").open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
            low_samples = low_samples+1 if memory > budget or observation["free_RAM_bytes"] < 8*GIB else 0
            if elapsed > 3600 or low_samples >= 3:
                stop = "one_hour_or_RAM_system_reserve_watchdog"
                write(folder / "resource_stop.json", {"reason": stop, "last_sample": rows[-1], "working_budget_bytes": budget})
                # PID and exact creation time are verified immediately before stopping.
                for row in members:
                    terminate_known_process(row["process_id"], row["created_UTC"])
            if child.poll() is not None:
                break
            time.sleep(3)
        exit_code = child.wait()
    write(folder / "process_status.json", {"process_exit_code": exit_code, "finished_UTC": now(),
                                           "exit_origin": "actual completed subprocess returncode", "command": command})
    write(folder / "resource_summary.json", {"run_id": folder.name, "peak_sampled_process_tree_working_bytes": max(row["kernel_working_bytes"] for row in rows),
              "CPU_seconds": sum(cpu.values()), "elapsed_seconds": time.monotonic()-started, "process_exit_code": exit_code,
              "sampling_interval_seconds": 3, "sampling_scope": "command root and recorded descendants; monitor process excluded",
              "short_process_observation": "peak may be unobserved if the child exits before the first OS snapshot",
              "native_root_creation_UTC": root_creation.isoformat(),
              "ownership_scope": "root bound to original Popen handle; live parent identity and child birth; stop verifies and terminates the same native handle",
              "owned_processes": [{k: row[k] for k in ("process_id", "name", "created_UTC")} for row in history],
              "resource_stop_reason": stop})
    return subprocess.CompletedProcess(command, exit_code)


def resource_prediction(spec, state=None):
    """Use measured peaks only from comparable, individually bounded cases."""
    state = state if state is not None else read(STATE, {})
    task = spec["task_id"]
    family = re.match(r"peec_m(40|80)_", task)
    comparable = []
    for previous in state.get("runs", []):
        previous_task = previous.get("task_id", "")
        if previous_task == task or (family and previous_task.startswith(family.group(0))):
            comparable.append(previous.get("run_id"))
    if task in ("analytic", "geometry", "fem3_mms", "fem3_cylinder"):
        comparable.append(selected_runs().get(spec["source_route"]))
    measured = max((source_peak(run) for run in comparable if run), default=0)
    model = int(spec["estimated_GiB"] * GIB)
    return {"estimated_working_bytes": int(max(model, 1.3 * measured)),
            "model_estimate_bytes": model, "measured_peak_bytes": measured,
            "measured_headroom_factor": 1.3, "comparable_source_run_ids": [run for run in comparable if run]}


def computational_signature(spec, config_path, interface_revision=1):
    paths = [config_path]
    if "stage" in spec:
        paths.append(ROOT / "src" / "stages" / (spec["stage"] + ".wl"))
        paths.append(ROOT / "src" / "NotebookPhysics.wl")
        if spec["stage"] in ("closure_peec", "closure_gpu", "closure_peec_tests"):
            paths.append(ROOT / "src" / "PEEC.wl")
            if spec["stage"] == "closure_peec_tests":
                paths.append(ROOT / "tests" / "ClosurePEEC.wlt")
            if spec["stage"] == "closure_gpu":
                paths.append(ROOT / "src" / "GPUVolumeFarKernel.wl")
        elif spec["stage"] == "closure_rt0":
            paths += [ROOT / "src" / "VoxelOperator.wl", ROOT / "src" / "VoxelPEEC.wl", ROOT / "src" / "VoxelOperatorParallel.wl", ROOT / "src" / "ClosureCSV.wl"]
        elif spec["stage"] == "voxel_operator_tests":
            paths += [ROOT / "src" / "VoxelOperator.wl", ROOT / "src" / "VoxelPEEC.wl", ROOT / "src" / "VoxelOperatorParallel.wl", ROOT / "tests" / "VoxelOperator.wlt"]
        elif spec["stage"] == "closure_rt0_parallel_tests":
            paths += [ROOT / "src" / "VoxelOperator.wl", ROOT / "src" / "VoxelPEEC.wl", ROOT / "src" / "VoxelOperatorParallel.wl", ROOT / "tests" / "VoxelOperatorParallel.wlt"]
        elif spec["stage"] == "closure_frozen_verify":
            paths.append(ROOT / "src" / "VerifyFrozenPhysics.wls")
        elif spec["stage"] == "closure_rt0_collect":
            paths.append(ROOT / "src" / "ClosureCSV.wl")
    elif "ansys_task" in spec:
        paths += [ROOT / "src" / name for name in ("RunClosureAnsys.py", "ansys_native3d.py", "ansys_validate.py")]
    else:
        if spec.get("custom") == "rt0_mesh_export":
            paths.append(ROOT / "src" / "ExportFrozenGridMesh.py")
        elif spec.get("custom") == "frozen_physics_collect":
            paths.append(ROOT / "src" / "CollectFrozenPhysicsValidation.py")
        else:
            paths += [ROOT / "src" / "RunClosureSmallTests.wls", ROOT / "src" / "PEEC.wl", ROOT / "tests" / "ClosurePEEC.wlt"]
    sources = [{"path": str(p.relative_to(ROOT)), "sha256": digest(p) if p.is_file() else "missing"} for p in paths]
    value = {"task_id": spec["task_id"], "interface_revision": interface_revision if "ansys_task" in spec else None,
             "kernel_assembly_workers": spec.get("kernel_assembly_workers"), "data_reference_run_ids": spec.get("data_reference_run_ids"),
             "data_reference_selection": spec.get("data_reference_selection"), "sources": sources}
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest(), sources


def prerequisite_path(value):
    first = value.split(",")[0]
    if RUN_RE.fullmatch(first):
        return ROOT / "outputs" / first / "results.json"
    return Path(first).resolve()


def ansys_python(explicit=None):
    candidate = explicit or os.environ.get("LITZ_ANSYS_PYTHON")
    if not candidate or not Path(candidate).is_file():
        raise RuntimeError("Set --ansys-python or LITZ_ANSYS_PYTHON to the existing PyAEDT environment")
    probe = subprocess.run([candidate, "-c", "import ansys.aedt.core"], capture_output=True, text=True, timeout=30)
    if probe.returncode:
        raise RuntimeError("The selected existing Python environment cannot import PyAEDT")
    return candidate


def task_spec(task):
    fixed = {
        "analytic": {"stage": "analytic", "source_route": "analytic", "estimated_GiB": 1},
        "geometry": {"stage": "closure_geometry", "source_route": "geometry", "estimated_GiB": 2},
        "fem3_mms": {"stage": "fem3_mms", "source_route": "fem3_mms", "estimated_GiB": 8},
        "fem3_diagnostics": {"stage": "closure_fem3_diagnostics", "source_route": "fem3_cylinder", "estimated_GiB": 4},
        "fem3_cylinder": {"stage": "fem3_cylinder", "source_route": "fem3_cylinder", "estimated_GiB": 20},
        "voxel_operator_tests": {"stage": "voxel_operator_tests", "source_route": "voxel_operator_tests", "estimated_GiB": 2},
        "peec_small_tests": {"stage": "closure_peec_tests", "source_route": "peec", "estimated_GiB": 1},
        "gpu_m40": {"stage": "closure_gpu", "source_route": "gpu_physics", "estimated_GiB": 4, "needs_gpu": True},
        "gpu_m80": {"stage": "closure_gpu", "source_route": "gpu_scale", "estimated_GiB": 6, "needs_gpu": True},
        "gpu_recovery": {"stage": "closure_gpu_recovery", "source_route": "gpu_scale", "estimated_GiB": 1},
        "closure_rt0_parallel_tests": {"stage": "closure_rt0_parallel_tests", "source_route": "voxel_operator_tests", "estimated_GiB": 2},
        "rt0_mesh_export": {"custom": "rt0_mesh_export", "source_route": "voxel_operator_quadrature", "estimated_GiB": 1},
        "frozen_physics_verify": {"stage": "closure_frozen_verify", "source_route": "peec", "estimated_GiB": 8},
        "frozen_physics_collect": {"custom": "frozen_physics_collect", "source_route": "peec", "estimated_GiB": 1},
        "rt0_campaign_collect": {"stage": "closure_rt0_collect", "source_route": "voxel_operator_quadrature", "estimated_GiB": 1},
    }
    if task in fixed:
        return {"task_id": task, "case_id": task, "attempt_limit": 1, **fixed[task]}
    if re.fullmatch(r"peec_m(40|80)_l(016|032|064|128)_q(4|6|8)_s(10p8|12p10)", task):
        return {"task_id": task, "case_id": task, "stage": "closure_peec", "source_route": "peec",
                "estimated_GiB": 1 if "_m40_" in task else 4, "attempt_limit": 1}
    if re.fullmatch(r"rt0_n(16|20|24|32)_q(14|18)", task):
        n = int(re.search(r"_n(\d+)", task).group(1))
        return {"task_id": task, "case_id": task, "stage": "closure_rt0", "source_route": "voxel_operator_quadrature",
                "estimated_GiB": {16: 4, 20: 6, 24: 8, 32: 12}[n], "attempt_limit": 1}
    if re.fullmatch(r"ansys_(2d_mesh|2d_return|2d_outer|native_probe|native_coarse|native_suite)_(q1|seven)", task):
        mode, case = task[len("ansys_"):].rsplit("_", 1)
        return {"task_id": task, "case_id": case, "ansys_task": mode, "source_route": "ansys_port" if mode.startswith("2d") else "ansys_import",
                "estimated_GiB": 16, "attempt_limit": 2}
    raise ValueError("Unknown closure task: " + str(task))


def inventory(config):
    tasks = [task_spec(t) for t in ("analytic", "geometry", "peec_small_tests", "fem3_diagnostics", "fem3_mms",
                                  "fem3_cylinder", "voxel_operator_tests", "gpu_m40", "gpu_m80", "gpu_recovery", "closure_rt0_parallel_tests", "rt0_mesh_export", "frozen_physics_verify", "frozen_physics_collect", "rt0_campaign_collect")]
    tasks += [task_spec(f"peec_m40_l{length}_q4_s10p8") for length in ("016", "032", "064", "128")]
    tasks += [task_spec(f"peec_m40_l064_q{q}_s10p8") for q in (6, 8)]
    tasks += [task_spec("peec_m40_l064_q4_s12p10")]
    tasks += [task_spec(f"peec_m80_l{length}_q4_s10p8") for length in ("032", "064", "128")]
    tasks += [task_spec(f"peec_m80_l064_q{q}_s10p8") for q in (6, 8)]
    tasks += [task_spec("peec_m80_l064_q4_s12p10")]
    tasks += [task_spec(f"rt0_n{n}_q{q}") for n in (16, 20, 24, 32) for q in (14, 18)]
    tasks += [task_spec("ansys_" + mode + "_" + case) for mode, case in (
        ("2d_mesh", "seven"), ("2d_return", "seven"), ("2d_outer", "seven"),
        ("native_probe", "q1"), ("native_coarse", "q1"), ("native_suite", "q1"), ("native_suite", "seven"))]
    selected = selected_runs()
    for row in tasks:
        row["source_run_id"] = selected.get(row["source_route"])
        if row["task_id"].startswith("rt0_"):
            row["source_run_id"] = "3d_20261005_voxel_operator_tight"
        # The GPU-scale historical peak includes a stopped larger allocation.
        # It is not an estimate for an individual m80 task.
        row.update(resource_prediction(row))
        row["minimum_profile"] = "high64gpu" if row.get("needs_gpu") or row["estimated_working_bytes"] > 24 * GIB else "low32"
        row["maximum_seconds"] = 3600
        row["required_outputs"] = ["parameters.json", "environment.json", "results.json", "test_report.json", "process_status.json"]
        task = row["task_id"]
        row["dependencies"] = [{"kind": "frozen_baseline_run", "run_id": row["source_run_id"]}]
        if task.startswith("peec_") and task != "peec_small_tests" or task.startswith("gpu_m"):
            row["dependencies"].append({"kind": "task", "task_id": "peec_small_tests"})
        ansys_gate = {
            "ansys_2d_return_seven": "ansys_2d_mesh_seven", "ansys_2d_outer_seven": "ansys_2d_mesh_seven",
            "ansys_native_coarse_q1": "ansys_native_probe_q1", "ansys_native_suite_q1": "ansys_native_coarse_q1",
            "ansys_native_suite_seven": "ansys_native_suite_q1",
        }
        if task in ansys_gate:
            row["dependencies"].append({"kind": "accepted_task", "task_id": ansys_gate[task]})
        row["stop_policy"] = "one-hour case budget, measured RAM/system/VRAM reserve, attempt limit, and prerequisite gate"
        row["conditional"] = row["task_id"].endswith("l128_q4_s10p8") or "_n32_" in row["task_id"] or "_q18" in row["task_id"] or row["task_id"] == "ansys_native_suite_seven"
    return tasks


def check_profile(env, profile, spec, config, strict=False):
    p = config["profiles"][profile]
    reasons = []
    if env["RAM_bytes"] < (p["nominal_RAM_GiB"] - 1) * GIB:
        reasons.append("RAM_below_requested_profile")
    if env["logical_processors"] < p["logical_processors"]:
        reasons.append("CPU_below_requested_profile")
    if strict and profile == "low32" and (env["RAM_bytes"] > 33 * GIB or env["logical_processors"] > 8 or env.get("gpu")):
        reasons.append("actual_low32_host_required_for_acceptance")
    if spec.get("needs_gpu") and (not p["gpu_allowed"] or not env.get("gpu")):
        reasons.append("task_requires_GPU")
    budget = max(0, min(p["maximum_working_GiB"] * GIB, env["free_RAM_bytes"] - p["minimum_free_GiB"] * GIB))
    if spec.get("estimated_working_bytes", 0) > budget:
        reasons.append("predicted_working_set_exceeds_budget")
    return reasons, budget


def snapshot(folder, config_path):
    items = [config_path, INDEX]
    items += sorted((ROOT / "src").rglob("*.wl")) + sorted((ROOT / "src").glob("*.wls"))
    items += sorted((ROOT / "src").glob("*.py")) + sorted((ROOT / "src").glob("*.ps1"))
    items += sorted((ROOT / "tests").glob("*.wlt"))
    rows = []
    for source in items:
        relative = source.relative_to(ROOT)
        dest = folder / "source_snapshot" / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        rows.append({"path": relative.as_posix(), "sha256": digest(source), "size_bytes": source.stat().st_size})
    write(folder / "run_manifest.json", {"snapshot_time": "before_execution", "sources": rows})
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        diff = subprocess.check_output(["git", "diff", "--binary"], cwd=ROOT)
        (folder / "working_tree.patch").write_bytes(diff)
    except (OSError, subprocess.CalledProcessError):
        head = "unknown"
    return head


def register(task, run_id, profile, result):
    # Light conversion and a serial solver can finish at the same moment.
    with state_lock():
        state = read(STATE, {"schema_version": 1, "tasks": {}, "runs": []})
        row = {"task_id": task, "run_id": run_id, "profile": profile, "completed_at_UTC": now(), **result}
        state["tasks"][task] = row
        state["runs"].append(row)
        state["updated_at_UTC"] = now()
        write(STATE, state)


@contextlib.contextmanager
def state_lock():
    import msvcrt
    lock = STATE.with_suffix(".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0"); stream.flush()
        deadline = time.monotonic() + 30
        while True:
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise RuntimeError("Closure state lock timed out")
                time.sleep(.1)
        try:
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def preflight(args, config, config_path):
    run_id = args.run_id or new_id("preflight")
    folder = ROOT / "outputs" / run_id
    folder.mkdir(exist_ok=False)
    env = hardware()
    items = inventory(config)
    for item in items:
        reasons, budget = check_profile(env, args.profile, item, config)
        item["preflight_status"] = "ready" if not reasons else "configuration_or_budget_stop"
        item["preflight_reasons"] = reasons
        item["available_budget_bytes"] = budget
    write(folder / "environment.json", env)
    write(folder / "parameters.json", {"action": "preflight", "profile": args.profile, "config_sha256": digest(config_path)})
    write(folder / "task_inventory.json", {"generated_at_UTC": now(), "index_sha256": digest(INDEX), "tasks": items})
    snapshot(folder, config_path)
    write(folder / "results.json", {"source_model": "closure_environment_and_task_preflight", "execution_status": "executed",
                                  "physical_acceptance_status": "not_applicable", "task_count": len(items),
                                  "low32_acceptance": "pending_actual_host", "run_id": run_id})
    write(folder / "process_status.json", {"process_exit_code": 0, "finished": now()})
    print(json.dumps({"run_id": run_id, "tasks": len(items), "actual_RAM_GiB": env["RAM_bytes"] / GIB,
                      "profile": args.profile, "ready": sum(x["preflight_status"] == "ready" for x in items)}))
    return 0


def run_task(args, config, config_path):
    spec = task_spec(args.task)
    if spec.get("custom") == "frozen_physics_collect":
        selection_path = Path(args.selection_file).resolve() if args.selection_file else None
        if not selection_path or not selection_path.is_file():
            raise ValueError("Frozen numerical collector requires --selection-file")
        spec["data_reference_selection"] = {"path": str(selection_path), "sha256": digest(selection_path)}
    if spec.get("stage") == "closure_rt0":
        spec["kernel_assembly_workers"] = args.kernel_assembly_workers
    if spec.get("custom") == "rt0_mesh_export" or spec.get("stage") in ("closure_frozen_verify", "closure_rt0_collect"):
        spec["data_reference_run_ids"] = args.reference_runs
    spec.update(resource_prediction(spec))
    env = hardware()
    reasons, budget = check_profile(env, args.profile, spec, config)
    run_id = args.run_id or new_id(args.task)
    folder = ROOT / "outputs" / run_id
    if folder.exists():
        raise FileExistsError("Existing run ID is protected: " + run_id)
    state = read(STATE, {"runs": []})
    if args.task in state.get("finalized_tasks", {}):
        raise RuntimeError("Task has a final bounded stop: " + str(state["finalized_tasks"][args.task]))
    signature, input_sources = computational_signature(spec, config_path, args.interface_revision)
    prior = [x for x in state.get("runs", []) if x["task_id"] == args.task and x.get("input_signature") == signature]
    if any(x.get("execution_status") == "executed" for x in prior):
        raise RuntimeError("This identical task already has executed evidence; use its explicit run ID")
    if len(prior) >= spec["attempt_limit"]:
        raise RuntimeError("Attempt budget reached; a diagnosed source or input revision is required")
    if reasons:
        folder.mkdir()
        write(folder / "results.json", {"run_id": run_id, "source_model": "closure_preflight",
                                      "execution_status": "blocked_environment_resource_budget",
                                      "physical_acceptance_status": "not_run", "failure_reason": reasons,
                                      "estimated_working_bytes": spec["estimated_working_bytes"], "budget_bytes": budget})
        write(folder / "environment.json", env)
        write(folder / "process_status.json", {"process_exit_code": 2, "finished": now()})
        register(args.task, run_id, args.profile, {"execution_status": "blocked_environment_resource_budget",
                                                "input_signature": signature, "failure_reason": reasons})
        print(json.dumps({"run_id": run_id, "failure_reason": reasons}))
        return 2
    dispatch = {"run_id": run_id, "task_id": args.task, "requested_at_UTC": now(),
                "input_signature": signature, "input_sources": input_sources,
                "config_sha256": digest(config_path), "actual_host": env, "requested_profile": args.profile,
                "available_working_budget_bytes": budget, "attempt_limit": spec["attempt_limit"],
                "reference_runs": [x for x in (args.reference_runs or "").split(",") if x],
                "snapshot_time": "before_child_execution"}
    dispatch_file = ROOT / "outputs" / "closure_dispatch" / (run_id + ".json")
    if dispatch_file.exists():
        raise FileExistsError("Existing dispatch evidence is protected: " + run_id)
    write(dispatch_file, dispatch)
    process_env = os.environ.copy()
    process_env.update({
        "LITZ_CLOSURE_CONFIG": str(config_path), "LITZ_CLOSURE_CASE_ID": spec["case_id"],
        "LITZ_CLOSURE_REFERENCE_RUNS": args.reference_runs or "",
        "LITZ_CLOSURE_PROFILE": args.profile, "LITZ_CLOSURE_MAX_WORKING_BYTES": str(budget),
        "LITZ_CLOSURE_MIN_SYSTEM_FREE_BYTES": str(8 * GIB), "LITZ_CLOSURE_MIN_FREE_VRAM_MIB": "1024",
        "LITZ_CLOSURE_CPU_THREADS": "16" if args.profile == "high64gpu" else "8",
        "LITZ_CLOSURE_MAX_SECONDS": "3600",
        "LITZ_RT0_KERNEL_ASSEMBLY_WORKERS": str(getattr(args, "kernel_assembly_workers", 1)),
        "LITZ_CLOSURE_REQUESTED_TASK": args.task,
    })
    if "stage" in spec:
        command = [powershell(), "-NoProfile", "-File", str(ROOT / "src" / "RunNotebookStage.ps1"),
                   "-Stage", spec["stage"], "-RunId", run_id]
    elif "ansys_task" in spec:
        command = [ansys_python(args.ansys_python), str(ROOT / "src" / "RunClosureAnsys.py"), "--task", spec["ansys_task"],
                   "--case", spec["case_id"], "--run-id", run_id, "--budget", "high" if args.profile == "high64gpu" else "low",
                   "--interface-revision", str(args.interface_revision)]
        if args.reference_runs:
            command += ["--prerequisite", str(prerequisite_path(args.reference_runs))]
    else:
        folder.mkdir()
        snapshot(folder, config_path)
        if spec.get("custom") == "rt0_mesh_export":
            write(folder / "environment.json", {"actual_host": env, "python_version": sys.version, "solver_executed": False})
            command = [sys.executable, str(ROOT / "src" / "ExportFrozenGridMesh.py"), "--output", str(folder), "--reference-runs", args.reference_runs]
        elif spec.get("custom") == "frozen_physics_collect":
            write(folder / "environment.json", {"actual_host": env, "python_version": sys.version, "solver_executed": False})
            shutil.copy2(selection_path, folder / "numeric_validation_selection.json")
            command = [sys.executable, str(ROOT / "src" / "CollectFrozenPhysicsValidation.py"), "--output", str(folder), "--selection", str(selection_path)]
        else:
            command = [shutil.which("wolframscript") or "wolframscript", "-file", str(ROOT / "src" / "RunClosureSmallTests.wls"), str(folder)]
    if "custom" in spec:
        result = run_custom_monitored(command, folder, process_env, budget)
    else:
        result = subprocess.run(command, cwd=ROOT, env=process_env, check=False)
    if folder.exists():
        shutil.copy2(dispatch_file, folder / "dispatch_manifest.json")
    data = read(folder / "results.json", {})
    proc = read(folder / "process_status.json", {})
    exit_code = proc.get("process_exit_code", result.returncode)
    # Process completion and scientific acceptance remain separate.
    register(args.task, run_id, args.profile, {
        "execution_status": data.get("execution_status", "failed_process_exit" if result.returncode else "unknown"),
        "physical_acceptance_status": data.get("physical_acceptance_status", "passed_full_Ansys_scope" if data.get("full_physical_acceptance") in (True, "passed") else "failed_or_limited_Ansys_scope" if "ansys_task" in spec else "not_verified"),
        "process_exit": exit_code, "input_signature": signature,
        "input_sources": input_sources,
        "failure_reason": data.get("failure_reason"), "source_run_ids": (args.reference_runs or "").split(","),
    })
    print(json.dumps({"task_id": args.task, "run_id": run_id, "process_exit": exit_code,
                      "execution_status": data.get("execution_status", "unknown")}))
    return result.returncode


def export(args, config, config_path):
    env = hardware()
    document_host = bool(getattr(args, "document_host", False))
    reasons, budget = check_profile(env, "low32", {}, config, strict=not document_host)
    if document_host and not 31*GIB <= env["RAM_bytes"] <= 33*GIB:
        reasons.append("user_selected_document_host_requires_32GiB_RAM")
    if args.profile != "low32" or reasons:
        raise RuntimeError("Document/Notebook export waits for the actual low32 configuration")
    run_id = args.run_id or new_id("export")
    folder = ROOT / "outputs" / run_id
    folder.mkdir(exist_ok=False)
    snapshot(folder, config_path)
    write(folder / "environment.json", {"actual_host": env, "requested_execution_budget": "low32",
          "user_selected_document_host": document_host, "CPU_thread_limit": 8,
          "working_budget_bytes": budget, "minimum_free_system_bytes": 8*GIB,
          "GPU_compute_enabled": False, "solver_executed": False,
          "strict_low32_hardware_status": "superseded_by_user_selected_32GiB_16logical_8GiB_GPU_delivery_host" if document_host else "passed"})
    process_env = os.environ.copy()
    process_env.update({"LITZ_CLOSURE_EXPORT_DIR": str(folder), "LITZ_CLOSURE_INDEX": str(INDEX),
        "LITZ_CLOSURE_CPU_THREADS": "8", "LITZ_CLOSURE_PROFILE": "low32",
        "LITZ_CLOSURE_MAX_WORKING_BYTES": str(budget), "LITZ_CLOSURE_MIN_SYSTEM_FREE_BYTES": str(8*GIB),
        "LITZ_CLOSURE_MAX_SECONDS": "3600", "OMP_NUM_THREADS": "8", "MKL_NUM_THREADS": "8",
        "OPENBLAS_NUM_THREADS": "8"})
    processes = []
    stages = [("ExportClosureEvidence.wls", route) for route in read(INDEX)["routes"]]
    stages.append(("BuildArchiveNotebooks.wls", None))
    for name, route in stages:
        process_env["LITZ_CLOSURE_ROUTE"] = route or "all"
        label = route or "notebooks"
        step = folder / "processes" / label
        step.mkdir(parents=True, exist_ok=False)
        step_sources = [ROOT / "src" / name]
        if name == "BuildArchiveNotebooks.wls":
            step_sources.append(ROOT / "src" / "ArchiveNotebookFormatting.wl")
        step_rows = []
        for source in step_sources:
            target = step / "source_snapshot" / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            step_rows.append({"path":source.relative_to(ROOT).as_posix(),"sha256":digest(source)})
        write(step / "run_manifest.json", {"snapshot_time":"before_this_conversion_step", "sources":step_rows})
        command = [shutil.which("wolframscript") or "wolframscript", "-file", str(ROOT / "src" / name)]
        result = run_custom_monitored(command, step, process_env, budget)
        changed = [row["path"] for row in step_rows if digest(ROOT/row["path"]) != row["sha256"]]
        if changed:
            write(step / "source_changed_during_execution.json", {"paths":changed,"scientific_solver_executed":False})
            result = subprocess.CompletedProcess(command, 2)
        summary = read(step / "resource_summary.json", {})
        processes.append({"stage":name,"route":route,"process_exit_code":result.returncode,"solver_executed":False,
             "resource_summary": (step / "resource_summary.json").relative_to(folder).as_posix(),
             "peak_sampled_process_tree_working_bytes": summary.get("peak_sampled_process_tree_working_bytes")})
        write(folder / "export_process_status.json", {"processes":processes})
        if result.returncode:
            write(folder / "process_status.json", {"process_exit_code": result.returncode, "failed_step": name, "route":route,"finished": now()})
            return result.returncode
    write(folder / "process_status.json", {"process_exit_code": 0, "finished": now()})
    print(json.dumps({"run_id": run_id, "bundle": str(folder)}))
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=("preflight", "run", "export", "verify"), default="preflight")
    parser.add_argument("--profile", choices=("low32", "high64gpu"), default="high64gpu")
    parser.add_argument("--task")
    parser.add_argument("--run-id")
    parser.add_argument("--bundle")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--reference-runs", default="")
    parser.add_argument("--selection-file")
    parser.add_argument("--document-host", action="store_true", help="User-selected 32GiB delivery host; CPU8/no GPU compute; does not certify strict low32 hardware")
    parser.add_argument("--ansys-python")
    parser.add_argument("--interface-revision", type=int, choices=(1, 2), default=1)
    parser.add_argument("--kernel-assembly-workers", type=int, choices=(1, 4), default=1)
    args = parser.parse_args()
    if args.run_id and not RUN_RE.fullmatch(args.run_id):
        parser.error("Invalid run ID")
    config_path = Path(args.config).resolve()
    config = read(config_path)
    if not config:
        parser.error("Missing or invalid closure config")
    try:
        if args.action == "preflight":
            return preflight(args, config, config_path)
        if args.action == "run":
            if not args.task:
                parser.error("Run requires --task")
            return run_task(args, config, config_path)
        if args.action == "export":
            return export(args, config, config_path)
        if not args.bundle:
            parser.error("Verify requires --bundle")
        return subprocess.run([sys.executable, str(ROOT / "src" / "VerifyClosureEvidence.py"),
                               "--bundle", args.bundle, "--profile", args.profile], cwd=ROOT, check=False).returncode
    except (RuntimeError, OSError, ValueError) as exc:
        print(json.dumps({"execution_status": "stopped", "failure_reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
