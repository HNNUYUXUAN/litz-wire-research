#!/usr/bin/env python3
"""Derive a final frozen cache; normalize JSON zero syntax and audit unit notes."""
from __future__ import annotations
import argparse
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import re
import shutil

from PreManuscriptClosure import ROOT, digest, now, read, write

TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|(?P<zero>(?<![\w.])-?0\.[eE][-+]?\d+(?![\w.]))')


def normalize_zeros(text):
    changed = []
    def replace(match):
        token = match.group("zero")
        if token is None:
            return match.group()
        fixed = token.replace(".e", ".0e").replace(".E", ".0E")
        if Decimal(fixed) != 0:
            raise ValueError("normalization only accepts exact numeric zero")
        changed.append({"character_offset": match.start(), "original_token": token, "normalized_token": fixed, "exact_decimal_value": "0"})
        return fixed
    normalized = TOKEN.sub(replace, text)
    json.loads(normalized, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    return normalized, changed


def semantic_key(source_key):
    parts = [part for part in source_key.split("/") if not part.isdigit() and part not in {"real", "imag"}]
    key = parts[-1]
    return re.sub(r"_(?:ReIm|Re_Im|real|imag|Re|Im)$", "", key)


def infer_unit(source_key, route):
    key = semantic_key(source_key)
    # Most specific compound dimensions precede their denominator suffix.
    if re.search(r"(?:_RMS)?_A_per_m2(?:_|$)", key):
        return "A/m^2 RMS" if "RMS" in key else "A/m^2", "current_density", None
    for suffix, unit, rule in [("_V_per_m", "V/m", "voltage_gradient"), ("_S_per_m", "S/m", "conductivity"), ("_ohm_m", "ohm m", "resistivity"), ("_H_per_m", "H/axial_m", "inductance_per_length"), ("_m3_per_axial_m", "m^3/axial_m", "copper_volume_per_length"), ("_ohm_per_axial_m", "ohm/axial_m", "resistance_per_length"), ("_ohm_per_m", "ohm/axial_m", "resistance_per_length"), ("_W_per_axial_m", "W/axial_m", "loss_per_length"), ("_W_per_m", "W/axial_m", "loss_per_length"), ("_W_per_m3", "W/m^3", "loss_density")]:
        if key.endswith(suffix):
            return unit, rule, None
    if key == "loss_W_segment":
        return "W", "segment_power", None
    if key in {"connectivity", "connectivity_node_ids", "triangles_node_ids", "local_face_ids", "boundary_node_ids", "boundary_sample_node_ids"}:
        return "dimensionless node/face identifiers", "topology_identifiers", None
    if key in {"markers", "element_markers", "material_ID", "material_ids"}:
        return "dimensionless material labels", "material_labels", None
    if "permutations" in key:
        return "dimensionless permutation entries", "permutations", None
    if key == "coordinates_dimensionless":
        return "dimensionless", "normalized_coordinates", None
    if key == "weights_m":
        return "m", "explicit_DTM_axial_step", None
    if key in {"normalized_quadrature_weights", "reference_quadrature_weights"}:
        return "dimensionless", "normalized_reference_weights", None
    if route in {"analytic", "closure_analytic"} and key == "profile":
        return "mixed column units; see column_units", "analytical_profile_columns", ["m", "A/m^2 RMS", "A/m^2 RMS", "A/m^2 RMS", "rad", "W/m^3"]
    if route in {"analytic", "closure_analytic"} and key == "frequency_sweep":
        return "mixed column units; see column_units", "analytical_frequency_columns", ["Hz", "dimensionless", "ohm/axial_m"]
    if re.search(r"(?:^|_)seconds(?:_|$)", key) or key.endswith("_s"):
        return "s", "explicit_seconds", None
    if key.endswith("_bytes"):
        return "bytes", "explicit_bytes", None
    if key.endswith("_RMS_A") or key in {"currents", "voltage"}:
        return ("V RMS" if key == "voltage" else "A RMS"), "RMS_phasor", None
    for suffix, unit in [("_A", "A"), ("_RMS_V", "V RMS"), ("_V", "V"), ("_T", "T"), ("_ohm", "ohm"), ("_H", "H"), ("_W", "W"), ("_Hz", "Hz"), ("_mm2", "mm^2"), ("_mm", "mm"), ("_m2", "m^2"), ("_m3", "m^3"), ("_m", "m"), ("_C", "degC")]:
        if key.endswith(suffix):
            return unit, "explicit_unit_suffix", None
    if any(token in key for token in ("relative", "residual", "tolerance")) or key in {"Rac_Rdc", "Rac_over_Rdc", "arc_length_growth", "mean_arc_length_growth", "relative_permeability", "h_normalized", "complex_filament_current_deviation_L2"}:
        # Unqualified tolerances can carry physical units; only explicitly relative
        # tolerances and normalized residuals are safely dimensionless.
        if "tolerance" not in key or "relative" in key or key in {"GMRES_tolerance", "GMRES_true_relative_tolerance"}:
            return "dimensionless", "explicit_relative_or_normalized_metric", None
    return None, None, None


def unit_audit(bundle):
    closure = read(bundle / "closure_manifest.json")
    records, scanned, unknown, rules = {}, Counter(), Counter(), {}
    sources = [{"path": "src/"+name, "sha256": digest(ROOT / "src" / name)} for name in ("FinalizeClosureCache.py", "CoaxFEM.wl", "Q1Analytical.wl", "NotebookPhysics.wl", "PEEC.wl", "VoxelPEEC.wl", "stages/analytic.wl", "stages/geometry.wl", "stages/closure_geometry.wl", "stages/closure_peec.wl", "stages/closure_rt0.wl")]
    def record(route, cached_file, source_key, old_unit, kind, origin):
        scanned[kind] += 1
        unit, rule, columns = infer_unit(source_key, route)
        if unit is None:
            unknown[semantic_key(source_key)] += 1
            return
        rules[rule] = {"rule_id": rule, "precedence": "compound physical dimensions before denominator suffix; exact source_key lookup", "source_evidence": sources, "scope": "annotation only; original values, source statuses and files unchanged"}
        if unit == old_unit and columns is None:
            return
        row = {"route": route, "cached_file": cached_file, "source_key": source_key, "original_unit": old_unit, "unit": unit, "rule_id": rule, "original_cached_file_sha256": digest(bundle / cached_file), "kind": kind, "source_file": origin.get("source_file"), "source_sha256": origin.get("source_sha256")}
        if columns:
            row["column_units"] = columns
        key = cached_file, source_key
        if key in records and records[key]["unit"] != unit:
            raise ValueError(f"conflicting unit for {key}")
        records[key] = row
    def walk(value, route, cached_file, path, origin):
        if isinstance(value, dict):
            if value.get("representation") in {"numeric_csv", "complex_re_im", "retained_in_original_WXF"}:
                record(route, cached_file, value.get("source_key", path), value.get("unit"), value["representation"], origin)
            for key, child in value.items():
                walk(child, route, cached_file, path+"/"+str(key), origin)
        elif isinstance(value, list):
            for index, child in enumerate(value, 1):
                walk(child, route, cached_file, path+"/"+str(index), origin)
    for route, row in closure["routes"].items():
        meta = read(bundle / row["metadata"])
        rt = read(bundle / meta["numerical_roundtrip"])
        origin = {"source_file": rt["source_payload_path"], "source_sha256": rt["source_payload_sha256"]}
        walk(read(bundle / meta["data"]), route, meta["data"], "data", origin)
        index = read(bundle / meta["scalar_index"])
        for scalar in index["scalars"]:
            if scalar["kind"] != "numeric_scalar":
                continue
            record(route, scalar["cached_file"], scalar["source_key"], scalar["unit"], "numeric_scalar", scalar)
    result = {"schema_version": 1, "source_index_sha256": closure["source_index_sha256"], "created_at_UTC": now(), "solver_executed": False, "scope": "SI unit annotation clarification; no numeric alteration or physical acceptance upgrade", "rules": list(rules.values()), "overrides": list(records.values()), "audit": {"routes": len(closure["routes"]), "objects_scanned": dict(scanned), "override_count": len(records), "unqualified_key_counts": dict(unknown), "unknown_policy": "Unqualified model coordinates, mixed fields and unqualified tolerances retain explicit unspecified units; no inferred conversion."}}
    write(bundle / "unit_clarifications.json", result)
    return result


def derive(origin, final):
    if read(origin / "process_status.json", {}).get("process_exit_code") != 0:
        raise ValueError("origin exporter did not exit normally")
    final.mkdir(exist_ok=False)
    source_snapshot = final / "cache_derivation_source_snapshot" / "src"
    source_snapshot.mkdir(parents=True)
    shutil.copy2(Path(__file__), source_snapshot / Path(__file__).name)
    write(final / "run_manifest.json", {"snapshot_time": "before_final_cache_derivation", "source_index_sha256": read(origin / "closure_manifest.json")["source_index_sha256"], "origin_bundle": origin.relative_to(ROOT).as_posix(), "origin_manifest_sha256": digest(origin / "closure_manifest.json"), "origin_process_status_sha256": digest(origin / "process_status.json"), "sources": [{"path": "src/FinalizeClosureCache.py", "sha256": digest(Path(__file__))}], "original_63_route_conversion": "completed at origin; no repeated WXF conversion or solver", "notebook_build": "pending_unique_actual_build"})
    evidence = final / "source_export_evidence"
    evidence.mkdir()
    for name in ("source_index.json", "closure_manifest.json"):
        shutil.copy2(origin / name, final / name)
    for name in ("routes", "figdata"):
        shutil.copytree(origin / name, final / name)
    for name in ("source_snapshot", "processes", "archive_builder_source_snapshot"):
        if (origin / name).exists():
            shutil.copytree(origin / name, evidence / name)
    for name in ("run_manifest.json", "environment.json", "process_status.json", "export_process_status.json", "closure_verification.json", "archive_notebooks.json", "closure_manifest.json"):
        if (origin / name).exists():
            shutil.copy2(origin / name, evidence / name)
    shutil.copy2(origin / "environment.json", final / "environment.json")
    closure = read(final / "closure_manifest.json")
    normalization = []
    for route in ("analytic", "closure_analytic"):
        for name in ("data.json", "scalar_index.json"):
            path = final / "routes" / route / name
            before_hash = digest(path)
            text, changes = normalize_zeros(path.read_text(encoding="utf-8-sig"))
            if not changes:
                raise ValueError("expected the explicitly identified zero syntax repair")
            preserved = evidence / "normalization_originals" / path.relative_to(final)
            preserved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, preserved)
            path.write_text(text, encoding="utf-8", newline="")
            for asset in closure["routes"][route]["assets"]:
                if asset["path"] == path.relative_to(final).as_posix():
                    asset.update(sha256=digest(path), bytes=path.stat().st_size)
            normalization.append({"path": path.relative_to(final).as_posix(), "original_sha256": before_hash, "normalized_sha256": digest(path), "original_bytes_preserved_at": preserved.relative_to(final).as_posix(), "changes": changes, "numeric_value_changed": False})
    write(final / "closure_manifest.json", closure)
    write(final / "json_normalization.json", {"schema_version": 1, "operation": "standards-compliant decimal zero token spelling", "source_index_sha256": closure["source_index_sha256"], "origin_bundle": origin.relative_to(ROOT).as_posix(), "files": normalization, "solver_executed": False, "roundtrip_policy": "Original WXF and successful original numeric roundtrip unchanged; only malformed JSON zero token spelling corrected, exact Decimal zero identity verified."})
    units = unit_audit(final)
    return {"routes": len(closure["routes"]), "normalized_files": len(normalization), "unit_overrides": len(units["overrides"]), "unit_clarifications_sha256": digest(final / "unit_clarifications.json"), "solver_executed": False}


