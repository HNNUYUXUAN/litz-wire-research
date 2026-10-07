"""Generate, screen and archive geometric Litz candidates; no field solver.

The clearance certificate is global in three dimensions. If every pair at the
same axial coordinate is separated by at least g and each transverse path has
Lipschitz constant <= M, then for any z,w its Euclidean separation is at least
g/sqrt(1+M*M). This follows by minimizing (g-M*abs(z-w))**2+(z-w)**2;
when abs(z-w)>=g/M the axial separation alone is sufficient. Circular tube
surfaces therefore have clearance >= that lower bound minus copper diameter.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import traceback

import numpy as np


MODEL = "analytic_geometric_trajectories_only"
LOCAL_TZ = timezone(timedelta(hours=8))


def save_json(path, value):
    def native(item):
        if isinstance(item, np.generic):
            return item.item()
        raise TypeError(f"Unsupported JSON value: {type(item).__name__}")
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=native), encoding="utf-8")


def hamilton_cycle(rows, columns):
    if rows % 2 or columns < 2:
        raise ValueError("An even row count and at least two columns are required.")
    indices = [(0, 0)]
    for row in range(rows):
        cols = range(1, columns) if row % 2 == 0 else range(columns - 1, 0, -1)
        indices.extend((row, col) for col in cols)
    indices.append((rows - 1, 0))
    indices.extend((row, 0) for row in range(rows - 2, 0, -1))
    array = np.asarray(indices, dtype=int)
    if len(array) != rows * columns or len(np.unique(array, axis=0)) != len(array):
        raise AssertionError("Hamilton cycle must visit every grid point once.")
    if not np.all(np.abs(np.roll(array, -1, axis=0) - array).sum(axis=1) == 1):
        raise AssertionError("Every Hamilton edge, including closure, must be adjacent.")
    return array


def rotate(vectors, angles):
    c, s = np.cos(angles)[:, None], np.sin(angles)[:, None]
    x, y = vectors[..., 0], vectors[..., 1]
    return np.stack((c * x - s * y, s * x + c * y), axis=-1)


class Candidate:
    def __init__(self, config, count, family, pitch_ratio):
        self.config, self.count, self.family = config, count, family
        self.rows, self.columns = config["strand_grids"][str(count)]
        self.diameter = config["reference_diameter_m"] * math.sqrt(config["reference_strands"] / count)
        self.spacing = config["slot_spacing_over_d"] * self.diameter
        self.cycle_indices = hamilton_cycle(self.rows, self.columns)
        self.slots = self.spacing * np.column_stack((self.cycle_indices[:, 1] - (self.columns - 1) / 2,
                                                    self.cycle_indices[:, 0] - (self.rows - 1) / 2))
        self.pitch_ratio = pitch_ratio
        self.pitch = pitch_ratio * count * self.diameter
        self.step_length = self.pitch / count
        self.edges = np.roll(self.slots, -1, axis=0) - self.slots
        # Subbundle centres preserve the same initial square slots. Their
        # spacing is 2*slot_spacing, with four local corners in every group.
        group_xy = np.column_stack((self.cycle_indices[:, 1] // 2 * 2 + .5,
                                    self.cycle_indices[:, 0] // 2 * 2 + .5))
        group_xy -= np.array([(self.columns - 1) / 2, (self.rows - 1) / 2])
        self.groups = group_xy * self.spacing
        self.inner = self.slots - self.groups
        self.name = f"N{count}_{family}" + ("" if family == "straight" else f"_P{int(pitch_ratio)}Nd")

    def evaluate(self, z):
        """Return transverse position, first and second axial derivatives."""
        z = np.asarray(z, dtype=float).reshape(-1)
        if self.family == "straight":
            shape = (len(z), self.count, 2)
            return np.broadcast_to(self.slots, shape).copy(), np.zeros(shape), np.zeros(shape)
        if self.family == "hamilton_crosslayer":
            phase = z / self.step_length
            index = np.floor(phase).astype(np.int64)
            t = phase - index
            q = t**3 * (10 + t * (-15 + 6 * t))
            dq = 30 * t**2 * (1 - t)**2 / self.step_length
            ddq = 60 * t * (1 - t) * (1 - 2 * t) / self.step_length**2
            slot = (index[:, None] + np.arange(self.count)) % self.count
            starts, edges = self.slots[slot], self.edges[slot]
            return starts + q[:, None, None] * edges, dq[:, None, None] * edges, ddq[:, None, None] * edges
        omega = 2 * math.pi / self.pitch
        if self.family == "single":
            a = rotate(self.slots, omega * z)
            return a, omega * np.stack((-a[..., 1], a[..., 0]), axis=-1), -omega**2 * a
        turns = self.config["subbundle_relative_turns_per_outer_turn"]
        sign = 1 if self.family == "multilevel_same" else -1
        omega_inner = (1 + sign * turns) * omega
        outer, inner = rotate(self.groups, omega * z), rotate(self.inner, omega_inner * z)
        position = outer + inner
        velocity = np.stack((-omega * outer[..., 1] - omega_inner * inner[..., 1],
                              omega * outer[..., 0] + omega_inner * inner[..., 0]), axis=-1)
        return position, velocity, -omega**2 * outer - omega_inner**2 * inner

    def certificate(self):
        omega = 2 * math.pi / self.pitch
        roundoff = 128 * np.finfo(float).eps * max(np.linalg.norm(self.slots, axis=1))
        if self.family == "hamilton_crosslayer":
            # For all distinct directed edges, displacement between simultaneous
            # moving points is a+b*q. Its squared norm is quadratic in q.
            first, second = np.triu_indices(self.count, 1)
            a, b = self.slots[first] - self.slots[second], self.edges[first] - self.edges[second]
            bb = np.sum(b * b, axis=1)
            q = np.divide(-np.sum(a * b, axis=1), bb, out=np.zeros_like(bb), where=bb > 0)
            q = np.clip(q, 0., 1.)
            same_z = float(np.min(np.linalg.norm(a + q[:, None] * b, axis=1))) - roundoff
            speed = self.spacing * (15 / 8) / self.step_length
            acceleration = self.spacing * (10 / math.sqrt(3)) / self.step_length**2
            method = "all_edge_pair_quadratic_minimum_plus_global_Lipschitz_3D_bound"
        elif self.family == "straight":
            same_z, speed, acceleration = self.spacing - roundoff, 0., 0.
            method = "parallel_straight_tubes_exact_separation"
        elif self.family == "single":
            radius = float(np.max(np.linalg.norm(self.slots, axis=1)))
            same_z, speed, acceleration = self.spacing - roundoff, omega * radius, omega**2 * radius
            method = "rotation_preserved_same_z_gap_plus_global_Lipschitz_3D_bound"
        else:
            rgroup, rinner = float(np.max(np.linalg.norm(self.groups, axis=1))), math.sqrt(2) * self.spacing / 2
            factor = 1 + (1 if self.family == "multilevel_same" else -1) * self.config["subbundle_relative_turns_per_outer_turn"]
            # Within a 2x2 group, distances rotate rigidly. Between groups the
            # triangle inequality gives centre spacing minus two local radii.
            same_z = min(self.spacing, 2 * self.spacing - 2 * rinner) - roundoff
            speed = omega * rgroup + abs(factor) * omega * rinner
            acceleration = omega**2 * rgroup + factor**2 * omega**2 * rinner
            method = "subbundle_triangle_inequality_plus_global_Lipschitz_3D_bound"
        distance = same_z / math.sqrt(1 + speed**2)
        # For r(z)=(x(z),y(z),z), curvature <= |r''(z)| because
        # |r'|>=1. This conservative radius bound is uniform along the curve.
        radius = None if acceleration == 0 else 1 / acceleration
        gap = distance - self.diameter
        return {"execution_status": "certified_analytic_lower_bound", "method": method,
                "same_z_centre_distance_lower_bound_m": same_z,
                "transverse_slope_upper_bound": speed,
                "continuous_3D_centre_distance_lower_bound_m": distance,
                "continuous_3D_surface_gap_lower_bound_m": gap,
                "curvature_radius_lower_bound_m": radius,
                "curvature_is_zero": acceleration == 0,
                "gap_screen_passed": gap >= self.config["minimum_surface_gap_over_d"] * self.diameter,
                "curvature_screen_passed": radius is None or radius >= self.config["minimum_curvature_radius_over_d"] * self.diameter,
                "floating_point_margin_m": roundoff,
                "certificate_scope": "nominal circular copper tubes around analytic centreline; no enamel, tension, fatigue or machine certification"}

    def lengths(self, length, order):
        nodes, weights = np.polynomial.legendre.leggauss(order)
        if self.family == "straight":
            return np.full(self.count, length)
        if self.family == "hamilton_crosslayer":
            complete = int(math.floor(length / self.step_length))
            remainder = length - complete * self.step_length
            def step_arc(end):
                t = (nodes + 1) * end / (2 * self.step_length)
                slope = self.spacing * 30 * t**2 * (1-t)**2 / self.step_length
                return float(np.dot(weights, np.sqrt(1+slope*slope)) * end / 2)
            return np.full(self.count, complete * step_arc(self.step_length) + step_arc(remainder))
        # Resolve both whole-bundle and inner rotations, using independent
        # Gauss orders for the saved numerical error estimate.
        intervals = max(64, int(math.ceil(length / self.pitch * 64)))
        ends = np.linspace(0, length, intervals + 1)
        total = np.zeros(self.count)
        for start, end in zip(ends[:-1], ends[1:]):
            z = start + (nodes + 1) * (end-start) / 2
            velocity = self.evaluate(z)[1]
            total += weights @ np.sqrt(1 + np.sum(velocity**2, axis=-1)) * (end-start) / 2
        return total

    def history(self, length, samples_over_n):
        samples = self.count * samples_over_n
        # Midpoint samples avoid double-counting the periodic endpoint.
        zs = (np.arange(samples) + .5) * length / samples
        envelope = max(float(np.max(np.linalg.norm(self.slots, axis=1))),
                       float(np.max(np.linalg.norm(self.groups, axis=1))) + float(np.max(np.linalg.norm(self.inner, axis=1))))
        edges = envelope * np.sqrt(np.linspace(0, 1, self.config["radial_shell_count"] + 1))
        hist = np.zeros((self.count, len(edges)-1))
        orders = np.asarray(self.config["angular_moment_orders"])
        moments = np.zeros((self.count, len(orders)), dtype=complex)
        for start in range(0, samples, 512):
            p = self.evaluate(zs[start:start+512])[0]
            radius = np.linalg.norm(p, axis=-1)
            bins = np.clip(np.searchsorted(edges, radius, side="right") - 1, 0, len(edges)-2)
            for shell in range(len(edges)-1):
                hist[:, shell] += np.sum(bins == shell, axis=0)
            theta = np.arctan2(p[..., 1], p[..., 0])
            for k, order in enumerate(orders):
                moments[:, k] += np.sum(np.exp(1j * order * theta), axis=0)
        hist /= samples
        moments /= samples
        shell_deviation = float(np.max(np.sum(np.abs(hist - hist.mean(axis=0)), axis=1)))
        angle_deviation = float(np.max(np.abs(moments - moments.mean(axis=0))))
        return {"source_model": "midpoint_sampled_geometric_axial_residence", "execution_status": "estimated",
                "length_m": length, "samples": samples, "weight": "axial_dz_over_length",
                "shell_edges_m": edges.tolist(), "mean_shell_residence": hist.mean(axis=0).tolist(),
                "shell_residence_max_L1_deviation_from_strand_mean": shell_deviation,
                "angular_moment_orders": orders.tolist(), "angular_moment_max_deviation_from_strand_mean": angle_deviation,
                "comparison_to_area_uniform_distribution": "equal-area shells are diagnostic; individual equality and uniform area occupancy are different conditions",
                "not_electromagnetic_equality": True}

    def summarize(self):
        length = self.config["axial_length_m"]
        coarse, fine = self.lengths(length, 16), self.lengths(length, 32)
        p, v, a = self.evaluate([0., self.pitch])
        certificate = self.certificate()
        sampling = self.config["fairness_samples_over_N"]
        axial_coarse, axial_fine = self.history(length, sampling), self.history(length, 2*sampling)
        periodic = self.history(self.pitch, sampling)
        if self.family == "hamilton_crosslayer":
            periodic["analytic_equality"] = {"execution_status": "proved_by_cyclic_phase_translation",
                "shell_residence_max_L1_deviation": 0.0, "angular_moment_max_deviation": 0.0,
                "reason": "each physical strand traverses exactly the same ordered directed cycle, shifted by an integer step, over a complete N-step period"}
        area = math.pi * (self.diameter / 2)**2
        rdc = 1 / np.sum(self.config["conductivity_S_m"] * area / fine)
        return {"candidate_id": self.name, "source_model": MODEL, "execution_status": "executed",
                "electromagnetic_execution_status": "not_run", "electromagnetic_ranking": "not_available",
                "family": self.family, "strands": self.count, "grid": [self.rows, self.columns],
                "diameter_m": self.diameter, "nominal_copper_area_m2": self.count * area,
                "dc_current_density_A_mm2": self.config["current_RMS_A"] / (self.count * area) / 1e6,
                "strand_d_over_skin_depth": self.diameter * math.sqrt(math.pi*self.config["frequency_Hz"]*4*math.pi*1e-7*self.config["conductivity_S_m"]),
                "pitch_m": self.pitch if self.family != "straight" else None,
                "pitch_over_Nd": self.pitch_ratio if self.family != "straight" else None,
                "full_geometric_period_m": self.pitch if self.family != "straight" else None,
                "periods_in_one_axial_m": length / self.pitch if self.family != "straight" else None,
                "hamilton_steps": self.count if self.family == "hamilton_crosslayer" else None,
                "step_axial_length_m": self.step_length if self.family == "hamilton_crosslayer" else None,
                "subbundle_strands": 4 if self.family.startswith("multilevel") else None,
                "axial_length_m": length, "arc_length_min_m": float(np.min(fine)), "arc_length_max_m": float(np.max(fine)),
                "mean_arc_length_growth": float(np.mean(fine)/length), "Rdc_ohm_per_axial_m": float(rdc/length),
                "copper_volume_m3_per_axial_m": float(area * np.sum(fine)/length),
                "arc_quadrature_16_to_32_max_relative_change": float(np.max(np.abs(fine/coarse-1))),
                "arc_lengths_m": fine.tolist(), "certificate": certificate,
                "geometry_screen_status": "passed" if certificate["gap_screen_passed"] and certificate["curvature_screen_passed"] else "failed_geometric",
                "periodic_position_closure_error_m": float(np.max(np.linalg.norm(p[1]-p[0], axis=1))),
                "periodic_tangent_closure_error": float(np.max(np.linalg.norm(v[1]-v[0], axis=1))),
                "periodic_second_derivative_closure_error_per_m": float(np.max(np.linalg.norm(a[1]-a[0], axis=1))),
                "full_period_geometric_history": periodic, "one_m_geometric_history": axial_fine,
                "finite_history_sampling_change": {
                    "shell_L1_metric_absolute_change": abs(axial_fine["shell_residence_max_L1_deviation_from_strand_mean"]-axial_coarse["shell_residence_max_L1_deviation_from_strand_mean"]),
                    "angular_metric_absolute_change": abs(axial_fine["angular_moment_max_deviation_from_strand_mean"]-axial_coarse["angular_moment_max_deviation_from_strand_mean"]),
                    "status": "empirical_sampling_change_not_certified_error_bound"}}

    def export(self, directory, write_csv=True):
        directory.mkdir()
        z = np.linspace(0, self.config["axial_length_m"], self.config["csv_uniform_stations"])
        if self.family == "hamilton_crosslayer":
            knots = np.arange(int(math.floor(self.config["axial_length_m"] / self.step_length))+1)*self.step_length
            z = np.unique(np.r_[z, knots])
        positions = self.evaluate(z)[0]
        if write_csv:
            with (directory / "centreline_samples_m.csv").open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["physical_strand_id", "x_m", "y_m", "z_m"])
                for strand in range(self.count):
                    rows = np.column_stack((np.full(len(z), strand+1), positions[:, strand], z))
                    writer.writerows([[int(row[0]), *(format(x, ".12e") for x in row[1:])] for row in rows])
        selected = np.unique(np.linspace(0, self.count-1, min(self.config["preview_strands"], self.count), dtype=int))
        preview_z = np.linspace(0, self.config["axial_length_m"], self.config["preview_stations"])
        preview = self.evaluate(preview_z)[0]
        save_json(directory / "preview.json", {"source_model": MODEL, "execution_status": "executed",
                    "candidate_id": self.name, "coordinate_units": "metres", "diameter_m": self.diameter,
                    "sampled_display_only": True, "full_strand_count": self.count,
                    "physical_strand_ids": (selected+1).tolist(),
                    "paths": [np.column_stack((preview[:, i], preview_z)).tolist() for i in selected],
                    "procedural_description": {"family": self.family, "pitch_m": self.pitch, "slots_in_directed_cycle_m": self.slots.tolist(),
                        "hamilton_interpolation": "q(t)=10t^3-15t^4+6t^5; slot=(physical_id-1+floor(z/(P/N))) mod N",
                        "multilevel_group_centres_m": self.groups.tolist(), "multilevel_local_offsets_m": self.inner.tolist()}})


def verify_implementation():
    checks = []
    for rows, cols in [(8,10), (10,16), (20,32)]:
        cycle = hamilton_cycle(rows, cols)
        checks.append({"id": f"Hamilton_{rows}x{cols}_unique_and_adjacent", "passed": len(cycle) == rows*cols})
    t = np.array([0., 1.])
    checks.append({"id": "quintic_C2_endpoints", "passed": bool(np.all(30*t*t*(1-t)**2 == 0) and np.all(60*t*(1-t)*(1-2*t) == 0))})
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--strands", default="80,160,640")
    parser.add_argument("--families", default=None)
    parser.add_argument("--no-csv", action="store_true", help="Skip large illustrative CSV; previews and metrics remain.")
    args = parser.parse_args()
    root = args.root.resolve()
    config_path = (args.config or root / "configs" / "topology_candidates.json").resolve()
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    run_id = args.run_id or "topology_" + datetime.now(LOCAL_TZ).strftime("%Y%m%d_%H%M%S_%f")
    if not run_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in run_id):
        parser.error("Run ID contains invalid characters.")
    output = root / "outputs" / run_id
    output.mkdir(parents=False, exist_ok=False)
    start = time.perf_counter()
    snapshot = output / "source_snapshot"
    snapshot.mkdir()
    shutil.copy2(Path(__file__).resolve(), snapshot / "TopologyCandidates.py")
    shutil.copy2(config_path, snapshot / "topology_candidates.json")
    counts = [int(x) for x in args.strands.split(",")]
    families = args.families.split(",") if args.families else config["families"]
    if any(str(n) not in config["strand_grids"] for n in counts) or any(f not in config["families"] for f in families):
        raise ValueError("Unsupported count/family; select candidates declared in the configuration.")
    save_json(output / "parameters.json", {"run_id":run_id, "source_model":MODEL, "config":config, "strands":counts, "families":families})
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    save_json(output / "environment.json", {"python_version":platform.python_version(), "numpy_version":np.__version__,
        "platform":platform.system(), "git_head":head or None, "timestamp":datetime.now(LOCAL_TZ).isoformat(),
        "execution_route":"existing_local_numpy_python", "network_used":False})
    (output / "model_assumptions.md").write_text("# Geometric candidate assumptions\n\n" + "\n".join("- "+item for item in config["assumptions"]), encoding="utf-8")
    checks, summaries = verify_implementation(), []
    try:
        with (output / "run_log.txt").open("w", encoding="utf-8") as log:
            for count in counts:
                for family in families:
                    ratios = config["pitch_over_Nd"][:1] if family == "straight" else config["pitch_over_Nd"]
                    for ratio in ratios:
                        candidate = Candidate(config, count, family, ratio)
                        message = f"{datetime.now(LOCAL_TZ).isoformat()} start {candidate.name}"
                        print(message, flush=True); log.write(message+"\n"); log.flush()
                        result = candidate.summarize()
                        directory = output / candidate.name
                        candidate.export(directory, write_csv=not args.no_csv)
                        save_json(directory / "metrics.json", result)
                        summaries.append(result)
                        checks.extend([
                            {"id":candidate.name+"_equal_copper_area", "passed":abs(result["nominal_copper_area_m2"]/(640*math.pi*(.0001/2)**2)-1)<1e-12},
                            {"id":candidate.name+"_C2_period_closure", "passed": result["periodic_position_closure_error_m"]<1e-10 and result["periodic_tangent_closure_error"]<1e-8 and result["periodic_second_derivative_closure_error_per_m"]<1e-6},
                            {"id":candidate.name+"_arc_quadrature", "passed":result["arc_quadrature_16_to_32_max_relative_change"]<1e-8}])
                        save_json(output / "checkpoint.json", {"execution_status":"running", "completed_candidate_ids":[r["candidate_id"] for r in summaries]})
                        message = f"finished {candidate.name}: {result['geometry_screen_status']}; continuous gap/d={result['certificate']['continuous_3D_surface_gap_lower_bound_m']/candidate.diameter:.6g}"
                        print(message, flush=True); log.write(message+"\n"); log.flush()
        save_json(output / "results.json", {"run_id":run_id, "stage":"topology_candidates", "source_model":MODEL,
            "execution_status":"executed", "electromagnetic_execution_status":"not_run", "elapsed_seconds":time.perf_counter()-start,
            "candidate_count":len(summaries), "geometrically_passed_count":sum(r["geometry_screen_status"]=="passed" for r in summaries),
            "candidates":summaries, "electromagnetic_ranking":"not_available"})
        save_json(output / "test_report.json", {"run_id":run_id, "source_model":"geometric_generator_integrity_and_quadrature",
            "execution_status":"passed" if all(c["passed"] for c in checks) else "failed", "checks":checks,
            "scope":"These checks do not assert electromagnetic performance or machine manufacturability."})
        columns=["candidate_id","source_model","geometry_screen_status","electromagnetic_execution_status","strands","diameter_m","nominal_copper_area_m2","pitch_m","Rdc_ohm_per_axial_m","mean_arc_length_growth","copper_volume_m3_per_axial_m"]
        with (output / "candidate_summary.csv").open("w",encoding="utf-8",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
            writer.writerows({k:r[k] for k in columns} for r in summaries)
        save_json(output / "run_manifest.json", {"run_id":run_id,"source_model":MODEL,"git_head":head or None,
            "source_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in snapshot.iterdir()},
            "completed_at":datetime.now(LOCAL_TZ).isoformat()})
        save_json(output / "process_status.json", {"process_exit_code":0,"elapsed_seconds":time.perf_counter()-start})
        print(str(output),flush=True)
        return 0
    except Exception as exc:
        save_json(output / "failure.json", {"source_model":MODEL,"execution_status":"failed_execution", "error":str(exc),"traceback":traceback.format_exc(),
                "completed_candidate_ids":[r["candidate_id"] for r in summaries]})
        save_json(output / "process_status.json", {"process_exit_code":1,"elapsed_seconds":time.perf_counter()-start})
        raise


if __name__ == "__main__":
    sys.exit(main())
