#!/usr/bin/env python3
"""Export one deterministic, lightweight evidence manifest for the report and web app.

The exporter reads the explicitly pinned run index. It never chooses a run from
filesystem timestamps and it copies only small, reviewable assets into web/public.
"""
from __future__ import annotations

import hashlib
import argparse
from collections import Counter
import csv
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file() and (p / "configs/reference_parameters.json").is_file())
INDEX = ROOT / "docs" / "总控" / "当前运行索引.json"
OUT = ROOT / "web" / "public" / "data"
REPORT_OUT = ROOT / "docs" / "report" / "运行索引.json"

STATUS_VALUES = {
    "passed", "passed_test_scope_only", "executed", "failed", "failed_numerical",
    "failed_process_exit", "blocked_environment_resource_budget", "not_run", "unknown",
    "constructed", "running", "not_verified", "not_tested", "blocked",
    "passed_scalar_validation_fields_unavailable", "failed_interface_or_solver",
    "stopped_resource_or_time_budget", "not_completed_time_budget"
}

VALIDATION_FIELDS = ("scalar_validation_status", "full_physical_acceptance", "full_physical_acceptance_status",
                     "scientific_execution_status", "scientific_acceptance_status")


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unavailable"


def compact_metrics(value: Any, limit: int | None = None) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, Any] = {}
    for key, item in value.items():
        if limit is not None and len(result) >= limit:
            break
        if isinstance(item, (int, float, str, bool)) or item is None:
            result[str(key)] = item
    return result


def effective_physics(parameters: Any) -> dict[str, Any]:
    """Use saved route parameters; an imposed-field case supersedes wrapper 20 A."""
    if not isinstance(parameters, dict):
        return {}
    keys = {"frequency_Hz": "frequency_hz", "conductivity_S_per_m": "conductivity_s_per_m",
            "relative_permeability": "relative_permeability", "temperature_C": "temperature_c",
            "phasor": "phasor_convention", "uniform_external_Bz_RMS_T": "uniform_external_Bz_rms_t",
            "excitation": "excitation", "Rac_from_P_over_I2": "Rac_from_P_over_I2"}
    result = {target: parameters[key] for key, target in keys.items() if key in parameters}
    current = next((parameters[key] for key in ("net_transport_current_RMS_A", "total_current_RMS_A", "current_RMS_A")
                    if key in parameters), None)
    if current is not None:
        result["total_current_rms_a"] = current
    if "net_transport_current_RMS_A" in parameters:
        result["net_transport_current_rms_a"] = parameters["net_transport_current_RMS_A"]
        result["excitation"] = "independent_imposed_field_zero_net_transport"
        result["Rac_from_P_over_I2"] = "not_applicable; loss is absorbed field power"
    return public_value(result)


def public_value(value: Any) -> Any:
    """Keep public numerical evidence free of credentials and local machine paths."""
    if isinstance(value, dict):
        if isinstance(value.get("source_key"), str) and re.search(
                r"password|token|secret|credential|license|username|user_name|machine_name|hostname", value["source_key"], re.I):
            value = {**value, "value": "[private metadata omitted]"}
        return {str(k): public_value(v) for k, v in value.items()
                if not re.search(r"password|token|secret|credential|license|username|user_name|machine_name|hostname", str(k), re.I)}
    if isinstance(value, list):
        return [public_value(v) for v in value]
    if isinstance(value, str) and re.search(r"(?:[A-Za-z]:[\\/]|\\\\[^\\]+\\|/(?:Users|home)/)", value):
        return "[local machine path omitted]"
    return value


