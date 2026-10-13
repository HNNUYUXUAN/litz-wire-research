#!/usr/bin/env python3
"""Verify frozen exports, or redraw numerical cache CSVs without Wolfram/solvers.

This module never imports WXF, stage code, GPU libraries or external packages.
Physical acceptance remains the source run's status. Verification certifies archive
integrity and conversion completeness only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
from pathlib import Path
from typing import Any

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file() and (p / "configs/reference_parameters.json").is_file())
LFS_PREFIX = b"version https://git-lfs.github.com/spec/v1"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def is_lfs_pointer(path: Path) -> bool:
    with path.open("rb") as stream:
        return stream.read(256).startswith(LFS_PREFIX)


def contained(base: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError(f"invalid archive-relative path: {relative!r}")
    if relative.startswith("/") or ":" in relative:
        raise ValueError(f"absolute path is not an archive reference: {relative!r}")
    candidate = (base / relative).resolve()
    if not candidate.is_relative_to(base.resolve()):
        raise ValueError(f"path escapes archive: {relative!r}")
    return candidate


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def descriptors(value: Any):
    if isinstance(value, dict):
        if value.get("representation") == "numeric_csv":
            yield value
        for item in value.values():
            yield from descriptors(item)
    elif isinstance(value, list):
        for item in value:
            yield from descriptors(item)


def omissions(value: Any):
    if isinstance(value, dict):
        if value.get("representation") in {"not_exportable", "retained_in_original_WXF"}:
            yield value
        for item in value.values():
            yield from omissions(item)
    elif isinstance(value, list):
        for item in value:
            yield from omissions(item)


def scalar_leaf_paths(value: Any, prefix: str):
    """Independently check complete scalar paths while leaving vectors in cache."""
    def numeric_shape(item):
        if isinstance(item, (int, float)) and not isinstance(item, bool) and math.isfinite(item):
            return (), 1
        if not isinstance(item, list) or not item:
            return None
        shapes = [numeric_shape(child) for child in item]
        if any(shape is None for shape in shapes) or any(shape[0] != shapes[0][0] for shape in shapes):
            return None
        return (len(item),) + shapes[0][0], sum(shape[1] for shape in shapes)

    if isinstance(value, dict):
        if value.get("representation") == "complex_re_im":
            yield prefix, "scalar"
        elif "representation" in value:
            yield prefix, "array_reference"
        else:
            for key, item in value.items():
                yield from scalar_leaf_paths(item, prefix + "/" + str(key))
    elif isinstance(value, list):
        shape = numeric_shape(value)
        if shape and shape[1] > 128:
            yield prefix, "array_reference"
        else:
            for index, item in enumerate(value, 1):
                yield from scalar_leaf_paths(item, prefix + "/" + str(index))
    elif value is None or isinstance(value, (str, bool, int, float)):
        yield prefix, "scalar"
def csv_values(path: Path, complex_values: bool):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        expected = ["flat_index_1based", "real", "imag"] if complex_values else ["flat_index_1based", "value"]
        if next(reader, None) != expected:
            raise ValueError(f"incorrect numeric CSV header: {path.name}")
        for number, row in enumerate(reader, 1):
            if len(row) != len(expected) or int(row[0]) != number:
                raise ValueError(f"invalid flattened index at row {number}: {path.name}")
            values = [float(v.replace("*^", "e")) for v in row[1:]]
            if not all(math.isfinite(v) for v in values):
                raise ValueError(f"nonfinite numeric value at row {number}: {path.name}")
            yield complex(*values) if complex_values else values[0]


def check_roundtrip(report: Any, meta: dict[str, Any], data: Any, bundle: Path, root: Path) -> list[str]:
    errors = []
    if not isinstance(report, dict):
        return ["numerical roundtrip report missing"]
    for key in ("route", "run_id", "source_index_sha256"):
        if report.get(key) != meta.get(key):
            errors.append(f"roundtrip {key} does not bind the pinned original")
    if report.get("passed") is not True or report.get("solver_executed") is not False:
        errors.append("roundtrip numeric validation was not passed without a solver")
    source_path = report.get("source_payload_path")
    sources = {s["path"]: s for s in meta.get("source_files", [])}
    if source_path not in sources or sources[source_path]["sha256"] != report.get("source_payload_sha256"):
        errors.append("roundtrip source WXF/JSON hash is not in original inventory")
    elif digest(contained(root, source_path)) != report["source_payload_sha256"]:
        errors.append("roundtrip source WXF/JSON changed")
    rows = report.get("arrays", [])
    if not isinstance(rows, list):
        return errors + ["roundtrip array records malformed"]
    by_path = {r.get("csv_path"): r for r in rows if isinstance(r, dict)}
    arrays = list(descriptors(data))
    if len(by_path) != len(rows) or set(by_path) != {d["path"] for d in arrays}:
        errors.append("roundtrip array set differs from exported numerical descriptors")
    scalar = report.get("JSON_scalar_readback", {})
    records = rows + [scalar]
    for record in records:
        if not isinstance(record, dict):
            errors.append("roundtrip numeric record malformed")
            continue
        if record.get("passed") is not True:
            errors.append("roundtrip numeric record not passed")
        for key in ("maximum_absolute_error", "maximum_relative_error", "maximum_normalized_error",
                    "absolute_tolerance", "relative_tolerance"):
            value = record.get(key)
            if not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
                errors.append(f"roundtrip {key} is missing/invalid")
        if record.get("maximum_normalized_error", math.inf) > 1:
            errors.append("roundtrip original/readback error exceeds declared tolerance")
        if record.get("absolute_tolerance", math.inf) > 1.0000001e-30 or record.get("relative_tolerance", math.inf) > 2.0000001e-14:
            errors.append("roundtrip numerical tolerances exceed conversion policy")
    if scalar.get("keys_and_list_lengths_verified") is not True or not isinstance(scalar.get("numeric_scalars_compared"), int):
        errors.append("roundtrip JSON scalar/key readback missing")
    for descriptor in arrays:
        row = by_path.get(descriptor["path"])
        if not row:
            continue
        for key in ("dimensions", "element_count", "complex", "source_key"):
            if row.get(key) != descriptor.get(key):
                errors.append(f"roundtrip {key} differs from array descriptor")
        if row.get("indices_verified") is not True:
            errors.append("roundtrip CSV indices not verified against original array")
        anchors = row.get("original_WXF_anchors", [])
        positions = {a.get("flat_index_1based"): a for a in anchors if isinstance(a, dict)}
        expected_positions = {1, max(1, math.ceil(descriptor["element_count"] / 2)), descriptor["element_count"]}
        if set(positions) != expected_positions:
            errors.append("roundtrip original WXF numerical anchors missing")
        for number, value in enumerate(csv_values(contained(bundle, descriptor["path"]), descriptor["complex"]), 1):
            if number not in positions:
                continue
            anchor = positions[number]
            for component, actual in (("real", complex(value).real), ("imag", complex(value).imag)):
                original = anchor.get(component)
                if not isinstance(original, (float, int)) or not math.isclose(actual, original,
                        rel_tol=row["relative_tolerance"], abs_tol=row["absolute_tolerance"]):
                    errors.append(f"CSV {component} differs from original WXF anchor at {number}")
    return errors


def verify(bundle: Path, root: Path = ROOT, profile: str = "low32", require_notebooks: bool = False, require_process: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    notes: list[str] = []
    counts = {"routes": 0, "assets": 0, "source_files": 0, "numeric_arrays": 0, "explicit_omissions": 0, "notebooks": 0}
    bundle = bundle.resolve()
    try:
        manifest = read(bundle / "closure_manifest.json")
        index_path = contained(bundle, manifest["source_index"])
        index = read(index_path)
        index_hash = digest(index_path)
        if manifest["source_index_sha256"] != index_hash:
            errors.append("frozen index SHA256 mismatch")
        expected = index["routes"]
        routes = manifest["routes"]
        if set(routes) != set(expected):
            errors.append(f"route set mismatch: missing={sorted(set(expected)-set(routes))}; extra={sorted(set(routes)-set(expected))}")
        for name, row in routes.items():
            counts["routes"] += 1
            try:
                meta = read(contained(bundle, row["metadata"]))
                pin = expected[name]
                if meta["route"] != name or meta["run_id"] != pin["selected_run_id"] or row["run_id"] != meta["run_id"]:
                    errors.append(f"{name}: run/route differs from frozen pin")
                if meta["source_index_sha256"] != index_hash:
                    errors.append(f"{name}: source index hash mismatch")
                if row.get("export_status") not in {"exported", "json_only"}:
                    errors.append(f"{name}: conversion is incomplete")
                if meta.get("solver_executed") is not False or row.get("solver_executed") is not False:
                    errors.append(f"{name}: missing no-solver conversion declaration")
                for field in ("execution_status", "physical_acceptance_status"):
                    if field in pin and meta.get(field) != pin[field]:
                        errors.append(f"{name}: {field} differs from source pin")
                asset_paths: set[str] = set()
                for asset in row["assets"]:
                    path = contained(bundle, asset["path"])
                    asset_paths.add(asset["path"])
                    counts["assets"] += 1
                    if not path.is_file():
                        errors.append(f"{name}: missing asset {asset['path']}")
                    elif is_lfs_pointer(path):
                        errors.append(f"{name}: unresolved LFS pointer {asset['path']}")
                    elif digest(path) != asset["sha256"]:
                        errors.append(f"{name}: asset SHA256 mismatch {asset['path']}")
                if meta["data"] not in asset_paths:
                    errors.append(f"{name}: scalar data not covered by asset manifest")
                source_files = meta.get("source_files", [])
                if not source_files:
                    errors.append(f"{name}: missing source hash inventory")
                for source in source_files:
                    path = contained(root, source["path"])
                    counts["source_files"] += 1
                    if not path.is_file():
                        errors.append(f"{name}: missing source {source['path']}")
                    elif is_lfs_pointer(path):
                        errors.append(f"{name}: unresolved source LFS pointer {source['path']}")
                    elif digest(path) != source["sha256"]:
                        errors.append(f"{name}: source SHA256 mismatch {source['path']}")
                source_dir = root / "outputs" / meta["run_id"]
                sources_by_path = {s["path"]: s for s in source_files}
                for asset in row["assets"]:
                    if asset.get("kind") not in {"preserved_custom_data", "preserved_unparseable_original", "preserved_figure"} or not asset.get("source_path"):
                        continue
                    original = sources_by_path.get(asset["source_path"])
                    if not original or original["sha256"] != asset["sha256"]:
                        errors.append(f"{name}: preserved custom/figure bytes differ from original source {asset['path']}")
                if meta.get("source_inventory_policy") == "recursive_original_files":
                    actual = {p.relative_to(root).as_posix() for p in source_dir.rglob("*") if p.is_file()}
                    inventoried = {s["path"] for s in source_files}
                    if actual != inventoried:
                        errors.append(f"{name}: recursive original inventory incomplete: missing={sorted(actual-inventoried)}; extra={sorted(inventoried-actual)}")
                    # Every recursive custom JSON/CSV must be covered, preserving
                    # subdirectories so equal case filenames cannot collide.
                    for source in source_files:
                        relative = Path(source["path"]).relative_to(Path("outputs") / meta["run_id"])
                        if relative.parts[0] in {"source_snapshot", "source_snapshots"} or relative.name in {"environment.json", "process_status.json", "resource_budget.json", "run_manifest.json"}:
                            continue
                        if relative.as_posix() in {"results.json", "parameters.json", "test_report.json"} or relative.suffix.lower() not in {".json", ".csv"}:
                            continue
                        required = (Path("routes") / name / "custom" / relative).as_posix()
                        if required not in asset_paths:
                            errors.append(f"{name}: custom numerical source omitted from assets {required}")
                declared_path = source_dir / "run_manifest.json"
                if declared_path.exists():
                    declared = read(declared_path)
                    inventoried = {s["path"] for s in source_files}
                    for source in declared.get("sources", []):
                        relative = (Path("outputs") / meta["run_id"] / "source_snapshot" / source["path"].replace("\\", "/")).as_posix()
                        snapshot_path = contained(root, relative)
                        if relative not in inventoried or not snapshot_path.exists():
                            errors.append(f"{name}: original source snapshot missing from inventory {relative}")
                        elif digest(snapshot_path).lower() != source["sha256"].lower():
                            errors.append(f"{name}: original run source snapshot hash mismatch {relative}")
                process = read(source_dir / "process_status.json") if (source_dir / "process_status.json").exists() else {}
                if meta.get("process_exit") != process.get("process_exit_code"):
                    errors.append(f"{name}: historical process exit was changed")
                if meta.get("process_exit") is None:
                    notes.append(f"{name}: historical normal process exit evidence unavailable")
                if "pinned_process_evidence" in meta:
                    if meta["pinned_process_evidence"] != pin.get("process_evidence"):
                        errors.append(f"{name}: pinned process evidence was changed")
                    evidence = meta["pinned_process_evidence"]
                    if isinstance(evidence, dict):
                        evidence_path = contained(root, evidence["path"])
                        if not evidence_path.is_file() or digest(evidence_path).lower() != evidence["sha256"].lower():
                            errors.append(f"{name}: pinned wrapper/native process evidence hash mismatch")
                if "effective_parameters" in meta:
                    parameters = meta["effective_parameters"]
                    if "net_transport_current_RMS_A" in parameters and (
                            parameters.get("current_RMS_A") != parameters["net_transport_current_RMS_A"] or
                            parameters.get("total_current_RMS_A") != parameters["net_transport_current_RMS_A"]):
                        errors.append(f"{name}: generic transport current overrides explicit imposed-field parameters")
                    for parameter_source in meta.get("effective_parameter_sources", []):
                        original = sources_by_path.get(parameter_source["path"])
                        if not original or original["sha256"] != parameter_source["sha256"]:
                            errors.append(f"{name}: effective parameter origin not bound to original inventory")
                if "scalar_index" in meta:
                    if meta["scalar_index"] not in asset_paths:
                        errors.append(f"{name}: complete scalar index is absent from asset inventory")
                    else:
                        scalar_index = read(contained(bundle, meta["scalar_index"]))
                        if scalar_index.get("route") != name or scalar_index.get("run_id") != meta["run_id"] or scalar_index.get("source_index_sha256") != index_hash:
                            errors.append(f"{name}: scalar coverage index does not bind the selected original")
                        entries = scalar_index.get("scalars", [])
                        if scalar_index.get("scalar_count") != len(entries) or meta.get("scalar_count") != len(entries):
                            errors.append(f"{name}: complete scalar index count mismatch")
                        for entry in entries + scalar_index.get("array_references", []):
                            original = sources_by_path.get(entry.get("source_file"))
                            if not original or original["sha256"] != entry.get("source_sha256") or entry.get("cached_file") not in asset_paths:
                                errors.append(f"{name}: scalar/array origin is not bound to complete cached source")
                        cached_sources = {meta["data"]: "data"}
                        cached_sources.update({asset["path"]: "custom" for asset in row["assets"]
                                               if asset.get("kind") == "preserved_custom_data" and asset["path"].lower().endswith(".json")})
                        expected_leaves = {(cached_file, key, kind) for cached_file, prefix in cached_sources.items()
                                           for key, kind in scalar_leaf_paths(read(contained(bundle, cached_file)), prefix)}
                        actual_leaves = [(entry.get("cached_file"), entry.get("source_key"), "scalar") for entry in entries]
                        actual_leaves += [(entry.get("cached_file"), entry.get("source_key"), "array_reference")
                                          for entry in scalar_index.get("array_references", [])]
                        if len(actual_leaves) != len(set(actual_leaves)) or set(actual_leaves) != expected_leaves:
                            errors.append(f"{name}: complete scalar/vector key coverage differs from cached primary/custom JSON")
                data = read(contained(bundle, meta["data"]))
                if meta.get("numerical_roundtrip_required"):
                    report_path = meta.get("numerical_roundtrip")
                    if report_path not in asset_paths:
                        errors.append(f"{name}: numerical roundtrip report not in hashed assets")
                    report = read(contained(bundle, report_path))
                    errors.extend(f"{name}: {message}" for message in check_roundtrip(report, meta, data, bundle, root))
                for descriptor in descriptors(data):
                    counts["numeric_arrays"] += 1
                    if descriptor["path"] not in asset_paths:
                        errors.append(f"{name}: array not in hash inventory {descriptor['path']}")
                    dims = descriptor["dimensions"]
                    if not dims or any(not isinstance(n, int) or n < 0 for n in dims) or math.prod(dims) != descriptor["element_count"]:
                        errors.append(f"{name}: array dimensions/count inconsistent {descriptor['path']}")
                    count = sum(1 for _ in csv_values(contained(bundle, descriptor["path"]), descriptor["complex"]))
                    if count != descriptor["element_count"]:
                        errors.append(f"{name}: array row count mismatch {descriptor['path']}")
                    if not descriptor.get("unit"):
                        errors.append(f"{name}: array unit declaration missing")
                for omission in omissions(data):
                    counts["explicit_omissions"] += 1
                    if not omission.get("reason"):
                        errors.append(f"{name}: unsupported object lacks reason")
            except (OSError, ValueError, KeyError, TypeError) as exc:
                errors.append(f"{name}: {exc}")
        if (bundle / "json_normalization.json").exists():
            normalization = read(bundle / "json_normalization.json")
            if normalization.get("source_index_sha256") != index_hash or normalization.get("solver_executed") is not False:
                errors.append("JSON normalization is not bound to the frozen index")
            for item in normalization.get("files", []):
                original = contained(bundle, item["original_bytes_preserved_at"])
                current = contained(bundle, item["path"])
                if digest(original) != item["original_sha256"] or digest(current) != item["normalized_sha256"]:
                    errors.append("JSON zero normalization file SHA differs")
                restored = original.read_text(encoding="utf-8-sig")
                from decimal import Decimal
                for change in reversed(item["changes"]):
                    offset = change["character_offset"]
                    before, after = change["original_token"], change["normalized_token"]
                    if restored[offset:offset+len(before)] != before or Decimal(after) != 0 or before.replace(".e", ".0e").replace(".E", ".0E") != after:
                        errors.append("JSON correction alters more than an exact zero spelling")
                    restored = restored[:offset]+after+restored[offset+len(before):]
                if current.read_text(encoding="utf-8-sig") != restored or item.get("numeric_value_changed") is not False:
                    errors.append("normalized JSON differs beyond recorded zero tokens")
            units = read(bundle / "unit_clarifications.json")
            if units.get("source_index_sha256") != index_hash or units.get("solver_executed") is not False:
                errors.append("unit clarifications do not bind frozen index")
            if (bundle / "unit_annotation_source_snapshot/manifest.json").exists():
                unit_sources = {row["path"]: row for row in read(bundle / "unit_annotation_source_snapshot/manifest.json")["sources"]}
                for evidence in {row["path"]: row for rule in units["rules"] for row in rule["source_evidence"]}.values():
                    source_row = unit_sources.get(evidence["path"])
                    if not source_row or source_row["sha256"] != evidence["sha256"] or digest(contained(bundle, source_row["snapshot_path"])) != evidence["sha256"]:
                        errors.append("unit annotation source snapshot SHA differs")
            unit_hashes, unit_keys = {}, set()
            for override in units.get("overrides", []):
                cached = override["cached_file"]
                if cached not in unit_hashes:
                    unit_hashes[cached] = digest(contained(bundle, cached))
                if unit_hashes[cached] != override["original_cached_file_sha256"] or not override.get("unit"):
                    errors.append("unit override cached source hash/unit mismatch")
                key = cached, override["source_key"]
                if key in unit_keys:
                    errors.append("duplicate unit override source key")
                unit_keys.add(key)
            counts["unit_overrides"] = len(unit_keys)
            original_exit = read(bundle / "source_export_evidence" / "process_status.json")
            steps = read(bundle / "source_export_evidence" / "export_process_status.json")["processes"]
            route_steps = [step for step in steps if step.get("stage") == "ExportClosureEvidence.wls"]
            if original_exit.get("process_exit_code") != 0 or {step.get("route") for step in route_steps} != set(expected) or any(step.get("process_exit_code") != 0 for step in route_steps):
                errors.append("derived cache lacks original complete 63-route actual exit evidence")
            notes.append("origin cache and its initial failed JSON/display verification are preserved; this cache applies only recorded syntax/unit clarifications")
        for supplement in manifest.get("supplements", []):
            from ExportRetainedTopology import verify as verify_topology
            supplement_path = contained(bundle, supplement["manifest"])
            supplement_manifest = read(supplement_path)
            source = contained(root, "outputs/"+supplement["run_id"])
            if digest(source / "topology_manifest.json") != supplement["original_manifest_sha256"]:
                errors.append("supplemental original integer topology report SHA differs")
            check = verify_topology(source, bundle, root)
            errors.extend("topology supplement: "+message for message in check["errors"])
            for array in supplement_manifest["arrays"]:
                if digest(contained(bundle, array["path"])) != array["sha256"]:
                    errors.append("attached supplemental topology CSV SHA differs")
            counts["supplemental_numeric_arrays"] = counts.get("supplemental_numeric_arrays", 0)+check["arrays"]
            counts["supplemental_integer_components"] = counts.get("supplemental_integer_components", 0)+check["integer_components"]
        notebook_path = bundle / "archive_notebooks.json"
        if notebook_path.exists():
            archive = read(notebook_path)
            if archive.get("source_index_sha256") != index_hash or archive.get("failures"):
                errors.append("Notebook cache build failed or refers to another index")
            for book in archive["notebooks"]:
                counts["notebooks"] += 1
                for key in ("notebook", "html"):
                    path = contained(bundle, book[key])
                    if not path.exists() or digest(path) != book[f"{key}_sha256"]:
                        errors.append(f"Notebook/HTML SHA256 mismatch: {book[key]}")
                if book.get("input_cell_count") != 0 or book.get("solver_executed") is not False:
                    errors.append(f"archive notebook is active: {book['notebook']}")
                original = contained(root, book["source_notebook"])
                if not original.exists() or digest(original) != book["source_sha256"]:
                    errors.append(f"research notebook differs from source snapshot: {book['source_notebook']}")
            notes.append("real-device low32 frontend acceptance remains pending unless separately recorded")
        elif require_notebooks:
            errors.append("archive_notebooks.json missing; cache build has not run")
        process_path = bundle / "export_process_status.json"
        if not process_path.exists() and (bundle / "process_status.json").exists():
            process_path = bundle / "process_status.json"
        if process_path.exists():
            proc = read(process_path)
            exit_values = proc.get("processes", [proc])
            if not exit_values or any(p.get("process_exit_code") != 0 for p in exit_values):
                errors.append("conversion process did not produce normal exit evidence")
        elif require_process:
            errors.append("caller-recorded export process exit evidence missing")
        else:
            notes.append("conversion child process exit evidence not checked")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"bundle: {exc}")
    return {"schema_version": 1, "profile": profile, "execution_status": "failed" if errors else "passed", "scope": "frozen archive integrity and numerical conversion; no physical acceptance upgrade", "solver_executed": False, "errors": errors, "notes": notes, "counts": counts, "low32_real_device_acceptance": "pending"}


def rebuild_figures(bundle: Path) -> dict[str, Any]:
    """Create bounded, static line plots solely from exported numerical CSVs."""
    manifest = read(bundle / "closure_manifest.json")
    target = bundle / "rebuilt_figures"
    target.mkdir(exist_ok=True)
    records = []
    for name, row in manifest["routes"].items():
        meta = read(contained(bundle, row["metadata"]))
        data = read(contained(bundle, meta["data"]))
        arrays = [d for d in descriptors(data) if any(token in d.get("source_key", "").lower() for token in ("current", "profile"))]
        for number, desc in enumerate(arrays[:4], 1):
            values = []
            stride = max(1, math.ceil(desc["element_count"] / 2048))
            for index, value in enumerate(csv_values(contained(bundle, desc["path"]), desc["complex"])):
                if index % stride == 0:
                    values.append((index + 1, abs(value) if isinstance(value, complex) else value))
            if not values:
                continue
            ymin = min(v for _, v in values); ymax = max(v for _, v in values)
            span = max(ymax-ymin, abs(ymax)*1e-12, 1e-30)
            xmin = values[0][0]; xmax = max(values[-1][0], xmin+1)
            points = " ".join(f"{70+760*(x-xmin)/(xmax-xmin):.3f},{330-240*(v-ymin)/span:.3f}" for x, v in values)
            title = f"{name}: cached {'absolute complex value' if desc['complex'] else 'value'}; flattened array index"
            source_key = html.escape(desc["source_key"])
            svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 440"><rect width="900" height="440" fill="white"/><g font-family="sans-serif" fill="#253547"><text x="35" y="30" font-size="17">{html.escape(title)}</text><text x="35" y="55" font-size="11">{source_key}</text><text x="35" y="78" font-size="11">{html.escape(meta["run_id"])} | {html.escape(desc["unit"])}</text><path d="M70 100V330H830" fill="none" stroke="#8494a7"/><polyline points="{points}" fill="none" stroke="#176c99" stroke-width="1.5"/><text x="70" y="358">flat index (1-based); stride {stride}</text><text x="70" y="384" font-size="11">Frozen numerical cache; source physical status: {html.escape(meta["physical_acceptance_status"])}</text><text x="70" y="408" font-size="11">Range: {ymin:.8g} to {ymax:.8g}; no new solve</text></g></svg>'
            path = target / f"{name}_{number}.svg"
            path.write_text(svg, encoding="utf-8")
            records.append({"path": path.relative_to(bundle).as_posix(), "sha256": digest(path), "source_csv": desc["path"], "source_csv_sha256": digest(contained(bundle, desc["path"])), "run_id": meta["run_id"], "source_key": desc["source_key"], "sampling_stride": stride, "solver_executed": False})
    report = {"schema_version": 1, "source_index_sha256": manifest["source_index_sha256"], "figures": records, "solver_executed": False}
    (target / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--profile", default="low32", choices=("low32", "high64", "high64gpu"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--require-notebooks", action="store_true")
    parser.add_argument("--require-process", action="store_true")
    parser.add_argument("--rebuild-figures", action="store_true")
    args = parser.parse_args()
    result = verify(args.bundle, args.root, args.profile, args.require_notebooks, args.require_process)
    if result["execution_status"] == "passed" and args.rebuild_figures:
        result["rebuilt_figure_count"] = len(rebuild_figures(args.bundle)["figures"])
    path = args.bundle / "closure_verification.json"
    if args.bundle.is_dir():
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["execution_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