def derive_normalized(origin, final):
    """Preserve numeric evidence while replacing a failed display cache only."""
    if read(origin / "process_status.json", {}).get("process_exit_code") != 0:
        raise ValueError("origin static build actual exit evidence missing")
    closure = read(origin / "closure_manifest.json")
    units = read(origin / "unit_clarifications.json")
    if units["source_index_sha256"] != closure["source_index_sha256"]:
        raise ValueError("unit evidence belongs to another index")
    final.mkdir(exist_ok=False)
    snapshot = final / "cache_derivation_source_snapshot" / "src"
    snapshot.mkdir(parents=True)
    shutil.copy2(Path(__file__), snapshot / Path(__file__).name)
    write(final / "run_manifest.json", {"snapshot_time": "before_normalized_cache_COPY", "source_index_sha256": closure["source_index_sha256"], "origin_bundle": origin.relative_to(ROOT).as_posix(), "origin_manifest_sha256": digest(origin / "closure_manifest.json"), "origin_process_status_sha256": digest(origin / "process_status.json"), "origin_visual_scope": "native QA found inherited legacy GPU title mojibake; origin not accepted as complete display", "sources": [{"path": "src/FinalizeClosureCache.py", "sha256": digest(Path(__file__))}], "conversion_scope": "exact COPY of existing normalized data; no WXF import, numeric recalculation or physical solver", "notebook_build": "pending_unique_actual_build"})
    for name in ("source_index.json", "closure_manifest.json", "environment.json", "unit_clarifications.json", "json_normalization.json"):
        shutil.copy2(origin / name, final / name)
    for name in ("routes", "figdata", "source_export_evidence"):
        shutil.copytree(origin / name, final / name)
    prior = final / "derivation_origin_evidence"
    prior.mkdir()
    for name in ("run_manifest.json", "cache_derivation_process_status.json", "process_status.json", "archive_notebooks.json"):
        if (origin / name).exists():
            shutil.copy2(origin / name, prior / name)
    for route, row in closure["routes"].items():
        for asset in row["assets"]:
            target = final / asset["path"]
            if digest(target) != asset["sha256"]:
                raise ValueError(f"copied numerical cache SHA differs: {route}/{asset['path']}")
    write(final / "cache_copy_validation.json", {"passed": True, "source_index_sha256": digest(final / "source_index.json"), "origin_source_index_sha256": digest(origin / "source_index.json"), "routes": len(closure["routes"]), "assets_checked": sum(len(row["assets"]) for row in closure["routes"].values()), "unit_clarifications_sha256": digest(final / "unit_clarifications.json"), "origin_unit_clarifications_sha256": digest(origin / "unit_clarifications.json"), "solver_executed": False, "new_notebook_build": "pending"})
    return {"routes": len(closure["routes"]), "assets_rehashed": sum(len(row["assets"]) for row in closure["routes"].values()), "normalized_files_recomputed": 0, "unit_clarifications_sha256": digest(final / "unit_clarifications.json"), "solver_executed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--already-normalized", action="store_true")
    args = parser.parse_args()
    result = (derive_normalized if args.already_normalized else derive)(args.origin.resolve(), args.output.resolve())
    print(json.dumps(result))


if __name__ == "__main__":
    main()