def public_environment(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    allowed = {"WolframVersion", "SystemID", "paclets", "ProcessorCount", "frontend_connected",
               "notebooks_supported", "thread_options", "timestamp_UTC", "execution_status",
               "elapsed_seconds", "gpu", "cpu", "logical_processors", "ram_bytes",
               "CUDA_version", "driver_version", "SDK_version"}
    return public_value({k: v for k, v in value.items() if k in allowed})


def public_cache_references(value: Any, run_id: str, namespace: str | None = None) -> Any:
    if isinstance(value, dict):
        result = {key: public_cache_references(item, run_id, namespace) for key, item in value.items()}
        for key in ("path", "cached_file", "coordinate_reference", "marker_reference"):
            relative = result.get(key)
            if isinstance(relative, str) and relative.startswith("routes/"):
                prefix = Path("cache") / namespace if namespace else Path("cache")
                result[key] = (Path("/assets") / run_id / prefix / Path(*Path(relative).parts[2:])).as_posix()
        return result
    if isinstance(value, list):
        return [public_cache_references(item, run_id, namespace) for item in value]
    return value


def load_unit_overrides(bundle: Path | None) -> dict:
    if bundle is None or not (bundle / "unit_clarifications.json").exists():
        return {}
    from VerifyClosureEvidence import contained
    evidence = read_json(bundle / "unit_clarifications.json")
    if evidence.get("source_index_sha256") != sha256(bundle / "source_index.json"):
        raise ValueError("unit override index hash differs")
    records, hashes = {}, {}
    for row in evidence["overrides"]:
        path = row["cached_file"]
        if path not in hashes:
            hashes[path] = sha256(contained(bundle, path))
        if hashes[path] != row["original_cached_file_sha256"]:
            raise ValueError("unit override source cache hash differs")
        records.setdefault(path, {})[row["source_key"]] = row
    return records


def apply_unit_overrides(value: Any, cached_file: str, overrides: dict, prefix: str = "data") -> Any:
    """Clarify public labels without changing the preserved cache or values."""
    if isinstance(value, dict):
        result = {key: apply_unit_overrides(item, cached_file, overrides, prefix+"/"+str(key)) for key, item in value.items()}
        key = value.get("source_key", prefix)
        record_file = value.get("cached_file", cached_file)
        row = overrides.get(record_file, {}).get(key)
        representation = value.get("representation")
        if row and ((isinstance(representation, str) and representation in {"numeric_csv", "complex_re_im", "retained_in_original_WXF"}) or value.get("kind") == "numeric_scalar"):
            result["unit"] = row["unit"]
            result["unit_clarification_rule"] = row["rule_id"]
            for extra in ("column_units", "component_units"):
                if extra in row:
                    result[extra] = row[extra]
        return result
    if isinstance(value, list):
        return [apply_unit_overrides(item, cached_file, overrides, prefix+"/"+str(index)) for index, item in enumerate(value, 1)]
    return value


def status_for(route: str, pin: dict[str, Any], result: Any, process: Any) -> tuple[str, str, str | None]:
    execution = str(pin.get("execution_status") or "")
    physical = str(pin.get("physical_acceptance_status") or "")
    failure = pin.get("failure_reason")
    if isinstance(process, dict) and process.get("process_exit_code") not in (None, 0):
        execution = "failed_process_exit"
        failure = failure or "process_exit_code_" + str(process.get("process_exit_code"))
    if not execution and isinstance(result, dict):
        execution = str(result.get("execution_status") or "")
    if not execution:
        if isinstance(result, dict) and result.get("failure"):
            execution = "failed"
            failure = failure or str(result.get("failure"))
        elif result is not None:
            execution = "executed"
        else:
            execution = "not_run"
    if not physical:
        physical = "not_run" if execution == "not_run" else "unknown"
    # Scientific campaigns record scope-specific tokens. Preserve legitimate status
    # strings rather than silently erasing them when a new route is explicitly pinned.
    valid = execution in STATUS_VALUES or bool(re.fullmatch(r"[a-z][a-z0-9_]{0,127}", execution))
    return execution if valid else "unknown", physical, failure


def asset_record(path: Path, root_relative: str, caption_id: str | None = None, source_run_id: str | None = None) -> dict[str, Any]:
    return {
        "path": root_relative.replace("\\", "/"),
        "sha256": sha256(path),
        "media_type": {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".csv": "text/csv", ".json": "application/json", ".html": "text/html"}.get(path.suffix.lower(), "application/octet-stream"),
        "caption_id": caption_id,
        "source_run_id": source_run_id,
    }


def copy_assets(run_id: str, run_dir: Path, closure_bundle: Path | None = None, closure_row: dict[str, Any] | None = None,
                *, clear_target: bool = True, cache_namespace: str | None = None, unit_overrides: dict | None = None) -> list[dict[str, Any]]:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Invalid pinned run_id")
    asset_root = (ROOT / "web" / "public" / "assets").resolve()
    target = (asset_root / run_id).resolve()
    if not target.is_relative_to(asset_root) or target == asset_root:
        raise ValueError("public asset target escapes the workspace asset directory")
    assets: list[dict[str, Any]] = []
    if clear_target and target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    candidates = []
    figures = run_dir / "figures"
    if figures.exists():
        candidates.extend(sorted(p for p in figures.rglob("*") if p.suffix.lower() in {".svg", ".png", ".jpg", ".jpeg"}))
    for name in ("results.json", "test_report.json", "parameters.json", "environment.json", "resource_curve.csv"):
        p = run_dir / name
        if p.exists():
            candidates.append(p)
    for source in candidates:
        relative = source.relative_to(run_dir)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix.lower() == ".json":
            value = read_json(source)
            if value is None:
                raise ValueError(f"Invalid source JSON: {source.name}")
            value = public_environment(value) if source.name == "environment.json" else public_value(value)
            destination.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        elif source.suffix.lower() == ".csv":
            with source.open(encoding="utf-8-sig", newline="") as src, destination.open("w", encoding="utf-8", newline="") as dst:
                writer = csv.writer(dst)
                writer.writerows([public_value(v) for v in row] for row in csv.reader(src))
        else:
            shutil.copy2(source, destination)
        public_path = Path("/assets") / run_id / relative
        assets.append(asset_record(destination, str(public_path), source.stem, run_id))
    if closure_bundle is not None and closure_row is not None:
        from VerifyClosureEvidence import contained
        for cached in closure_row.get("assets", []):
            if cached.get("kind") == "preserved_unparseable_original":
                continue
            source = contained(closure_bundle, cached["path"])
            if not source.is_file() or sha256(source) != cached["sha256"]:
                raise ValueError(f"Missing or changed closure asset: {cached['path']}")
            parts = Path(cached["path"]).parts
            cache_prefix = Path("cache") / cache_namespace if cache_namespace else Path("cache")
            relative = cache_prefix / Path(*parts[2:]) if len(parts) >= 3 and parts[0] == "routes" else cache_prefix / source.name
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.suffix.lower() == ".json":
                value = read_json(source)
                if value is None:
                    raise ValueError(f"Invalid cached JSON: {cached['path']}")
                value = apply_unit_overrides(value, cached["path"], unit_overrides or {})
                # Turn bundle-relative numerical references into public asset references.
                destination.write_text(json.dumps(public_value(public_cache_references(value, run_id, cache_namespace)), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
            elif source.suffix.lower() == ".csv":
                with source.open(encoding="utf-8-sig", newline="") as src, destination.open("w", encoding="utf-8", newline="") as dst:
                    writer = csv.writer(dst)
                    writer.writerows([public_value(v) for v in row] for row in csv.reader(src))
            elif source.suffix.lower() in {".svg", ".png", ".jpg", ".jpeg"}:
                shutil.copy2(source, destination)
            else:
                continue
            public_path = Path("/assets") / run_id / relative
            assets.append(asset_record(destination, str(public_path), source.stem, run_id))
    return assets


def build(closure_bundle: Path | None = None) -> dict[str, Any]:
    unit_overrides = load_unit_overrides(closure_bundle)
    closure_manifest = read_json(closure_bundle / "closure_manifest.json") if closure_bundle else None
    index_path = closure_bundle / "source_index.json" if closure_bundle else INDEX
    index = read_json(index_path) or {}
    if closure_bundle and (not isinstance(closure_manifest, dict) or sha256(index_path) != closure_manifest.get("source_index_sha256")):
        raise ValueError("Missing or mismatched frozen closure index")
    routes: list[dict[str, Any]] = []
    assets: list[dict[str, Any]] = []
    pinned_rows = index.get("routes") or {}
    run_counts = Counter(p.get("selected_run_id") for p in pinned_rows.values() if isinstance(p, dict))
    copied_runs: set[str] = set()
    for route, pin in (index.get("routes") or {}).items():
        pin = pin if isinstance(pin, dict) else {}
        run_id = pin.get("selected_run_id")
        run_dir = ROOT / "outputs" / str(run_id) if run_id else ROOT / "outputs" / "missing"
        result = read_json(run_dir / "results.json")
        test_report = read_json(run_dir / "test_report.json")
        process = read_json(run_dir / "process_status.json")
        execution, physical, failure = status_for(route, pin, result, process)
        if not pin.get("physical_acceptance_status") and isinstance(test_report, dict) and test_report.get("execution_status") == "passed" and not physical.startswith("failed"):
            physical = "passed_test_scope_only"
        if not pin.get("physical_acceptance_status") and isinstance(test_report, dict) and test_report.get("execution_status") in {"failed", "not_run", "blocked"}:
            physical = test_report.get("execution_status")
        checks = []
        if isinstance(test_report, dict):
            checks = test_report.get("tests") or test_report.get("checks") or []
            if isinstance(checks, dict):
                checks = [{"name": k, "value": v} for k, v in checks.items()]
            if not isinstance(checks, list):
                checks = []
        closure_row = (closure_manifest.get("routes") or {}).get(route) if closure_manifest else None
        if closure_bundle and (not closure_row or closure_row.get("run_id") != run_id):
            raise ValueError(f"No exact cached export for pinned route: {route}")
        route_assets = copy_assets(str(run_id), run_dir, closure_bundle, closure_row,
                                   clear_target=run_id not in copied_runs,
                                   cache_namespace=route if run_counts[run_id] > 1 else None, unit_overrides=unit_overrides) if run_id and run_dir.exists() else []
        if run_id:
            copied_runs.add(run_id)
        assets.extend(route_assets)
        metrics = compact_metrics(pin.get("metrics", {}))
        numerical_cases = []
        route_physics = effective_physics(read_json(run_dir / "parameters.json"))
        scalar_coverage = None
        validation = {k: pin.get(k, (result or {}).get(k)) for k in VALIDATION_FIELDS
                      if k in pin or (isinstance(result, dict) and k in result)}
        metrics.update(compact_metrics((result or {}).get("metrics") if isinstance(result, dict) else {}))
        if isinstance(result, dict):
            metrics.update({k: result[k] for k in ("elapsed_seconds", "check_count", "failed_checks") if k in result})
        if closure_bundle and closure_row:
            from VerifyClosureEvidence import contained
            cached_meta = read_json(contained(closure_bundle, closure_row["metadata"])) or {}
            cached_data = read_json(contained(closure_bundle, cached_meta["data"]))
            if cached_data is None:
                raise ValueError(f"Missing numerical cache for route: {route}")
            cached_data = apply_unit_overrides(cached_data, cached_meta["data"], unit_overrides)
            metrics.update(compact_metrics(cached_meta.get("metrics", {})))
            metrics.update(compact_metrics(cached_data))
            route_physics = effective_physics(cached_meta.get("effective_parameters")) or route_physics
            scalar_asset = next((asset for asset in route_assets if asset["path"].endswith("/scalar_index.json")), None)
            if scalar_asset:
                scalar_coverage = {"path": scalar_asset["path"], "sha256": scalar_asset["sha256"],
                                   "scalar_count": cached_meta.get("scalar_count"),
                                   "scope": "complete scalar leaves with exact original source hashes; arrays reference complete cached data"}
            cases = cached_data.get("cases", []) if isinstance(cached_data, dict) else []
            if isinstance(cases, list) and cases and isinstance(cases[-1], dict):
                metrics.update(compact_metrics(cases[-1]))
            numerical_cases = public_cache_references(cases, run_id, route if run_counts[run_id] > 1 else None) if isinstance(cases, list) else []
            # Keep every recursive case/scalar JSON as an attributable case record.
            # Do not flatten several sensitivity cases into a single implied result.
            for asset in closure_row.get("assets", []):
                if asset.get("kind") != "preserved_custom_data" or not asset["path"].lower().endswith(".json"):
                    continue
                value = read_json(contained(closure_bundle, asset["path"]))
                if not isinstance(value, dict):
                    continue
                source_relative = asset.get("source_relative_path", asset["path"])
                scope = {k: value[k] for k in VALIDATION_FIELDS if k in value}
                scalars = compact_metrics(value)
                if scalars or scope:
                    numerical_cases.append({"source_relative_path": source_relative,
                                            "source_sha256": asset.get("sha256"),
                                            "metrics": public_value(scalars),
                                            "validation_scopes": public_value(scope)})
            validation.update({k: cached_meta[k] for k in VALIDATION_FIELDS if k in cached_meta})
        routes.append({
            "route": route,
            "run_id": run_id,
            "source_model": (result or {}).get("source_model") if isinstance(result, dict) and (result or {}).get("source_model") else pin.get("source_model"),
            "execution_status": execution,
            "physical_acceptance_status": physical,
            "process_exit": process.get("process_exit_code", pin.get("process_exit")) if isinstance(process, dict) else pin.get("process_exit"),
            "process_evidence": public_value(pin.get("process_evidence")),
            "physics": route_physics,
            "scalar_coverage": scalar_coverage,
            "unit_overrides": public_cache_references([record for per_file in unit_overrides.values() for record in per_file.values() if record["route"] == route], run_id, route if run_counts[run_id] > 1 else None),
            "failure_reason": failure,
            "metrics": public_value(metrics),
            "checks": checks,
            "validation_scopes": public_value(validation),
            "numerical_cases": public_value(numerical_cases),
            "figures": [a for a in route_assets if a["media_type"].startswith("image/")],
            "files": route_assets,
        })
    physics = {
        "scope": "reference transport case; route physics supersedes this reference for imposed-field and custom cases",
        "units": "SI",
        "phasor_convention": "exp(+j omega t)",
        "current_type": "RMS",
        "frequency_hz": 200000,
        "total_current_rms_a": 20,
        "conductivity_s_per_m": 5.8e7,
        "relative_permeability": 1,
        "temperature_c": 20,
        "q2_min_copper_area_mm2": 5,
    }
    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_commit": git_commit(),
        "selection_policy": index.get("selection_policy", "explicit run_id"),
        "physics": physics,
        "routes": routes,
        "notebooks": [{"path": f"notebooks/{p.name}", "media_type": "application/vnd.wolfram.nb", "sha256": sha256(p), "bytes": p.stat().st_size} for p in sorted((ROOT / "notebooks").glob("*.nb"))],
        "assets": assets,
        "glossary_version": "2026-10-05",
    }
    if closure_manifest:
        manifest["closure_source_index_sha256"] = closure_manifest["source_index_sha256"]
        manifest["closure_export_scope"] = "archived numerical conversion; original physical acceptance retained"
        if unit_overrides:
            manifest["unit_clarifications"] = {"scope": "unit labels clarified from exact cached source keys; values and physical scope unchanged", "source_sha256": sha256(closure_bundle / "unit_clarifications.json"), "override_count": sum(len(items) for items in unit_overrides.values())}
    return public_value(manifest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--closure-bundle", type=Path, default=Path(os.environ["LITZ_CLOSURE_EXPORT_DIR"]) if os.environ.get("LITZ_CLOSURE_EXPORT_DIR") else None)
    args = parser.parse_args()
    manifest = build(args.closure_bundle)
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    (OUT / "manifest.json").write_text(text, encoding="utf-8")
    preview = ROOT / "outputs" / "3d_20261005_site" / "preview.json"
    if preview.exists():
        shutil.copy2(preview, OUT / "geometry-preview.json")
    REPORT_OUT.write_text(text, encoding="utf-8")
    print(json.dumps({"routes": len(manifest["routes"]), "assets": len(manifest["assets"]), "output": str(OUT / "manifest.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
