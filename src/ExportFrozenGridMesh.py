"""Export the exact Cartesian mesh topology of explicitly frozen RT0 fields.

This derives geometry from stored dimensions and validates every stored field
centre. It does not solve, interpolate fields, or invent vertex field values.
"""
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024**2), b""):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def export_case(case_path, destination):
    case = read(case_path)
    dims = case["dimensions"]
    width = float(case["cell_width_m"])
    field = case_path.parent / "cell_fields.csv"
    physics_path = case_path.parents[2] / "closure_rt0_parameters.json"
    physics = read(physics_path)
    sigma = float(physics["conductivity_S_per_m"])
    mu_r = float(physics["relative_permeability"])
    if len(dims) != 3 or any(not isinstance(n, int) or n < 1 for n in dims) or width <= 0:
        raise ValueError("Invalid frozen Cartesian dimensions")
    nx, ny, nz = dims
    expected = nx*ny*nz
    maximum_error = 0.
    with field.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.DictReader(stream)
        count = 0
        for count, (ijk, row) in enumerate(zip(itertools.product(range(nx), range(ny), range(nz)), rows, strict=True), 1):
            maximum_error = max(maximum_error, *(abs(float(row[name])-(index+.5)*width) for name, index in zip(("x_m", "y_m", "z_m"), ijk)))
    if count != expected or maximum_error > 1e-14:
        raise ValueError("Frozen field centres do not match the exact grid ordering")
    destination.mkdir(exist_ok=False)
    nodes = destination / "nodes_SI.csv"
    cells = destination / "hexahedra_materials.csv"
    node_id = lambda i, j, k: 1+(i*(ny+1)+j)*(nz+1)+k
    with nodes.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream);writer.writerow(("node_id", "x_m", "y_m", "z_m"))
        for i, j, k in itertools.product(range(nx+1), range(ny+1), range(nz+1)):
            writer.writerow((node_id(i,j,k), i*width, j*width, k*width))
    with cells.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("cell_id", *("node_"+str(i) for i in range(1,9)), "material_id", "conductivity_S_per_m", "relative_permeability", "cell_volume_m3"))
        for index, (i,j,k) in enumerate(itertools.product(range(nx), range(ny), range(nz)),1):
            corners = ((i,j,k),(i+1,j,k),(i+1,j+1,k),(i,j+1,k),(i,j,k+1),(i+1,j,k+1),(i+1,j+1,k+1),(i,j+1,k+1))
            writer.writerow((index, *(node_id(*p) for p in corners), 1, sigma, mu_r, width**3))
    record = {"case_id": case["case_id"], "source_run_id": case["run_id"], "dimensions": dims,
              "node_count": (nx+1)*(ny+1)*(nz+1), "cell_count": expected, "cell_width_m": width,
              "mesh_type": "Cartesian hexahedra; VTK corner order; original RT0 volume cells",
              "topology_source": "deterministically generated from frozen dimensions; checked against every original field centre",
              "material_scope": "original homogeneous copper block, not an inferred strand material assignment",
              "material_id_source": "generated ID1 from the original homogeneous single-material model",
              "field_scope": "original cell-centred RMS complex J and phi; no vertex interpolation or new field solve",
              "centre_order_maximum_error_m": maximum_error, "centre_order_tolerance_m": 1e-14,
              "source_files": [{"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p)} for p in (case_path,field,physics_path)],
              "assets": [{"path": p.name, "sha256": sha(p), "bytes": p.stat().st_size} for p in (nodes,cells)],
              "execution_status": "executed_data_export", "physical_acceptance_status": case["physical_acceptance_status"],
              "solver_executed": False, "units": "SI"}
    write(destination / "mesh_metadata.json",record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--reference-runs", required=True)
    args = parser.parse_args()
    out = args.output.resolve();out.mkdir(exist_ok=True)
    if (out / "results.json").exists():
        raise FileExistsError("Existing exported run is protected")
    records = []
    for rid in args.reference_runs.split(","):
        if not rid or Path(rid).name != rid or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in rid):
            raise ValueError("Explicit safe run IDs are required")
        paths = sorted((ROOT / "outputs" / rid / "cases").glob("*/case.json"))
        if not paths:
            raise ValueError("Missing frozen case in "+rid)
        for path in paths:
            records.append(export_case(path,out / (rid+"_"+path.parent.name)))
    write(out / "parameters.json", {"source_run_ids":args.reference_runs.split(","),"solver_executed":False,"units":"SI","schema_version":1})
    write(out / "results.json", {"run_id":out.name,"source_model":"frozen_RT0_grid_topology_export","execution_status":"executed_data_export","physical_acceptance_status":"not_applicable_data_export","data":{"mesh_exports":records},"solver_executed":False})
    write(out / "test_report.json", {"execution_status":"passed","tests":[{"id":r["case_id"]+"_all_field_centres_match_grid","execution_status":"passed","actual":r["centre_order_maximum_error_m"],"tolerance":1e-14,"source_model":"frozen_grid_identity"} for r in records]})
    write(out / "process_status.json", {"process_exit_code":0,"finished_UTC":datetime.now(timezone.utc).isoformat()})
    print(json.dumps({"run_id":out.name,"exported_cases":len(records),"solver_executed":False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
