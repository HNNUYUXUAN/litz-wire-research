"""Read-only baseline and local archive inventory; never executes model code.

Only a fresh outputs/<run_id> directory is written. Original results, canonical
index, notebooks, documents and problem statements are read-only. This inventory
is a point-in-time audit, not an off-device backup or physical acceptance test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file() and (p / "configs/reference_parameters.json").is_file())
BASELINE_ROUTES = ("analytic", "fem2", "coax", "coax640", "circuits", "copper", "geometry")
MODEL_SOURCES = {
    "analytic": ["src/stages/analytic.wl", "src/NotebookPhysics.wl", "src/Q1Analytical.wl",
                 "configs/reference_parameters.json", "configs/reference_values.json", "tests/Q1Analytical.wlt"],
    "fem2": ["src/stages/fem2.wl", "src/NotebookPhysics.wl"],
    "coax": ["src/stages/coax.wl", "src/CoaxFEM.wl", "src/NotebookPhysics.wl"],
    "coax640": ["src/stages/coax640.wl", "src/CoaxFEM.wl", "src/NotebookPhysics.wl"],
    "circuits": ["src/stages/circuits.wl", "src/NotebookPhysics.wl"],
    "copper": ["src/stages/copper.wl", "src/NotebookPhysics.wl"],
    "geometry": ["src/stages/geometry.wl", "src/NotebookPhysics.wl"],
    "peec": ["src/stages/peec.wl", "src/PEEC.wl", "src/NotebookPhysics.wl"],
}
SCOPE_NOTES = {
    "analytic": "50-digit Bessel calibration; Q1 D=2 mm remains a calibration with the stated current-density conflict.",
    "fem2": "Independent 2D single-cylinder diffusion FEM within saved mesh/current/power tests.",
    "coax": "Common-terminal-voltage, total-current 2D coax FEM; no imposed equal strand currents.",
    "coax640": "640-strand 2D coax FEM with actual mesh copper area; does not establish finite transposition performance.",
    "circuits": "Controlled field/circuit common-port algebra demonstration; not an independent finite-structure field solve.",
    "copper": "Equal-copper Bessel solid and isolated-strand internal-impedance reduced predictions; no final topology ranking.",
    "geometry": "Original sampled centrelines and synthetic additive DTM demonstration; no field performance ranking.",
    "peec": "Historic longitudinal PEEC model changed; current-source campaign and regression evidence assessed separately.",
}
EXCLUDE_DIRS = {".git", "node_modules", ".next", "__pycache__", ".ipynb_checkpoints", ".venv", "venv", ".cache"}
SECRET_SUFFIXES = {".key", ".pem", ".pfx", ".p12"}
REQUIRED = ("results.json", "results.wxf", "checkpoint.wxf", "parameters.json", "environment.json",
            "run_manifest.json", "test_report.json", "run_log.txt", "model_assumptions.md", "process_status.json")


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def relative_source(value):
    value = str(value).replace("\\", "/")
    p = Path(value)
    if p.is_absolute() or ".." in p.parts or re.match(r"^[A-Za-z]:", value):
        raise ValueError("source path escapes project root")
    return value


def excluded_file(p):
    return p.suffix.lower() in SECRET_SUFFIXES or (p.name.startswith(".env") and p.name != ".env.example")


def normal_path(path):
    value = str(path)
    if os.name == "nt" and value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif os.name == "nt" and value.startswith("\\\\?\\"):
        value = value[4:]
    return Path(value)


def filesystem_path(path):
    value = str(normal_path(path).absolute())
    if os.name == "nt":
        value = "\\\\?\\UNC\\" + value[2:] if value.startswith("\\\\") else "\\\\?\\" + value
    return Path(value)


class Audit:
    def __init__(self, root, bundle):
        self.root, self.bundle = root.resolve(), bundle.resolve()
        self.inventory = {}
        self.errors, self.notes = [], []
        self.skipped = []
        self.json_errors = []

    def pathkey(self, p):
        return normal_path(p).relative_to(self.root).as_posix()

    def file(self, p, role=None):
        """Stream bytes, detect unresolved LFS pointers and concurrent writes."""
        p = normal_path(p)
        key = self.pathkey(p)
        if key in self.inventory:
            record = self.inventory[key]
            if role and role not in record["roles"]:
                record["roles"].append(role)
            return record
        record = {"path": key, "roles": [role] if role else []}
        try:
            physical = filesystem_path(p)
            resolved = normal_path(physical.resolve())
            if not resolved.is_relative_to(self.root):
                raise ValueError("external symlink target is outside workspace")
            if excluded_file(p):
                raise ValueError("local credential/configuration file excluded")
            before = physical.stat()
            digest = hashlib.sha256()
            with physical.open("rb") as stream:
                prefix = stream.read(200)
                digest.update(prefix)
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            after = physical.stat()
            stable = (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
            record.update(bytes=after.st_size, sha256=digest.hexdigest(),
                          mtime_ns=after.st_mtime_ns, stable_during_hash=stable,
                          lfs_pointer=prefix.startswith(b"version https://git-lfs.github.com/spec/v1"),
                          inventory_status="hashed" if stable else "changed_during_hash")
        except (OSError, ValueError) as exc:
            record.update(inventory_status="unavailable", reason=str(exc))
        self.inventory[key] = record
        return record

    def read_json(self, p, optional=True):
        if not filesystem_path(p).exists():
            if not optional:
                self.errors.append({"path": self.pathkey(p), "reason": "required JSON missing"})
            return {}
        self.file(p)
        try:
            value = json.loads(filesystem_path(p).read_text(encoding="utf-8-sig"))
            return value
        except (OSError, ValueError) as exc:
            self.json_errors.append({"path": self.pathkey(p), "reason": str(exc)})
            return {}

    def walk(self, directory, role):
        found = []
        if not filesystem_path(directory).exists():
            return found
        def traversal_error(exc):
            self.errors.append({"path":self.pathkey(Path(exc.filename)),
                                "reason":"archive directory traversal failed", "error":str(exc)})
        for base, dirs, files in os.walk(filesystem_path(directory), followlinks=False, onerror=traversal_error):
            kept = []
            for name in sorted(dirs):
                p = normal_path(Path(base) / name)
                physical = filesystem_path(p)
                if name in EXCLUDE_DIRS or normal_path(physical.resolve()) == self.bundle or physical.is_symlink():
                    self.skipped.append({"path": self.pathkey(p), "reason": "environment/cache/symlink/audit-output excluded"})
                else:
                    kept.append(name)
            dirs[:] = kept
            for name in sorted(files):
                p = normal_path(Path(base) / name)
                if excluded_file(p):
                    self.skipped.append({"path": self.pathkey(p), "reason": "local credential/configuration excluded"})
                    continue
                found.append(self.file(p, role)["path"])
        return found

    def snapshots(self, run, model_paths):
        manifest = self.read_json(run / "run_manifest.json")
        rows = []
        declared = {}
        sources = manifest.get("sources", []) if isinstance(manifest, dict) else []
        for item in sources:
            try:
                name = relative_source(item["path"])
            except (ValueError, KeyError, TypeError) as exc:
                rows.append({"path": str(item), "status": "invalid_source_declaration", "reason": str(exc)})
                continue
            snapshot = run / "source_snapshot" / name
            snap = self.file(snapshot, "original_run_source_snapshot")
            current = self.file(self.root / name, "current_project_source")
            expected = item.get("sha256")
            match = snap.get("sha256") == expected and snap.get("stable_during_hash") is True
            row = {"path": name, "declared_sha256": expected, "snapshot_path": self.pathkey(snapshot),
                   "snapshot_sha256": snap.get("sha256"), "snapshot_matches_original_manifest": match,
                   "current_sha256": current.get("sha256"),
                   "current_matches_snapshot": bool(match and current.get("sha256") == expected),
                   "role": "critical_model_input" if name in model_paths else "supporting_run_snapshot"}
            if not match:
                row["status"] = "missing_or_hash_mismatch"
            elif row["current_matches_snapshot"]:
                row["status"] = "unchanged"
            else:
                row["status"] = "current_source_changed"
            rows.append(row)
            declared[name] = row
        critical = []
        for name in model_paths:
            if name in declared:
                critical.append(declared[name])
            else:
                current = self.file(self.root / name, "critical_model_input")
                critical.append({"path": name, "current_sha256": current.get("sha256"),
                                 "status": "not_in_original_manifest", "current_matches_snapshot": None})
        return rows, critical

    def run(self, route, pin):
        run_id = pin.get("selected_run_id", pin.get("run_id"))
        if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
            self.errors.append({"route": route, "reason": "invalid explicit run_id"})
            return {"route": route, "audit_status": "invalid_pin"}
        run = self.root / "outputs" / run_id
        paths = self.walk(run, "selected_baseline_raw" if route != "peec" else "historic_peec_raw")
        records = [self.inventory[p] for p in paths]
        missing = [name for name in REQUIRED if not (run / name).is_file()]
        result = self.read_json(run / "results.json")
        checks = self.read_json(run / "test_report.json")
        tests = checks.get("tests", []) if isinstance(checks, dict) else []
        process = self.read_json(run / "process_status.json")
        metadata = self.read_json(run / "environment.json")
        parameters = self.read_json(run / "parameters.json")
        snapshots, critical = self.snapshots(run, MODEL_SOURCES.get(route, []))
        mismatch = [r for r in snapshots if r.get("snapshot_matches_original_manifest") is not True]
        bad_raw = [r["path"] for r in records if r.get("inventory_status") != "hashed" or r.get("lfs_pointer")]
        required_core = {"results.json", "results.wxf", "parameters.json", "test_report.json", "run_manifest.json"}
        integrity = not (required_core.intersection(missing) or mismatch or bad_raw)
        if not integrity and route in BASELINE_ROUTES:
            self.errors.append({"route": route, "reason": "selected raw/declared snapshot integrity incomplete",
                                "missing": missing, "bad_raw": bad_raw, "snapshot_mismatch_count": len(mismatch)})
        failed = [t for t in tests if isinstance(t, dict) and t.get("execution_status") not in ("passed", "skipped")]
        index_tests = pin.get("checks", [])
        def signature(seq):
            return sorted(json.dumps(t, ensure_ascii=False, sort_keys=True) for t in seq)
        index_checks_match = signature(index_tests) == signature(tests)
        if not index_checks_match:
            self.notes.append({"route": route, "reason": "frozen index check rows differ from original complete test report"})
        known_exit = process.get("process_exit_code") if isinstance(process, dict) else None
        future_export = ["complete numerical results and nested case scalar metrics from preserved WXF",
                         "complex currents as real/imaginary numerical values with SI units and source keys"]
        if route in ("fem2", "coax", "coax640"):
            future_export += ["original mesh coordinates, connectivity, element and material markers",
                              "stored field/profile numerical samples; unavailable objects explicitly not_exportable"]
        if route == "geometry":
            future_export += ["original centreline/arc-length/gap/DTM numerical arrays from strand_geometry.wxf"]
        if known_exit is None:
            future_export.append("historical process exit missing; cannot manufacture successful exit evidence")
        return {
            "route": route, "selected_run_id": run_id, "exact_source_directory": self.pathkey(run),
            "selection_origin": "source_index.json:routes." + route,
            "source_model": result.get("source_model", pin.get("source_model")),
            "execution_status": result.get("execution_status", pin.get("execution_status")),
            "physical_acceptance_status": pin.get("physical_acceptance_status", result.get("physical_acceptance_status", "unknown")),
            "result_physical_acceptance_status": result.get("physical_acceptance_status", "not_recorded"),
            "failure_reason": result.get("failure_reason", pin.get("failure_reason")),
            "scope_note": SCOPE_NOTES.get(route), "solver_executed_by_audit": False,
            "raw_integrity_status": "passed_readonly_hash_and_manifest_check" if integrity else "incomplete",
            "artifact_files": paths, "artifact_count": len(paths), "artifact_bytes": sum(r.get("bytes", 0) for r in records),
            "required_file_presence": {name: (run / name).is_file() for name in REQUIRED},
            "missing_required_files": missing, "raw_hash_or_LFS_issues": bad_raw,
            "input_parameters": parameters,
            "environment_version": metadata.get("WolframVersion", metadata.get("wolfram_version", metadata.get("version", metadata.get("$Version")))),
            "checks": tests, "test_report_status": checks.get("execution_status"),
            "check_count": len(tests), "failed_or_unrecognized_checks": failed,
            "frozen_index_checks_equal_original_report": index_checks_match,
            "original_process_exit_code": known_exit,
            "process_exit_evidence": "known_original_exit" if known_exit is not None else "not_recorded_in_historical_run",
            "source_snapshots": snapshots, "critical_model_sources": critical,
            "critical_sources_all_unchanged": all(r.get("status") == "unchanged" for r in critical),
            "future_export_requirements": future_export,
            "documentation_reuse_assessment": "reuse_original_cached_results_with_saved_scope_and_status" if integrity else "resolve_missing_original_artifacts_first",
        }

    def campaign(self, state):
        rows = []
        # State entries are scheduling evidence, never the canonical route selection.
        tasks = state.get("tasks", {}) if isinstance(state, dict) else {}
        for task, entry in sorted(tasks.items()):
            if not isinstance(entry, dict):
                continue
            run_id = entry.get("run_id")
            if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
                continue
            run = self.root / "outputs" / run_id
            result = self.read_json(run / "results.json")
            tests = self.read_json(run / "test_report.json")
            process = self.read_json(run / "process_status.json")
            selected = task.startswith("peec")
            snapshots, critical = self.snapshots(run, ["src/PEEC.wl", "tests/ClosurePEEC.wlt"] if selected else [])
            sources = entry.get("input_sources", [])
            bindings = []
            for source in sources:
                try:
                    name = relative_source(source["path"])
                except (ValueError, KeyError, TypeError):
                    continue
                expected = source.get("sha256")
                actual = self.file(self.root / name, "campaign_current_source").get("sha256")
                bindings.append({"path": name, "scheduled_sha256": expected, "current_sha256": actual,
                                 "current_matches_scheduled_source": expected == actual})
            statuses = {"scheduled_execution_status": entry.get("execution_status"),
                        "result_execution_status": result.get("execution_status"),
                        "physical_acceptance_status": result.get("physical_acceptance_status", entry.get("physical_acceptance_status", "unknown")),
                        "original_process_exit_code": process.get("process_exit_code", entry.get("process_exit")),
                        "failure_reason": result.get("failure_reason", entry.get("failure_reason"))}
            is_running = any("running" in str(value).lower() for value in statuses.values()) or not (run / "results.json").exists()
            complete_tests = tests.get("tests", []) if isinstance(tests, dict) else tests if isinstance(tests, list) else []
            row = {"task": task, "run_id": run_id, "origin": "closure_state_snapshot.json:tasks." + task,
                   "canonical_pin_changed_by_audit": False, "statuses": statuses,
                   "source_model": result.get("source_model"),
                   "current_source_binding": bindings, "source_snapshots": snapshots,
                   "critical_model_sources": critical, "checks": complete_tests,
                   "source_binding_missing": not bool(snapshots or bindings),
                   "tests_succeeded": result.get("tests_succeeded", sum(t.get("execution_status") == "passed" for t in complete_tests if isinstance(t, dict))),
                   "tests_failed": result.get("tests_failed", sum(t.get("execution_status") == "failed" for t in complete_tests if isinstance(t, dict))),
                   "is_live_or_unfinished": is_running,
                   "archive_finality": "pending_completion_and_rehash" if is_running else "point_in_time_inventory_only"}
            if selected:
                paths = self.walk(run, "current_peec_campaign_originals")
                row["artifact_files"] = paths
                row["missing_original_provenance"] = [n for n in ("run_manifest.json", "run_log.txt") if not (run / n).exists()]
                if not snapshots:
                    row["provenance_note"] = "Original test execution lacks a hashed source snapshot; current source hash and later campaign binding cannot retroactively prove the test source bytes."
            rows.append(row)
        peec_current = self.file(self.root / "src/PEEC.wl", "current_peec_model")
        return {"current_PEEC_sha256": peec_current.get("sha256"),
                "historic_PEEC_is_not_current_model_regression": True,
                "small_regression": next((r for r in rows if r["task"] == "peec_small_tests"), None),
                "replacement_campaign": [r for r in rows if r["task"].startswith("peec") and r["task"] != "peec_small_tests"],
                "other_completed_or_active_closure_tasks": [r for r in rows if not r["task"].startswith("peec")],
                "physics_ranking_rule": "Replacement campaign status and numerical uncertainty must be preserved; test success alone does not establish topology ranking."}

    def git_capture(self):
        common = {"cwd": self.root, "check": False, "stderr": subprocess.PIPE}
        status = subprocess.run(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], stdout=subprocess.PIPE, **common)
        if status.returncode:
            self.errors.append({"reason": "Git status failed", "details": status.stderr.decode("utf-8", "replace")})
            return {}
        (self.bundle / "git_status_porcelain_v1.z").write_bytes(status.stdout)
        pieces = status.stdout.decode("utf-8", "replace").split("\0")
        changes, i = [], 0
        while i < len(pieces):
            item = pieces[i]
            i += 1
            if not item:
                continue
            code, name = item[:2], item[3:]
            if name.startswith(self.pathkey(self.bundle) + "/"):
                continue
            row = {"status": code, "path": name, "tracked_diff_in_patch": code != "??"}
            if "R" in code or "C" in code:
                row["original_path"] = pieces[i]
                i += 1
            p = self.root / name
            if p.is_file() and not excluded_file(p):
                row["file_inventory_path"] = self.file(p, "uncommitted_user_or_closure_artifact")["path"]
            elif p.exists() and excluded_file(p):
                row["content_excluded_reason"] = "local credentials/configuration"
            else:
                row["working_tree_file_absent"] = True
            changes.append(row)
        pathspec = [".", ":(exclude)**/.env", ":(exclude)**/.env.*", ":(exclude)**/*.key",
                    ":(exclude)**/*.pem", ":(exclude)**/*.pfx", ":(exclude)**/*.p12"]
        with (self.bundle / "tracked_changes_from_HEAD.patch").open("wb") as patch:
            diff = subprocess.run(["git", "diff", "--binary", "HEAD", "--", *pathspec], stdout=patch, **common)
        rev = subprocess.run(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE, **common)
        return {"HEAD": rev.stdout.decode().strip(), "status_exit_code": status.returncode,
                "tracked_diff_exit_code": diff.returncode, "changes": changes,
                "patch_path": "tracked_changes_from_HEAD.patch",
                "patch_sha256": sha_bytes((self.bundle / "tracked_changes_from_HEAD.patch").read_bytes()),
                "untracked_contents_are_in_inventory_not_git_patch": True,
                "git_index_and_working_tree_modified_by_audit": False}

    def archive_runs(self):
        rows = []
        for run in sorted((self.root / "outputs").iterdir()):
            if not run.is_dir() or run.resolve() == self.bundle:
                continue
            result = self.read_json(run / "results.json")
            test = self.read_json(run / "test_report.json")
            process = self.read_json(run / "process_status.json")
            result = result if isinstance(result, dict) else {}
            test = test if isinstance(test, dict) else {}
            process = process if isinstance(process, dict) else {}
            statuses = [result.get("execution_status"), test.get("execution_status")]
            running = any("running" in str(v).lower() for v in statuses)
            incomplete = (run / "run_manifest.json").exists() and not (run / "results.json").exists()
            live = running or incomplete
            rows.append({"run_id": run.name, "result_execution_status": result.get("execution_status"),
                         "test_report_status": test.get("execution_status"),
                         "original_process_exit_code": process.get("process_exit_code"),
                         "physical_acceptance_status": result.get("physical_acceptance_status", "not_recorded"),
                         "is_live_or_unfinished": live,
                         "archive_finality": "pending_completion_and_rehash" if live else "point_in_time_inventory_only",
                         "interpretation": "Absent results/status are not successful computation evidence."})
        return rows


def audit(root, run_id, index):
    started = utc()
    clock = time.perf_counter()
    root = root.resolve()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("run_id must be an explicit safe identifier")
    bundle = root / "outputs" / run_id
    bundle.mkdir(parents=False, exist_ok=False)
    a = Audit(root, bundle)
    raw = index.read_bytes()
    frozen = json.loads(raw.decode("utf-8-sig"))
    (bundle / "source_index.json").write_bytes(raw)
    index_sha = sha_bytes(raw)
    routes = frozen.get("routes", {})
    state_path = root / "outputs/prewrite_closure_state.json"
    state_raw = state_path.read_bytes() if state_path.exists() else b"{}"
    (bundle / "closure_state_snapshot.json").write_bytes(state_raw)
    state = json.loads(state_raw.decode("utf-8-sig"))
    baseline = []
    for route in (*BASELINE_ROUTES, "peec"):
        print("AUDIT selected " + route, flush=True)
        if route not in routes:
            a.errors.append({"route": route, "reason": "explicit baseline route missing"})
        else:
            baseline.append(a.run(route, routes[route]))
    campaign = a.campaign(state)
    print("AUDIT Git and uncommitted artifacts", flush=True)
    git = a.git_capture()
    archive_roots = ["originals", "problem", "docs", "notebooks", "web", "src", "configs", "tests", "references", "provenance", "outputs"]
    inventory_groups = {}
    for group in archive_roots:
        print("AUDIT archive inventory " + group, flush=True)
        paths = a.walk(root / group, "project_archive_" + group)
        inventory_groups[group] = {"file_count": len(paths), "bytes": sum(a.inventory[p].get("bytes", 0) for p in paths), "paths": paths}
    # Root-level project descriptors and uncommitted files are equally necessary.
    for p in root.iterdir():
        if p.is_file() and not excluded_file(p):
            a.file(p, "root_project_descriptor")
    archive_runs = a.archive_runs()
    write_json(bundle / "archive_runs.json", archive_runs)
    print("AUDIT final frozen-source and archive checks", flush=True)
    current_index_sha = sha_bytes(index.read_bytes())
    if index_sha != current_index_sha:
        a.notes.append({"reason": "canonical index changed concurrently after frozen snapshot; final selection must be re-frozen"})
    for key, record in a.inventory.items():
        if record.get("inventory_status") != "hashed":
            continue
        try:
            stat = filesystem_path(root / key).stat()
            record["unchanged_at_audit_finish"] = (stat.st_size, stat.st_mtime_ns) == (record["bytes"], record["mtime_ns"])
        except OSError:
            record["unchanged_at_audit_finish"] = False
        if record["unchanged_at_audit_finish"] is False:
            record["inventory_status"] = "changed_after_hash_pending_rehash"
    unstable = [p for p, v in a.inventory.items() if v.get("inventory_status") != "hashed" or v.get("stable_during_hash") is not True]
    lfs = [p for p, v in a.inventory.items() if v.get("lfs_pointer")]
    inventory = {"schema_version": 1, "started_UTC": started, "finished_UTC": utc(),
                 "hash_algorithm": "SHA256", "files": list(a.inventory.values()), "groups": inventory_groups,
                 "excluded": a.skipped, "unstable_or_unavailable_paths": unstable, "LFS_pointer_paths": lfs,
                 "policy": "Read-only original artifacts. No environment/install directories copied. No original file deleted or rewritten."}
    write_json(bundle / "archive_inventory.json", inventory)
    write_json(bundle / "git_status.json", git)
    matrix = {"schema_version": 1, "run_id": run_id, "source_model": "readonly_baseline_source_and_archive_integrity_audit",
              "execution_status": "executed", "physical_acceptance_status": "not_applicable_integrity_audit",
              "solver_executed": False, "source_index_path": a.pathkey(index), "frozen_index_sha256": index_sha,
              "current_index_sha256_at_finish": current_index_sha, "canonical_index_modified_by_audit": False,
              "closure_state_snapshot_sha256": sha_bytes(state_raw), "selected_baselines": baseline, "PEEC_replacement": campaign,
              "archive_inventory_file": "archive_inventory.json", "git_capture_file": "git_status.json",
              "archive_runs_file": "archive_runs.json", "live_or_unfinished_run_ids": [r["run_id"] for r in archive_runs if r["is_live_or_unfinished"]],
              "errors": a.errors, "notes": a.notes, "unparseable_source_JSON": a.json_errors,
              "required_after_science_completion": [
                  "Explicitly pin accepted closure routes and their original JSON/CSV/WXF sources; retain failed attempts.",
                  "Freeze final index, campaign sources, raw checkpoints, source snapshots and numerical data before reducing resources.",
                  "Run preservation/export verifier against frozen SHA256 values; non-numerical objects require explicit omission reasons.",
                  "Preserve untracked files separately; Git tracked patch does not contain untracked artifacts or ignored outputs.",
                  "After campaigns and renderers exit, rehash changed/live files and test backup copies off-device; this audit is not a backup.",
                  "On the actual lower-resource device, verify cached-only Notebook/HTML/CSV reading and chart rebuild; acceptance remains pending."],
              "low32_real_device_acceptance": "pending_actual_device_change",
              "no_posthoc_success_exit_or_source_binding_created": True}
    write_json(bundle / "audit_matrix.json", matrix)
    counts = {"baseline_routes": len(baseline), "inventory_files": len(a.inventory),
              "inventory_bytes": sum(v.get("bytes", 0) for v in a.inventory.values()),
              "errors": len(a.errors), "unstable_or_unavailable_files": len(unstable), "LFS_pointers": len(lfs),
              "all_baseline_raw_integrity_passed": all(r.get("raw_integrity_status") == "passed_readonly_hash_and_manifest_check" for r in baseline),
              "baseline_critical_source_changes": {r["route"]: [s["path"] for s in r["critical_model_sources"] if s["status"] != "unchanged"] for r in baseline},
              "baseline_missing_process_exit": [r["route"] for r in baseline if r["original_process_exit_code"] is None]}
    checks = [
        {"id": "selected_baseline_raw_and_manifest_integrity", "passed": counts["all_baseline_raw_integrity_passed"]},
        {"id": "frozen_index_hash_matches_original_snapshot", "passed": sha_bytes((bundle / "source_index.json").read_bytes()) == index_sha},
        {"id": "all_selected_routes_explicitly_pinned", "passed": len(baseline) == len(BASELINE_ROUTES) + 1},
        {"id": "canonical_index_unchanged_during_audit", "passed": current_index_sha == index_sha},
        {"id": "Git_tracked_patch_captured", "passed": git.get("tracked_diff_exit_code") == 0},
    ]
    write_json(bundle / "test_report.json", {"run_id": run_id, "source_model": "readonly_file_integrity",
                                              "execution_status": "passed" if all(c["passed"] for c in checks) else "incomplete", "tests": checks})
    write_json(bundle / "audit_completion.json", {"run_id": run_id, "started_UTC": started, "finished_UTC": utc(),
                 "elapsed_seconds": time.perf_counter() - clock, "solver_executed": False, "counts": counts,
                 "generated_files": [{"path": p.name, "bytes": p.stat().st_size, "sha256": sha_bytes(p.read_bytes())}
                                     for p in sorted(bundle.iterdir()) if p.is_file()],
                 "process_exit_evidence": "caller_must_record_actual_process_exit",
                 "backup_verified": False, "low32_real_device_acceptance": "pending_actual_device_change"})
    print(json.dumps({"bundle": str(bundle), "counts": counts}, ensure_ascii=False), flush=True)
    return 1 if a.errors else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--index", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    index = (args.index or root / "docs/总控/当前运行索引.json").resolve()
    return audit(root, args.run_id, index)


if __name__ == "__main__":
    sys.exit(main())
