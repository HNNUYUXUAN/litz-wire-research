#!/usr/bin/env python3
"""Monitored supplemental conversion of explicitly retained frozen mesh topology."""
from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import sys
from pathlib import Path

from PreManuscriptClosure import GIB, ROOT, digest, now, read, run_custom_monitored, write
from VerifyClosureEvidence import contained, omissions


def verify(folder: Path, bundle: Path, root: Path | None = None) -> dict:
    root = root or ROOT
    request = read(folder / "request.json")
    manifest = read(folder / "topology_manifest.json")
    errors = []
    if not manifest or manifest.get("execution_status") != "passed_original_integer_topology_readback":
        return {"passed": False, "errors": ["original topology conversion failed or missing"]}
    if read(folder / "process_status.json", {}).get("process_exit_code") != 0:
        errors.append("supplemental conversion actual process exit is not zero")
    if manifest.get("solver_executed") is not False or manifest.get("GPU_compute_enabled") is not False:
        errors.append("supplement is not marked as a CPU cache conversion")
    for key in ("source_index_sha256", "source_payload_path", "source_payload_sha256", "original_data_path", "original_data_sha256"):
        if manifest.get(key) != request[key]:
            errors.append(f"manifest/request mismatch: {key}")
    for path_key, hash_key in (("source_index_path", "source_index_sha256"), ("source_payload_path", "source_payload_sha256"), ("original_data_path", "original_data_sha256")):
        if digest(contained(root, request[path_key])) != request[hash_key]:
            errors.append(f"original SHA changed: {path_key}")
    if not manifest.get("checks") or any(check.get("passed") is not True for check in manifest["checks"]):
        errors.append("original-WXF checks are not all passed")
    required_checks = {"frozen_index_SHA256", "original_omission_SHA256", "original_WXF_SHA256_before_read", "original_WXF_SHA256_after_read", "frozen_index_SHA256_after_read"}
    for target in request["targets"]:
        required_checks.update(target["source_key"] + suffix for suffix in ("_dimensions", "_integer_node_IDs", "_CSV_write", "_CSV_header_rows", "_CSV_indices", "_original_WXF_integer_readback"))
        required_checks.add(target["alias_source_key"] + "_identity")
    if {check.get("id") for check in manifest.get("checks", [])} != required_checks:
        errors.append("original-WXF direct identity and full integer readback checks incomplete")
    targets = {row["source_key"]: row for row in request["targets"]}
    if {row["source_key"] for row in manifest["arrays"]} != set(targets):
        errors.append("explicit retained target coverage differs")
    count = 0
    for array in manifest["arrays"]:
        target = targets[array["source_key"]]
        path = contained(folder, array["path"])
        dims = array["dimensions"]
        if digest(path) != array["sha256"] or path.stat().st_size != array["bytes"] or dims != target["dimensions"]:
            errors.append(f"CSV SHA/dimensions mismatch: {path.name}")
        if array.get("alias_source_keys") != [target["alias_source_key"]]:
            errors.append("original alias coverage missing")
        rt = array.get("roundtrip", {})
        if not rt.get("passed") or rt.get("components_compared") != dims[0]*dims[1] or any(rt.get(key) != 0 for key in ("maximum_absolute_error", "absolute_tolerance", "relative_tolerance")):
            errors.append(f"exact original integer roundtrip failed: {path.name}")
        anchors = {row["element_index_1based"]: row["node_IDs"] for row in rt["original_WXF_anchors"]}
        number = 0
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream)
            if next(reader) != array["CSV_header"]:
                errors.append(f"CSV header mismatch: {path.name}")
            for number, row in enumerate(reader, 1):
                values = [int(value) for value in row]
                if len(values) != dims[1]+1 or values[0] != number or any(not 1 <= node <= array["node_count"] for node in values[1:]):
                    raise ValueError(f"invalid mesh row: {path.name}:{number}")
                if number in anchors and values[1:] != anchors[number]:
                    errors.append(f"original WXF anchor mismatch: {path.name}:{number}")
        if number != dims[0]:
            errors.append(f"CSV row count mismatch: {path.name}")
        count += number*dims[1]
    if digest(bundle / "source_index.json") != request["source_index_sha256"]:
        errors.append("bundle index changed")
    return {"schema_version": 1, "passed": not errors, "errors": errors, "arrays": len(manifest["arrays"]), "integer_components": count, "solver_executed": False, "scope": "supplemental exact integer topology conversion; no physical acceptance upgrade"}


