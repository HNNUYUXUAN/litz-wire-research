"""CPU-only frozen evidence reader and elementary SI parameter exploration.

Uses only the Python standard library. No Wolfram, FEM, Ansys or GPU process is
started. AC Bessel calibration is provided separately by the Wolfram entry point.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024**2), b""):
            h.update(block)
    return h.hexdigest()


def contained(folder, relative):
    path = (folder / relative).resolve()
    if not path.is_relative_to(folder.resolve()):
        raise ValueError("Cache reference escapes its bundle")
    return path


def topology_supplements(bundle, manifest, route, entry, data_path):
    """Expose verified CSV references without expanding millions of node IDs."""
    assets = {item["path"]: item for item in entry["assets"]}
    checked = set()
    def verified(path, expected_sha=None):
        if path not in assets:
            raise ValueError("Topology reference absent from route assets: " + path)
        if expected_sha and expected_sha != assets[path]["sha256"]:
            raise ValueError("Conflicting topology SHA: " + path)
        if path not in checked:
            if sha(contained(bundle, path)) != assets[path]["sha256"]:
                raise ValueError("Missing or changed topology attachment: " + path)
            checked.add(path)
        return path
    records = []
    for supplement in manifest.get("supplements", []):
        if supplement["route"] != route:
            continue
        path = verified(supplement["manifest"])
        payload = read(contained(bundle, path))
        if payload["source_index_sha256"] != manifest["source_index_sha256"] or payload["route"] != route:
            raise ValueError("Topology supplement belongs to a different frozen route")
        if payload["original_data_sha256"] != assets[data_path]["sha256"]:
            raise ValueError("Topology supplement refers to different cached data")
        arrays = []
        for item in payload["arrays"]:
            exported = dict(item)
            exported["path"] = verified(item["path"], item["sha256"])
            for key in ("coordinate_reference", "marker_reference"):
                exported[key] = verified(item[key])
            arrays.append(exported)
        records.append({"manifest":path, "manifest_sha256":assets[path]["sha256"],
                        "run_id":payload["run_id"], "source_run_id":payload["source_run_id"],
                        "execution_status":payload["execution_status"],
                        "physical_acceptance_status":payload["physical_acceptance_status"],
                        "arrays":arrays, "path_base":"bundle_root", "solver_executed":False})
    return records


def view(bundle):
    index = read(bundle / "source_index.json")
    manifest = read(bundle / "closure_manifest.json")
    if manifest["source_index_sha256"] != sha(bundle / "source_index.json"):
        raise ValueError("Frozen source index hash differs")
    if set(index["routes"]) != set(manifest["routes"]):
        raise ValueError("Missing frozen routes; no recomputation fallback")
    clarifications_path = bundle / "unit_clarifications.json"
    clarifications = read(clarifications_path) if clarifications_path.is_file() else {}
    if clarifications and clarifications["source_index_sha256"] != manifest["source_index_sha256"]:
        raise ValueError("Unit clarifications refer to a different frozen source index")
    overrides = clarifications.get("overrides", [])
    checked_override_sources = set()
    for item in overrides:
        original = (item["cached_file"], item["original_cached_file_sha256"])
        if original not in checked_override_sources:
            if sha(contained(bundle, original[0])) != original[1]:
                raise ValueError("Unit clarification source changed: " + original[0])
            checked_override_sources.add(original)
    def clarified(value, key, units):
        if isinstance(value, dict):
            result = {name: clarified(item, key+"/"+name, units) for name,item in value.items()}
            source_key = result.get("source_key", key)
            if "unit" in result and source_key in units:
                result.update(units[source_key])
            return result
        if isinstance(value, list):
            return [clarified(item, key+"/"+str(number), units) for number,item in enumerate(value, 1)]
        return value
    rows = []
    for route, entry in manifest["routes"].items():
        metadata_path = contained(bundle, entry["metadata"])
        metadata = read(metadata_path)
        assets = {item["path"]: item for item in entry["assets"]}
        for key in (entry["metadata"], metadata["data"]):
            if key not in assets or sha(contained(bundle, key)) != assets[key]["sha256"]:
                raise ValueError("Missing or changed frozen scalar metadata: " + route)
        record = {key: metadata.get(key) for key in (
            "route", "run_id", "source_model", "execution_status", "physical_acceptance_status",
            "process_exit", "metrics", "effective_parameters")}
        route_overrides = [item for item in overrides if item["route"] == route]
        units = {item["source_key"]:{key:item[key] for key in ("unit", "column_units", "component_units") if key in item}
                 for item in route_overrides if item["cached_file"] == metadata["data"]}
        record["frozen_data"] = clarified(read(contained(bundle, metadata["data"])), "data", units)
        record["effective_unit_overrides"] = route_overrides
        record["unit_policy"] = "Explicit clarification overrides precede archived annotations; unspecified source units remain unspecified."
        record["topology_supplements"] = topology_supplements(bundle, manifest, route, entry, metadata["data"])
        rows.append(record)
    return {"source_model": "frozen_JSON_evidence_reader", "execution_status": "executed_cache_read",
            "source_index_sha256": manifest["source_index_sha256"], "route_count": len(rows),
            "routes": rows, "physical_solver_executed": False, "GPU_used": False}


def analytic(diameter_m, frequency_Hz, current_RMS_A, conductivity):
    if not all(math.isfinite(v) for v in (diameter_m, frequency_Hz, current_RMS_A, conductivity)):
        raise ValueError("Finite SI inputs required")
    if min(diameter_m, frequency_Hz, conductivity) <= 0 or current_RMS_A < 0:
        raise ValueError("Diameter, positive frequency and conductivity required; RMS current cannot be negative")
    area = math.pi * (diameter_m / 2)**2
    rdc = 1 / (conductivity * area)
    return {"source_model": "elementary_round_wire_DC_and_skin_depth_analytic",
            "execution_status": "executed_light_CPU_analytic",
            "physical_acceptance_status": "analytic_formula_scope_only",
            "inputs_SI": {"diameter_m": diameter_m, "frequency_Hz": frequency_Hz,
                "current_RMS_A": current_RMS_A, "conductivity_S_per_m": conductivity, "relative_permeability": 1},
            "area_m2": area, "Rdc_ohm_per_axial_m": rdc,
            "Jdc_A_per_m2": current_RMS_A / area, "DC_Joule_loss_W_per_axial_m": current_RMS_A**2 * rdc,
            "skin_depth_m": math.sqrt(1 / (math.pi * frequency_Hz * 4*math.pi*1e-7 * conductivity)),
            "scope": "SI; RMS; mu_r1; straight isolated cylinder; DC resistance/loss and skin depth only; AC Rac requires the separate Bessel entry.",
            "physical_solver_executed": False, "GPU_used": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("view", "analytic"), default="view")
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--diameter-m", type=float, default=.002)
    parser.add_argument("--frequency-hz", type=float, default=200000)
    parser.add_argument("--current-rms-a", type=float, default=20)
    parser.add_argument("--conductivity", type=float, default=5.8e7)
    args = parser.parse_args()
    start = time.perf_counter()
    if args.mode == "view" and not args.bundle:
        parser.error("--bundle is required for cache reading")
    result = view(args.bundle.resolve()) if args.mode == "view" else analytic(
        args.diameter_m, args.frequency_hz, args.current_rms_a, args.conductivity)
    result.update(python_version=sys.version, elapsed_seconds=time.perf_counter()-start,
                  entry_source_sha256=sha(Path(__file__)))
    text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+"\n"
    if args.output:
        if args.output.exists():
            raise FileExistsError("Existing output is protected")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(json.dumps({"execution_status":result["execution_status"], "source_model":result["source_model"],
                     "route_count":result.get("route_count"), "physical_solver_executed":False, "GPU_used":False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
