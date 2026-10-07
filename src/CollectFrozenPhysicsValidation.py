"""Collect explicitly selected original-cache validation reports without a solver.

Each selected case is bound to its saved JSON hash and all original source files.
A failed parent batch may supply a passed case only through an explicit, exact
partial-parent declaration. Its failed outcome and unselected failures are kept.
No original run, canonical index, model, Notebook or manuscript is rewritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"[A-Za-z0-9_-]+\Z")
HASH_RE = re.compile(r"[0-9a-f]{64}\Z")
PASSED = "passed_original_numeric_agreement"
LFS_PREFIX = b"version https://git-lfs.github.com/spec/v1"
DIRECT_REL = 2e-14
DIRECT_ABS = 1e-30
MATRIX_ID = "saved_CPU_GPU_full_L_matrix_error_identity"


def safe_id(value, field):
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ValueError(f"Explicit safe {field} required: {value!r}")
    return value


def relative_path(root, value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Source path must be a nonempty workspace-relative POSIX path")
    path = Path(value)
    if path.is_absolute() or any(part in ("..", ".") for part in path.parts) or ":" in value:
        raise ValueError("Invalid relative source path: " + value)
    resolved = (root / path).resolve()
    resolved.relative_to(root.resolve())
    return resolved


def file_record(path, root, role, expected_sha=None, expected_bytes=None):
    path = path.resolve()
    path.relative_to(root.resolve())
    if not path.is_file():
        raise FileNotFoundError(path)
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        prefix = stream.read(256)
        if prefix.startswith(LFS_PREFIX):
            raise ValueError("Unresolved Git LFS pointer: " + str(path))
        digest.update(prefix)
        while block := stream.read(1024 * 1024):
            digest.update(block)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("Source changed during hash: " + str(path))
    sha = digest.hexdigest()
    if expected_sha is not None:
        if not isinstance(expected_sha, str) or not HASH_RE.fullmatch(expected_sha):
            raise ValueError("Invalid expected SHA256: " + str(path))
        if sha != expected_sha:
            raise ValueError("SHA256 mismatch: " + str(path))
    if expected_bytes is not None and (type(expected_bytes) is not int or expected_bytes != after.st_size):
        raise ValueError("Original byte count mismatch: " + str(path))
    return {"path": path.relative_to(root.resolve()).as_posix(), "role": role,
            "sha256": sha, "bytes": after.st_size, "mtime_ns": after.st_mtime_ns}


def read_json(path, root, role, expected_sha=None):
    record = file_record(path, root, role, expected_sha)
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("JSON object required: " + str(path))
    after = path.stat()
    if (record["bytes"], record["mtime_ns"]) != (after.st_size, after.st_mtime_ns):
        raise ValueError("JSON changed during read: " + str(path))
    return value, record


def validate_selection(selection):
    if selection.get("schema_version") != 1:
        raise ValueError("Unsupported selection schema_version")
    required = selection.get("required_raw_run_ids")
    rows = selection.get("selected_reports")
    partial = selection.get("partial_parent_failures", {})
    if not isinstance(required, list) or not required or not isinstance(rows, list) or not rows:
        raise ValueError("Nonempty required_raw_run_ids and selected_reports are required")
    required = [safe_id(run, "required raw_run_id") for run in required]
    if len(required) != len(set(required)):
        raise ValueError("Duplicate required raw run")
    if not isinstance(partial, dict):
        raise ValueError("partial_parent_failures must be an explicit object")
    selected = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Every selected report must be an object")
        raw = safe_id(row.get("raw_run_id"), "raw_run_id")
        parent = safe_id(row.get("verification_run_id"), "verification_run_id")
        case = safe_id(row.get("case_id"), "case_id")
        sha = row.get("case_report_sha256")
        if not isinstance(sha, str) or not HASH_RE.fullmatch(sha):
            raise ValueError("Every selected case needs its explicit case_report_sha256")
        selected.append({"raw_run_id": raw, "verification_run_id": parent,
                         "case_id": case, "case_report_sha256": sha})
    raw_ids = [row["raw_run_id"] for row in selected]
    if len(raw_ids) != len(set(raw_ids)):
        raise ValueError("Duplicate selected raw run; one explicit case per raw run is required")
    if set(raw_ids) != set(required):
        raise ValueError("Selected raw coverage differs from required_raw_run_ids")
    for parent, rule in partial.items():
        safe_id(parent, "partial verification_run_id")
        if parent not in {row["verification_run_id"] for row in selected} or not isinstance(rule, dict):
            raise ValueError("Partial-parent declaration must identify a selected parent")
        if type(rule.get("expected_process_exit_code")) is not int or rule["expected_process_exit_code"] == 0:
            raise ValueError("Partial parent must explicitly preserve a nonzero expected exit")
        ids = rule.get("allowed_failed_check_ids")
        failed_raw = rule.get("expected_failed_raw_run_ids")
        if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)):
            raise ValueError("Partial parent requires explicit unique allowed_failed_check_ids")
        if not isinstance(failed_raw, list) or not failed_raw or len(failed_raw) != len(set(failed_raw)):
            raise ValueError("Partial parent requires explicit unique expected_failed_raw_run_ids")
        for run in failed_raw:
            safe_id(run, "expected failed raw_run_id")
    return required, selected, partial


def check_numeric_records(case):
    checks = case.get("checks")
    if not isinstance(checks, list) or not checks or any(not isinstance(row, dict) for row in checks):
        raise ValueError("Selected case lacks complete checks")
    ids = [row.get("id") for row in checks]
    if any(not isinstance(value, str) or not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("Duplicate or invalid selected case check IDs")
    if any(row.get("execution_status") != "passed" for row in checks):
        raise ValueError("Selected case contains failed/incomplete checks")
    lookup = {row["id"]: row for row in checks}
    if "required_model_source_snapshot_declarations" not in lookup or "phasor_convention" not in lookup:
        raise ValueError("Selected case lacks source snapshot or phasor proof")
    basis = case.get("scope", {}).get("basis", "")
    if "CPU/GPU" in basis:
        required = {"all_GPU_currents_WXF_to_JSON", "every_GPU_current_ReIm", "every_CPU_current_ReIm",
                    "GPU_voltage_ReIm_WXF_to_JSON", "every_original_filament_id", MATRIX_ID}
        kind = "CPU_GPU"
    elif "RT0" in basis:
        required = {"every_face_flux_ReIm_WXF_to_CSV", "every_face_axis_grid_WXF_to_CSV",
                    "every_cell_phi_ReIm_WXF_to_CSV", "every_cell_J_from_original_face_flux_to_CSV",
                    "port_current_ReIm_WXF_to_JSON", "port_voltage_ReIm_WXF_to_JSON", "loss_WXF_to_JSON"}
        kind = "RT0"
    elif "longitudinal" in basis:
        required = {"every_current_ReIm_WXF_to_JSON", "every_current_ReIm_WXF_to_CSV",
                    "port_voltage_ReIm_WXF_to_JSON", "loss_WXF_to_JSON", "Rac_WXF_to_JSON"}
        kind = "PEEC"
    else:
        raise ValueError("Unsupported original-cache validation scope")
    if not required.issubset(lookup):
        raise ValueError("Missing required complete complex/unit coverage: " + repr(sorted(required-set(lookup))))
    for row in checks:
        if "maximum_normalized_error" in row:
            value = row["maximum_normalized_error"]
            if not isinstance(value, (float, int)) or not math.isfinite(value) or value > 1 or value < 0:
                raise ValueError("Passing case contains invalid normalized numerical error")
        is_direct = "WXF_to_JSON" in row["id"] or "WXF_to_CSV" in row["id"] or row["id"] in {
            "every_GPU_current_ReIm", "every_CPU_current_ReIm", "every_GPU_current_abs",
            "every_GPU_current_phase", "every_original_center", "every_cell_J_from_original_face_flux_to_CSV"}
        if is_direct and row.get("kind") not in {"exact_identity", "exact_numerical_identity"}:
            if row.get("relative_tolerance", math.inf) > DIRECT_REL or row.get("absolute_tolerance", math.inf) > DIRECT_ABS * 1.00000001:
                raise ValueError("Direct WXF/JSON/CSV agreement tolerance was widened")
        if row["id"] == MATRIX_ID:
            if row.get("kind") != "arithmetic_reduction_agreement" or row.get("relative_tolerance") != 1e-12:
                raise ValueError("GPU Frobenius arithmetic-reduction contract missing")
            if row.get("direct_value_relative_tolerance") != DIRECT_REL or row.get("saved_physical_matrix_error_threshold") != 1e-10:
                raise ValueError("GPU direct-value/physical thresholds were changed")
            if not row.get("original_formula") or not row.get("verification_formula") or not row.get("tolerance_reason"):
                raise ValueError("GPU arithmetic reduction lacks explicit formula/roundoff explanation")
    if case.get("solver_executed") is not False or case.get("scope", {}).get("new_physics_solved") is not False:
        raise ValueError("Selected report must explicitly be read-only cache verification")
    scope = case["scope"]
    if scope.get("phasor") != "exp(+j omega t)" or scope.get("current_convention") != "RMS":
        raise ValueError("Selected case has incompatible complex-current convention")
    return kind, len(checks)


def parent_evidence(parent_id, rule, root):
    folder = root / "outputs" / parent_id
    report, report_file = read_json(folder / "frozen_validation" / "frozen_physics_validation.json", root, "original_validation_parent_report")
    tests, tests_file = read_json(folder / "frozen_validation" / "test_report.json", root, "original_validation_parent_test_report")
    process, process_file = read_json(folder / "process_status.json", root, "original_validation_parent_actual_process_exit")
    child, child_file = read_json(folder / "frozen_verifier_child_process.json", root, "original_validation_child_actual_process_exit")
    manifest, manifest_file = read_json(folder / "run_manifest.json", root, "original_validation_before_stage_manifest")
    source_sha = report.get("verifier_source_sha256")
    declared = [row for row in manifest.get("sources", []) if row.get("path", "").replace("\\", "/") == "src/VerifyFrozenPhysics.wls"]
    if len(declared) != 1 or declared[0].get("sha256") != source_sha:
        raise ValueError("Validation tool is not bound to its original before-stage source snapshot")
    snapshot = file_record(folder / "source_snapshot" / "src" / "VerifyFrozenPhysics.wls", root, "original_validation_tool_before_stage", source_sha)
    cases = report.get("cases")
    if not isinstance(cases, list) or not cases or report.get("unverified_reference_runs"):
        raise ValueError("Validation parent lacks a complete per-case report")
    keys = [(row.get("run_id"), row.get("case_id")) for row in cases]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate validation parent cases")
    references = report.get("ReferenceRuns")
    if not isinstance(references, list) or len(references) != len(set(references)) or set(references) != {key[0] for key in keys}:
        raise ValueError("Validation parent explicit reference coverage is incomplete")
    failed = [row for row in cases if row.get("validation_status") != PASSED]
    failed_checks = [{"raw_run_id": row.get("run_id"), "case_id": row.get("case_id"),
                      "failed_checks": [check for check in row.get("checks", []) if check.get("execution_status") != "passed"]}
                     for row in failed]
    parent_exit = process.get("process_exit_code")
    child_exit = child.get("process_exit_code")
    if type(parent_exit) is not int or type(child_exit) is not int:
        raise ValueError("Actual validation parent/child exit code missing")
    if child.get("solver_executed") is not False or report.get("solver_executed") is not False or report.get("new_physics_solved") is not False:
        raise ValueError("Validation parent must be explicitly read-only")
    if child.get("ReferenceRuns") != report.get("ReferenceRuns"):
        raise ValueError("Parent and actual child explicit references disagree")
    test_rows = tests.get("tests")
    if not isinstance(test_rows, list) or {(row.get("id"), row.get("execution_status")) for row in test_rows} != {
            (row["run_id"] + "/" + row["case_id"], "passed" if row["validation_status"] == PASSED else "failed_or_incomplete") for row in cases}:
        raise ValueError("Parent per-case test report disagrees with original validation cases")
    if rule is None:
        if parent_exit != 0 or child_exit != 0 or report.get("execution_status") != PASSED or tests.get("execution_status") != "passed" or failed:
            raise ValueError("Nonpassing parent requires an explicit partial-parent failure contract")
    else:
        if parent_exit != rule["expected_process_exit_code"] or child_exit != parent_exit or parent_exit == 0:
            raise ValueError("Partial parent actual exit differs from explicit preserved failure")
        if report.get("execution_status") != "not_verified_or_failed_original_evidence" or tests.get("execution_status") != "failed_or_incomplete":
            raise ValueError("Partial parent overall failure is not preserved")
        failed_raw = {row.get("run_id") for row in failed}
        ids = {check.get("id") for row in failed_checks for check in row["failed_checks"]}
        if failed_raw != set(rule["expected_failed_raw_run_ids"]) or ids != set(rule["allowed_failed_check_ids"]):
            raise ValueError("Partial parent failures differ from explicit allowed failed cases/checks")
        if any(row.get("missing_or_error") is not None for row in failed) or any(not row["failed_checks"] for row in failed_checks):
            raise ValueError("Incomplete parent case is not an allowed numerical-check-only failure")
    return {"verification_run_id": parent_id, "original_parent_execution_status": report.get("execution_status"),
            "original_parent_test_execution_status": tests.get("execution_status"), "actual_parent_process_exit_code": parent_exit,
            "actual_child_process_exit_code": child_exit, "partial_parent_failure_explicitly_preserved": rule is not None,
            "unselected_failed_cases": failed_checks, "parent_failed_outcome_changed": False,
            "source_files": [report_file, tests_file, process_file, child_file, manifest_file, snapshot]}, report


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def collect(selection_path, output, root=ROOT):
    root = Path(root).resolve()
    selection_path = Path(selection_path).resolve()
    output = Path(output).resolve()
    output.relative_to(root / "outputs")
    if output.exists():
        # The unified monitored runner prepares the new run's snapshot/log files.
        # Existing scientific/collector outputs are never overwritten.
        protected = ("results.json", "parameters.json", "selection.json", "test_report.json", "frozen_physics_validation.json")
        if not output.is_dir() or any((output / name).exists() for name in protected):
            raise FileExistsError("Existing output run is protected: " + str(output))
    else:
        output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    selected = []
    parents = []
    tests = []
    source_cache = {}
    report = {"schema_version": 1, "source_model": "explicit_original_cache_validation_report_collection",
              "execution_status": "failed_or_incomplete_collection", "physical_acceptance_status": "not_applicable_cache_integrity_only",
              "solver_executed": False, "new_physics_solved": False, "cases": selected, "verification_batches": parents,
              "process_exit_evidence": "caller_must_record_actual_collector_process_exit"}
    try:
        selection, selection_file = read_json(selection_path, root, "explicit_validation_report_selection")
        (output / "selection.json").write_bytes(selection_path.read_bytes())
        report["selection_source"] = selection_file
        report["collector_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        required, rows, partial = validate_selection(selection)
        report["ReferenceRuns"] = required
        parent_lookup = {}
        for parent_id in dict.fromkeys(row["verification_run_id"] for row in rows):
            evidence, parent_report = parent_evidence(parent_id, partial.get(parent_id), root)
            parents.append(evidence)
            parent_lookup[parent_id] = parent_report
        for row in rows:
            raw, parent, case_id = row["raw_run_id"], row["verification_run_id"], row["case_id"]
            folder = root / "outputs" / parent / "frozen_validation" / "cases"
            case, record = read_json(folder / (raw + "__" + case_id + ".json"), root, "selected_original_validation_case_report", row["case_report_sha256"])
            matching = [entry for entry in parent_lookup[parent]["cases"] if entry.get("run_id") == raw and entry.get("case_id") == case_id]
            if len(matching) != 1 or case != matching[0]:
                raise ValueError("Selected case report differs from its original parent embedded report")
            if case.get("run_id") != raw or case.get("case_id") != case_id or case.get("validation_status") != PASSED or case.get("missing_or_error") is not None:
                raise ValueError("Selected case identity/status is not fully passed")
            kind, count = check_numeric_records(case)
            sources = case.get("source_files")
            if not isinstance(sources, list) or not sources:
                raise ValueError("Selected case lacks original source hashes")
            verified = []
            for source in sources:
                if not isinstance(source, dict) or not source.get("path", "").startswith("outputs/" + raw + "/"):
                    raise ValueError("Selected original source is outside its explicit raw run")
                path = relative_path(root, source["path"])
                path.relative_to((root / "outputs" / raw).resolve())
                key = (source["path"], source.get("sha256"), source.get("bytes"))
                if key not in source_cache:
                    source_cache[key] = file_record(path, root, source.get("role", "original_raw_source"), source.get("sha256"), source.get("bytes"))
                verified.append(source_cache[key])
            roles = {source.get("role") for source in sources}
            if not {"original_complete_saved_model_or_solution", "original_stage_numeric_CSV", "original_model_source_before_stage",
                    "original_case_scalar_and_current_JSON", "original_case_input_parameters", "original_run_provenance"}.issubset(roles):
                raise ValueError("Original WXF/JSON/CSV/parameters/provenance/model-source coverage incomplete")
            if kind == "CPU_GPU" and "original_saved_GPU_matrix_and_solution" not in roles:
                raise ValueError("Original GPU matrix/current/voltage archive hash is missing")
            selected.append({**row, "validation_status": PASSED, "validation_kind": kind, "case_report": record,
                             "check_count": count, "source_files": verified, "scope": case["scope"],
                             "source_case_execution_status": case.get("source_case_execution_status"),
                             "source_physical_acceptance_status": case.get("source_physical_acceptance_status"),
                             "source_run_status": case.get("source_run_status"),
                             "physical_acceptance_status": case.get("physical_acceptance_status"),
                             "unit_and_complex_coverage": {"phasor": "exp(+j omega t)", "current_convention": "RMS",
                                                           "scope": case["scope"].get("JSON_vector_coverage")}})
            tests.append({"id": raw + "/" + case_id, "execution_status": "passed", "check_count": count})
        # Recheck stat stability for every original and validation report hashed.
        all_records = [selection_file] + list(source_cache.values())
        all_records += [source for parent in parents for source in parent["source_files"]]
        all_records += [case["case_report"] for case in selected]
        for record in all_records:
            stat = relative_path(root, record["path"]).stat()
            if (stat.st_size, stat.st_mtime_ns) != (record["bytes"], record["mtime_ns"]):
                raise ValueError("Original source/report changed before collection completed: " + record["path"])
        report["execution_status"] = PASSED
        report["selected_case_count"] = len(selected)
        report["selected_check_count"] = sum(row["check_count"] for row in selected)
        report["unique_original_files_rehashed"] = len(source_cache)
        report["source_status_policy"] = "Selected case agreement is passed; original parent failures and every original physical limitation remain unchanged. No physical acceptance is inferred."
        tests.append({"id": "exact_required_raw_run_coverage_and_source_hashes", "execution_status": "passed"})
    except (OSError, ValueError, KeyError, TypeError) as error:
        report["failure_reason"] = str(error)
        tests.append({"id": "explicit_original_report_collection", "execution_status": "failed", "reason": str(error)})
    report["elapsed_seconds"] = time.monotonic() - started
    write_json(output / "frozen_physics_validation.json", report)
    write_json(output / "test_report.json", {"execution_status": "passed" if report["execution_status"] == PASSED else "failed",
               "tests": tests, "solver_executed": False, "physical_acceptance_status": "not_applicable_cache_integrity_only"})
    write_json(output / "parameters.json", {"schema_version": 1, "ReferenceRuns": report.get("ReferenceRuns", []),
               "selection_source": report.get("selection_source"), "solver_executed": False,
               "units": "SI", "phasor": "exp(+j omega t)", "current_convention": "RMS"})
    write_json(output / "results.json", {"run_id": output.name, "source_model": report["source_model"],
               "execution_status": report["execution_status"], "physical_acceptance_status": report["physical_acceptance_status"],
               "data": report, "solver_executed": False, "failure_reason": report.get("failure_reason"),
               "process_exit_evidence": "caller_must_record_actual_collector_process_exit"})
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = collect(args.selection, args.output)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(report["execution_status"], "cases=", len(report["cases"]), "checks=", report.get("selected_check_count", 0))
    if report.get("failure_reason"):
        print(report["failure_reason"], file=sys.stderr)
    return 0 if report["execution_status"] == PASSED else 1


if __name__ == "__main__":
    raise SystemExit(main())
