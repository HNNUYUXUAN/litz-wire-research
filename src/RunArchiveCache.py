#!/usr/bin/env python3
"""Build one fresh static Notebook cache using the existing bounded monitor."""
import argparse
import os
from pathlib import Path
import shutil
import sys

from PreManuscriptClosure import ROOT, GIB, digest, now, read, run_custom_monitored, write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    if (bundle / "archive_notebooks.json").exists():
        raise ValueError("preserve existing build; select a fresh cache")
    closure = read(bundle / "closure_manifest.json")
    if set(closure["routes"]) != set(read(bundle / "source_index.json")["routes"]):
        raise ValueError("incomplete frozen route cache")
    step = bundle / "processes" / "notebooks"
    step.mkdir(parents=True, exist_ok=False)
    sources = []
    for name in ("RunArchiveCache.py", "BuildArchiveNotebooks.wls", "ArchiveNotebookFormatting.wl", "PreManuscriptClosure.py"):
        source = ROOT / "src" / name
        target = step / "source_snapshot" / "src" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        sources.append({"path": source.relative_to(ROOT).as_posix(), "sha256": digest(source)})
    write(step / "run_manifest.json", {"snapshot_time": "before_this_Notebook_build", "sources": sources, "source_index_sha256": digest(bundle / "source_index.json"), "closure_manifest_sha256": digest(bundle / "closure_manifest.json"), "unit_clarifications_sha256": digest(bundle / "unit_clarifications.json"), "solver_executed": False})
    env = dict(os.environ, LITZ_CLOSURE_EXPORT_DIR=str(bundle), LITZ_CLOSURE_INDEX=str(bundle / "source_index.json"), LITZ_CLOSURE_CPU_THREADS="8", OMP_NUM_THREADS="8", MKL_NUM_THREADS="8", OPENBLAS_NUM_THREADS="8")
    command = [shutil.which("wolframscript") or "wolframscript", "-file", str(ROOT / "src" / "BuildArchiveNotebooks.wls")]
    result = run_custom_monitored(command, step, env, 24*GIB)
    changed = [row["path"] for row in sources if digest(ROOT / row["path"]) != row["sha256"]]
    code = result.returncode if not changed else 2
    if changed:
        write(step / "source_changed_during_execution.json", {"paths": changed})
    summary = read(step / "resource_summary.json", {})
    write(bundle / "export_process_status.json", {"processes": [{"stage": "BuildArchiveNotebooks.wls", "route": None, "process_exit_code": result.returncode, "solver_executed": False, "resource_summary": "processes/notebooks/resource_summary.json", "peak_sampled_process_tree_working_bytes": summary.get("peak_sampled_process_tree_working_bytes")}], "source_conversion_evidence": "source_export_evidence/export_process_status.json", "source_conversion_scope": "all 63 routes were converted at the origin bundle; this run builds cached Notebooks only"})
    write(bundle / "process_status.json", {"process_exit_code": code, "native_child_exit_code": result.returncode, "source_changed_during_execution": changed, "exit_origin": "actual child returncode; source mutation failure separately identified", "finished_UTC": now(), "command": command})
    print({"process_exit_code": code, "bundle": str(bundle), "solver_executed": False})
    return code


if __name__ == "__main__":
    sys.exit(main())