def attach(folder: Path, bundle: Path) -> None:
    """Add assets without altering the original data, metadata or roundtrip."""
    evidence = verify(folder, bundle)
    if not evidence["passed"]:
        raise ValueError(str(evidence["errors"]))
    manifest = read(folder / "topology_manifest.json")
    closure = read(bundle / "closure_manifest.json")
    route = manifest["route"]
    destination = bundle / "routes" / route / "supplements" / folder.name
    destination.mkdir(parents=True, exist_ok=False)
    assets = []
    for source in [folder / "topology_manifest.json", folder / "test_report.json", folder / "process_status.json", folder / "resource_summary.json", *[contained(folder, row["path"]) for row in manifest["arrays"]]]:
        relative = source.relative_to(folder)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.name == "topology_manifest.json":
            copied = dict(manifest)
            copied["arrays"] = [dict(row, path=(destination / row["path"]).relative_to(bundle).as_posix()) for row in manifest["arrays"]]
            copied["original_manifest_sha256"] = digest(source)
            write(target, copied)
        else:
            shutil.copy2(source, target)
        asset = {"path": target.relative_to(bundle).as_posix(), "sha256": digest(target), "bytes": target.stat().st_size, "kind": "supplemental_mesh_connectivity" if source.suffix == ".csv" else "supplemental_topology_evidence"}
        assets.append(asset)
    closure["routes"][route]["assets"].extend(assets)
    closure.setdefault("supplements", []).append({"run_id": folder.name, "route": route, "manifest": next(row["path"] for row in assets if row["path"].endswith("/topology_manifest.json")), "original_manifest_sha256": digest(folder / "topology_manifest.json"), "resolved_source_keys": [key for row in manifest["arrays"] for key in [row["source_key"], *row["alias_source_keys"]]], "solver_executed": False})
    write(bundle / "closure_manifest.json", closure)
    write(folder / "attachment.json", {"attached_at_UTC": now(), "bundle_relative_path": destination.relative_to(bundle).as_posix(), "assets": assets, "original_data_unchanged": digest(contained(ROOT, manifest["original_data_path"])) == manifest["original_data_sha256"]})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--attach", action="store_true")
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id):
        parser.error("invalid run ID")
    origin_exit = read(bundle / "source_export_evidence" / "process_status.json", {}).get("process_exit_code")
    if read(bundle / "process_status.json", {}).get("process_exit_code") != 0 and origin_exit != 0:
        raise ValueError("complete primary export must exit normally before supplement")
    closure = read(bundle / "closure_manifest.json")
    index = read(bundle / "source_index.json")
    if set(closure["routes"]) != set(index["routes"]):
        raise ValueError("primary route coverage incomplete")
    environment = read(bundle / "environment.json")
    if not environment.get("user_selected_document_host") or environment.get("GPU_compute_enabled") is not False:
        raise ValueError("explicit accepted CPU-only document host required")
    route = "coax640"
    data_path = bundle / "routes" / route / "data.json"
    data = read(data_path)
    targets = []
    for item in omissions(data):
        match = re.fullmatch(r"data/cases/(\d+)/mesh/elements/(\d+)/connectivity", item.get("source_key", ""))
        if not match or item.get("representation") != "retained_in_original_WXF":
            continue
        case_index, element_index = map(int, match.groups())
        case = data["cases"][case_index-1]
        targets.append({"case_index_1based": case_index, "element_index_1based": element_index, "dimensions": item["dimensions"], "source_key": item["source_key"], "alias_source_key": f"data/cases/{case_index}/triangles_node_ids", "coordinate_reference": case["mesh"]["coordinates"]["path"], "marker_reference": case["mesh"]["elements"][element_index-1]["markers"]["path"]})
    if not targets:
        raise ValueError("no explicitly retained connectivity targets")
    folder = ROOT / "outputs" / args.run_id
    folder.mkdir(exist_ok=False)
    (folder / "arrays").mkdir()
    sources = []
    for name in ("ExportRetainedTopology.wls", "ExportRetainedTopology.py", "PreManuscriptClosure.py"):
        source = ROOT / "src" / name
        target = folder / "source_snapshot" / "src" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        sources.append({"path": source.relative_to(ROOT).as_posix(), "sha256": digest(source)})
    run = closure["routes"][route]["run_id"]
    wxf = ROOT / "outputs" / run / "results.wxf"
    request = {"schema_version": 1, "run_id": args.run_id, "route": route, "source_run_id": run, "source_index_path": (bundle / "source_index.json").relative_to(ROOT).as_posix(), "source_index_sha256": closure["source_index_sha256"], "source_payload_path": wxf.relative_to(ROOT).as_posix(), "source_payload_sha256": digest(wxf), "original_data_path": data_path.relative_to(ROOT).as_posix(), "original_data_sha256": digest(data_path), "targets": targets}
    write(folder / "request.json", request)
    write(folder / "run_manifest.json", {"snapshot_time": "before_supplemental_conversion", "sources": sources, "request_sha256": digest(folder / "request.json"), "solver_executed": False})
    write(folder / "environment.json", dict(environment, task="supplemental_cached_integer_topology", CPU_thread_limit=8, working_budget_bytes=24*GIB, minimum_free_system_bytes=8*GIB))
    process_env = dict(os.environ, LITZ_TOPOLOGY_REQUEST=str(folder / "request.json"), OMP_NUM_THREADS="8", MKL_NUM_THREADS="8", OPENBLAS_NUM_THREADS="8")
    command = [shutil.which("wolframscript") or "wolframscript", "-file", str(ROOT / "src" / "ExportRetainedTopology.wls")]
    result = run_custom_monitored(command, folder, process_env, 24*GIB)
    if result.returncode:
        return result.returncode
    report = verify(folder, bundle)
    changed = [row["path"] for row in sources if digest(ROOT / row["path"]) != row["sha256"]]
    if changed:
        report["passed"] = False
        report["errors"].append(f"source changed during conversion: {changed}")
    write(folder / "test_report.json", report)
    if report["passed"] and args.attach:
        attach(folder, bundle)
    print(report)
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
