"""Native Maxwell 3D APhi calibration with archived, independently integrated J.

No CAD import, software installation, or global MCP change is performed. A pilot
is one geometry/mesh and three actual voltage solves. It is not full acceptance.
This entry point deliberately does not modify the existing Ansys runner.
"""
from __future__ import annotations

import argparse
import cmath
import contextlib
import copy
import ctypes
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime, timezone

from ansys_validate import dump

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file() and (p / "configs/reference_parameters.json").is_file())
GIB = 1024 ** 3


class ResourceBlocked(RuntimeError):
    pass


class InterfaceFailed(RuntimeError):
    pass


class NumericalFailed(RuntimeError):
    pass


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def complex_record(value):
    return {"real": float(value.real), "imag": float(value.imag)}


def require(value, message):
    if value is False or value is None:
        raise InterfaceFailed(message)
    return value


def check(identifier, actual, tolerance):
    actual = float(actual)
    return {"id": identifier, "actual": actual, "tolerance": tolerance,
            "execution_status": "passed" if math.isfinite(actual) and actual <= tolerance else "failed"}


def read_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if config.get("geometry_kind") != "straight":
        raise NotImplementedError("Only native straight geometry is implemented; curved geometry remains not_run.")
    fixed = {"frequency_Hz": 200000.0, "conductivity_S_per_m": 5.8e7,
             "relative_permeability": 1.0, "total_current_RMS_A": 20.0, "temperature_C": 20.0}
    for key, value in fixed.items():
        if not math.isclose(float(config[key]), value, rel_tol=1e-12):
            raise ValueError("Project invariant differs: " + key)
    centers, radius = config["strand_centers_m"], config["strand_diameter_m"] / 2
    if not centers or any(len(center) != 2 for center in centers):
        raise ValueError("Expected nonempty labelled XY strand centers.")
    for i, point in enumerate(centers):
        if math.hypot(*point) + radius >= config["return_inner_radius_m"]:
            raise ValueError("Strand intersects or touches the explicit return.")
        for other in centers[:i]:
            if math.dist(point, other) <= 2 * radius:
                raise ValueError("Copper strands touch; along-path insulation would be violated.")
    if not (0 < config["return_inner_radius_m"] < config["return_outer_radius_m"]
            < config["outer_domain_radius_m"] and config["axial_length_m"] > 0):
        raise ValueError("Invalid finite coaxial geometry.")
    mesh = config["mesh_lengths_m"]
    if len(mesh) != 3 or not (mesh[0] > mesh[1] > mesh[2] > 0):
        raise ValueError("Exactly three strictly decreasing mesh lengths are required.")
    if not (1 <= int(config["solver_cores"]) <= 4):
        raise ValueError("Student execution is limited to at most 4 solver cores.")
    if config["voltage_excitation_model"] not in {"Single Potential", "Double Potentials", "Double Potentials with Ground"}:
        raise ValueError("Unknown APhi terminal model.")
    if config["voltage_excitation_model"] != "Single Potential" and config.get("axial_air_padding_m", 0) <= 0:
        raise ValueError("Double Potentials faces must be internal: positive axial_air_padding_m is required.")
    return config


def physical_geometry(config):
    count, diameter = len(config["strand_centers_m"]), config["strand_diameter_m"]
    length, sigma = config["axial_length_m"], config["conductivity_S_per_m"]
    area = count * math.pi * diameter ** 2 / 4
    return {"strand_count": count, "nominal_copper_area_m2": area,
            "nominal_dc_current_density_A_per_mm2": config["total_current_RMS_A"] / area / 1e6,
            "meets_5_mm2_nominal_constraint": area >= 5e-6,
            "source_Rdc_ohm": length / (sigma * area),
            "source_copper_volume_m3": length * area, "arc_length_growth": 1.0,
            "return_copper_volume_m3": math.pi * (config["return_outer_radius_m"] ** 2
                                                   - config["return_inner_radius_m"] ** 2) * length}


def voltage_parameters(value):
    """Explicit volts prevent PyAEDT's numeric default of millivolts."""
    return {"Voltage": format(abs(value) * math.sqrt(2), ".17g") + "V",
            "phase": format(math.degrees(cmath.phase(value)), ".17g") + "deg"}


def estimate_resources(config, mesh_length):
    geometry = physical_geometry(config)
    metal_volume = geometry["source_copper_volume_m3"] + geometry["return_copper_volume_m3"]
    air_length = config["axial_length_m"] + 2 * config.get("axial_air_padding_m", 0)
    air_volume = math.pi * config["outer_domain_radius_m"] ** 2 * air_length - metal_volume
    # This is a planning estimate. It cannot certify the actual Student mesh limit.
    tets = int(math.ceil(6 * (metal_volume / mesh_length ** 3
                            + air_volume / config["air_mesh_length_m"] ** 3)))
    surface_area = sum(2 * math.pi * (config["strand_diameter_m"] / 2) * config["axial_length_m"]
                       + 2 * math.pi * (config["strand_diameter_m"] / 2) ** 2
                       for _ in config["strand_centers_m"])
    surface_area += 2 * math.pi * (config["return_inner_radius_m"] + config["return_outer_radius_m"]) * config["axial_length_m"]
    surface_elements = int(math.ceil(2 * surface_area / mesh_length ** 2))
    return {"estimated_tetrahedra": tets, "estimated_metal_surface_triangles": surface_elements,
            "estimated_working_bytes": int(2 * GIB + 50000 * tets), "measured_allocation": False,
            "estimate_scope": "Conservative isotropic tetrahedron heuristic, not a measured solver/hardware maximum."}


def available_ram():
    if os.name == "nt":
        class Status(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                (name, ctypes.c_ulonglong) for name in ("total", "free", "total_page", "free_page", "total_virtual", "free_virtual", "extended")]
        status = Status()
        status.length = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            raise ResourceBlocked("Windows RAM probe failed.")
        return {"total_bytes": status.total, "free_bytes": status.free}
    import psutil
    ram = psutil.virtual_memory()
    return {"total_bytes": ram.total, "free_bytes": ram.available}


def preflight(config, mesh_length):
    resource = {**estimate_resources(config, mesh_length), **available_ram()}
    reason = None
    if resource["estimated_tetrahedra"] > config["student_tetrahedra_limit"]:
        reason = "predicted_mesh_exceeds_Student_tetrahedron_budget"
    elif resource["estimated_metal_surface_triangles"] > config["student_surface_elements_limit"]:
        reason = "predicted_metal_surface_mesh_exceeds_Student_surface_budget"
    elif resource["estimated_working_bytes"] > min(config["maximum_working_set_GiB"] * GIB,
                                                     resource["free_bytes"] - config["minimum_system_free_GiB"] * GIB):
        reason = "predicted_working_memory_exceeds_available_budget"
    resource.update(execution_status="blocked_environment_resource_budget" if reason else "passed", reason=reason)
    return resource


def case_variations(config, mode):
    meshes = config["mesh_lengths_m"]
    items = [("mesh_coarse", copy.deepcopy(config), meshes[0])]
    if mode == "pilot":
        return items
    items.extend((label, copy.deepcopy(config), mesh) for label, mesh in zip(("mesh_medium", "mesh_fine"), meshes[1:]))
    return_config = copy.deepcopy(config)
    thickness = config["return_outer_radius_m"] - config["return_inner_radius_m"]
    return_config["return_inner_radius_m"] *= config["return_radius_sensitivity_factor"]
    return_config["return_outer_radius_m"] = return_config["return_inner_radius_m"] + thickness
    if return_config["return_outer_radius_m"] >= config["outer_domain_radius_m"]:
        raise ValueError("Return sensitivity must fit inside the unchanged outer domain.")
    items.append(("return_distance", return_config, meshes[-1]))
    outer_config = copy.deepcopy(config)
    outer_config["outer_domain_radius_m"] *= config["outer_domain_sensitivity_factor"]
    items.append(("outer_domain", outer_config, meshes[-1]))
    for factor in config["length_sensitivity_factors"]:
        length_config = copy.deepcopy(config)
        length_config["axial_length_m"] *= factor
        items.append(("length_" + format(factor, "g"), length_config, meshes[-1]))
    return items


def archive_snapshot(out, config_path):
    snapshot = out / "source_snapshot"
    snapshot.mkdir()
    for path in [Path(__file__).resolve(), Path(__file__).with_name("ansys_validate.py"), Path(__file__).with_name("RunAnsysValidation.ps1"), config_path]:
        shutil.copy2(path, snapshot / path.name)
    dump(out / "source_hashes.json", {path.name: sha256(path) for path in snapshot.iterdir()})


def geometry_model(app, config):
    app.modeler.model_units = "mm"
    copper = app.materials.add_material("native_litz_copper")
    copper.conductivity = config["conductivity_S_per_m"]
    copper.permeability = config["relative_permeability"]
    copper.permittivity = 1.0
    air = app.materials.add_material("native_litz_air")
    air.conductivity = 0.0
    air.permeability = air.permittivity = 1.0
    length_mm, radius_mm = config["axial_length_m"] * 1000, config["strand_diameter_m"] * 500
    source = []
    for index, center in enumerate(config["strand_centers_m"], 1):
        obj = require(app.modeler.create_cylinder("Z", [center[0] * 1000, center[1] * 1000, 0],
                      radius_mm, length_mm, num_sides=0, name=f"Source_{index:04d}", material="native_litz_copper"),
                      "Native source cylinder creation failed.")
        obj.solve_inside = True
        source.append(obj)
    return_outer = require(app.modeler.create_cylinder("Z", [0, 0, 0], config["return_outer_radius_m"] * 1000,
                           length_mm, num_sides=0, name="ReturnCopper", material="native_litz_copper"), "Return creation failed.")
    return_inner = require(app.modeler.create_cylinder("Z", [0, 0, 0], config["return_inner_radius_m"] * 1000,
                           length_mm, num_sides=0, name="ReturnVoid", material="native_litz_air"), "Return bore creation failed.")
    require(app.modeler.subtract(return_outer, return_inner, keep_originals=False), "Native annular return subtract failed.")
    return_outer = app.modeler["ReturnCopper"]
    return_outer.solve_inside = True
    padding_mm = config.get("axial_air_padding_m", 0) * 1000
    region = require(app.modeler.create_cylinder("Z", [0, 0, -padding_mm], config["outer_domain_radius_m"] * 1000,
                     length_mm + 2 * padding_mm, num_sides=0, name="AirRegion", material="native_litz_air"), "Air cylinder creation failed.")
    require(app.modeler.subtract(region, [obj.name for obj in source] + [return_outer.name], keep_originals=True),
            "Air-minus-copper native boolean failed.")
    region = app.modeler["AirRegion"]
    ends, geometry_checks = {}, []
    radius_outer_mm = config["outer_domain_radius_m"] * 1000
    for obj in source + [return_outer]:
        near, far, sides = [], [], []
        for face in obj.faces:
            face_center = face.center_from_aedt if face.is_planar else None
            if face_center and abs(face_center[2]) < 1e-7:
                near.append(face)
            elif face_center and abs(face_center[2] - length_mm) < 1e-7:
                far.append(face)
            else:
                sides.append(face)
        if len(near) != 1 or len(far) != 1:
            raise InterfaceFailed("Cannot uniquely identify native conductor terminal faces: " + obj.name)
        expected_area = math.pi * radius_mm ** 2 if obj in source else math.pi * (
            (config["return_outer_radius_m"] * 1000) ** 2 - (config["return_inner_radius_m"] * 1000) ** 2)
        geometry_checks.append({"name": obj.name, "near_face_id": near[0].id, "far_face_id": far[0].id,
                                "side_face_ids": [face.id for face in sides],
                                "near_area_m2": near[0].area * 1e-6, "far_area_m2": far[0].area * 1e-6,
                                "actual_CAD_volume_m3": obj.volume * 1e-9,
                                "expected_area_m2": expected_area * 1e-6,
                                "area_relative_error": max(abs(near[0].area / expected_area - 1), abs(far[0].area / expected_area - 1)),
                                "volume_relative_error": abs(obj.volume / (expected_area * length_mm) - 1)})
        ends[obj.name] = {"near": near[0].id, "far": far[0].id, "sides": [face.id for face in sides]}
    outer_faces = []
    for face in region.faces:
        face_center = face.center_from_aedt if face.is_planar else None
        end = bool(face_center) and (abs(face_center[2] + padding_mm) < 1e-7
                                    or abs(face_center[2] - length_mm - padding_mm) < 1e-7)
        edge_points = [list(map(float, app.modeler.oeditor.GetEdgePositionAtNormalizedParameter(edge.id, fraction)))
                       for edge in face.edges for fraction in (0, .25, .5, .75)]
        exterior_side = not face.is_planar and any(abs(math.hypot(point[0], point[1]) - radius_outer_mm) < 1e-7
                                                  for point in edge_points)
        if end or exterior_side:
            outer_faces.append(face.id)
    if not outer_faces:
        raise InterfaceFailed("No exterior magnetic faces identified.")
    require(app.assign_flux_tangential(outer_faces, flux_name="OuterFluxTangential"), "APhi magnetic exterior boundary rejected.")
    require(app.eddy_effects_on([obj.name for obj in source] + [return_outer.name],
                              enable_eddy_effects=True, enable_displacement_current=False), "APhi copper eddy effect setting rejected.")
    return source, return_outer, region, ends, geometry_checks, outer_faces


def assign_terminals(app, config, ends):
    boundaries = {}
    for name, end in ends.items():
        near = require(app.assign_voltage([end["near"]], amplitude="0V", name=name + "_Near",
                       excitation_model=config["voltage_excitation_model"], phase="0deg"), "Near end APhi voltage rejected: " + name)
        far = require(app.assign_voltage([end["far"]], amplitude="0V", name=name + "_FarZero",
                      excitation_model=config["voltage_excitation_model"], phase="0deg"), "Far 0V ideal terminal rejected: " + name)
        boundaries[name] = {"near": near, "far": far}
    return boundaries


def make_expression(app, name, operations, assignment=None):
    definition = {"name": name, "description": "Independent physical current-density integration",
                  "design_type": ["Maxwell 3D"], "fields_type": ["Fields"], "solution_type": "",
                  "primary_sweep": "Freq", "assignment": "", "assignment_type": ["Solid", "Face"],
                  "operations": operations, "dependent_expressions": [], "report": ["Data Table"]}
    return require(app.post.fields_calculator.add_expression(definition, assignment=assignment, name=name),
                   "Current-density calculator expression rejected: " + name)


def current_density_expressions(app, config, ends):
    field = config["current_density_quantity"]
    field_operation = (f"NameOfExpression('{field}')" if config.get("current_density_expression_kind", "fundamental") == "named"
                       else f"Fundamental_Quantity('{field}')")
    expressions = {}
    for name, end in ends.items():
        expressions[name] = {"near": {}, "far": {}, "sides": []}
        for terminal in ("near", "far"):
            for component, operation in (("real", "Real"), ("imag", "Imag")):
                expression = name + "_" + terminal + "_Jz_" + component
                operations = [field_operation, "Operation('ScalarZ')", f"Operation('{operation}')",
                              "EnterSurface('assignment')", "Operation('SurfaceValue')", "Operation('Integrate')"]
                expressions[name][terminal][component] = make_expression(app, expression, operations, end[terminal])
        # Average Joule loss from peak phasors: (Re J dot Re J + Im J dot Im J)/(2 sigma).
        operations = []
        for axis in ("ScalarX", "ScalarY", "ScalarZ"):
            for component in ("Real", "Imag"):
                one = [field_operation, f"Operation('{axis}')", f"Operation('{component}')"]
                operations.extend(one + one + ["Operation('*')"])
                if len(operations) > len(one + one + ["Operation('*')"]):
                    operations.append("Operation('+')")
        operations += [f"Scalar_Constant({1 / (2 * config['conductivity_S_per_m']):.17g})",
                       "Operation('*')", "EnterVolume('assignment')", "Operation('VolumeValue')", "Operation('Integrate')"]
        expressions[name]["joule"] = make_expression(app, name + "_VolumeJoule", operations, name)
        for index, face_id in enumerate(end["sides"]):
            operations = []
            for component in ("Real", "Imag"):
                one = [field_operation, "Operation('Normal')", "Operation('Dot')", f"Operation('{component}')"]
                operations += one + one + ["Operation('*')"]
            operations += ["Operation('+')", "Scalar_Constant(0.5)", "Operation('*')", "EnterSurface('assignment')",
                           "Operation('SurfaceValue')", "Operation('Integrate')"]
            expressions[name]["sides"].append(make_expression(app, name + f"_SideJnSquared_{index}", operations, face_id))
    return expressions


def evaluate_expression(app, config, expression, folder):
    file = folder / (expression + ".fld")
    require(app.post.fields_calculator.write(expression, str(file), setup=app.nominal_adaptive,
                   intrinsics={"Freq": format(config["frequency_Hz"], ".17g") + "Hz", "Phase": "0deg"}),
            "Physical field expression export failed: " + expression)
    if not file.is_file():
        raise InterfaceFailed("Calculator returned a path without an actual field file: " + expression)
    raw = file.read_text(encoding="utf-8", errors="replace").splitlines()
    value = float(next(line.strip() for line in reversed(raw) if line.strip()).replace("D", "E"))
    if not math.isfinite(value):
        raise NumericalFailed("Nonfinite physical field integral: " + expression)
    return value


def integrate_fields(app, config, expressions, folder, objects):
    data = {"source_model": "independent_surface_Jz_and_volume_Joule_integrals", "conductors": {}}
    for name, expr in expressions.items():
        terminals = {}
        for terminal in ("near", "far"):
            parts = {part: evaluate_expression(app, config, expression, folder) / math.sqrt(2)
                     for part, expression in expr[terminal].items()}
            terminals[terminal] = parts
        joule = evaluate_expression(app, config, expr["joule"], folder)
        side_squares = sum(evaluate_expression(app, config, expression, folder) for expression in expr["sides"])
        if side_squares < -1e-18:
            raise NumericalFailed("Negative integral of squared side-normal current: " + name)
        obj = objects[name]
        side_area = sum(face.area for face in obj.faces if face.id not in [obj.top_face_z.id, obj.bottom_face_z.id]) * 1e-6
        data["conductors"][name] = {"current_RMS_A_positive_z": terminals, "independent_joule_W": joule,
                                     "side_normal_current_squared_integral_A2_per_m2": side_squares,
                                     "side_normal_flux_L1_bound_A": math.sqrt(max(0.0, side_squares) * side_area)}
    for terminal in ("near", "far"):
        source = sum(complex(row["current_RMS_A_positive_z"][terminal]["real"], row["current_RMS_A_positive_z"][terminal]["imag"])
                     for name, row in data["conductors"].items() if name != "ReturnCopper")
        ret = data["conductors"]["ReturnCopper"]["current_RMS_A_positive_z"][terminal]
        data[terminal + "_source_current_RMS_A"] = complex_record(source)
        data[terminal + "_return_current_RMS_A"] = ret
    data["source_joule_W"] = sum(row["independent_joule_W"] for name, row in data["conductors"].items() if name != "ReturnCopper")
    data["return_joule_W"] = data["conductors"]["ReturnCopper"]["independent_joule_W"]
    data["total_joule_W"] = data["source_joule_W"] + data["return_joule_W"]
    dump(folder / "independent_field_integrals.json", data)
    return data


def mesh_identity(project, mesh_stats):
    # Hash actual coordinate/connectivity payloads, omitting AEDT's timestamp/index header.
    results = project.with_suffix(".aedtresults")
    candidates = list(results.rglob("*.msh")) if results.exists() else []
    current = [path for path in candidates if any("cmesh" in part.lower() for part in path.parts)]
    if current:
        newest = max(current, key=lambda path: path.stat().st_mtime_ns)
        candidates = [path for path in current if path.parent == newest.parent]
    if not candidates:
        raise InterfaceFailed("No actual native mesh coordinate/connectivity file available; fixed mesh cannot be certified.")
    entries = []
    for path in sorted(candidates):
        raw = path.read_bytes()
        if raw.startswith(b"$begin") and b"$begin 'mesh'" in raw:
            raw = raw[raw.index(b"$begin 'mesh'"):]
            raw = b"\n".join(line.strip() for line in raw.splitlines() if b"verbose=" not in line)
        entries.append({"file": path.name, "relative_path": str(path.relative_to(results)),
                        "raw_sha256": sha256(path), "mesh_payload_sha256": hashlib.sha256(raw).hexdigest(),
                        "bytes": path.stat().st_size})
    text = mesh_stats.read_text(encoding="utf-8", errors="replace")
    total = re.search(r"Total number of mesh elements:\s*([\d,]+)", text, re.IGNORECASE)
    if not total:
        raise InterfaceFailed("Cannot read actual mesh element count; Student budget acceptance remains unverified.")
    return {"tetrahedra": int(total.group(1).replace(",", "")), "files": entries,
            "identity_sha256": hashlib.sha256(json.dumps(sorted(entry["mesh_payload_sha256"] for entry in entries)).encode()).hexdigest(),
            "scope": "Actual native mesh-file content identity, excluding ASCII timestamp/index header; statistics separately retained."}


class ResourceMonitor:
    def __init__(self, app, folder, config):
        import psutil
        self.psutil, self.pid, self.folder, self.config = psutil, app.desktop_class.aedt_process_id, folder, config
        self.stop_event = threading.Event()
        self.reason = None
        self.started = time.monotonic()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def run(self):
        low_count = 0
        path = self.folder / "resource_curve.jsonl"
        while not self.stop_event.wait(3):
            try:
                owned = self.psutil.Process(self.pid)
                processes = [owned] + owned.children(recursive=True)
                working = sum(proc.memory_info().rss for proc in processes if proc.is_running())
                free = available_ram()["free_bytes"]
                elapsed = time.monotonic() - self.started
                low = free < self.config["minimum_system_free_GiB"] * GIB or working > self.config["maximum_working_set_GiB"] * GIB
                low_count = low_count + 1 if low else 0
                row = {"elapsed_s": elapsed, "owned_aedt_pid": self.pid, "owned_working_bytes": working,
                       "free_RAM_bytes": free, "low_budget_samples": low_count}
                with path.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(row) + "\n")
                if low_count >= 3 or elapsed > self.config["solver_timeout_s"]:
                    self.reason = "runtime_RAM_budget" if low_count >= 3 else "runtime_timeout"
                    dump(self.folder / "resource_stop.json", {**row, "reason": self.reason, "execution_status": "blocked_environment_resource_budget"})
                    # Only this newly created Desktop and its descendants are owned by this run.
                    for proc in reversed(processes):
                        with contextlib.suppress(self.psutil.Error):
                            proc.terminate()
                    return
            except self.psutil.Error:
                return

    def __exit__(self, *ignored):
        self.stop_event.set()
        self.thread.join(timeout=5)


def solve_current_vector(data):
    import numpy as np
    return np.array([complex(data[key]["real"], data[key]["imag"])
                     for key in ("far_source_current_RMS_A", "far_return_current_RMS_A")])


def round_wire_rac(config):
    if len(config["strand_centers_m"]) != 1:
        return None
    radius = config["strand_diameter_m"] / 2
    sigma = config["conductivity_S_per_m"]
    k = cmath.sqrt(1j * 2 * math.pi * config["frequency_Hz"] * 4 * math.pi * 1e-7 * sigma)
    z = k * radius
    def bessel(order):
        term = total = 1 + 0j if order == 0 else z / 2
        for index in range(1, 10000):
            term *= z * z / (4 * index * (index + order))
            total += term
            if abs(term) < 1e-16 * max(abs(total), 1e-30):
                return total
        raise NumericalFailed("Round-wire Bessel series did not converge.")
    return (k * bessel(0) / (2 * math.pi * radius * sigma * bessel(1))).real


def run_one(config, mesh_length, folder, mesh_verifier=None, field_exporter=None, project_freezer=None):
    from ansys.aedt.core import Maxwell3d
    from ansys.aedt.core.generic.constants import SolutionsMaxwell3D
    import numpy as np
    folder.mkdir(exist_ok=False)
    resource = preflight(config, mesh_length)
    dump(folder / "resource_preflight.json", resource)
    dump(folder / "parameters.json", {**config, "mesh_length_m": mesh_length, **physical_geometry(config)})
    report = {"source_model": config["source_model"], "execution_status": "running", "solves": [],
              "full_physical_acceptance": "not_run", "tests": [], "solver_started": False, "actual_solver_attempts": 0}
    if resource["execution_status"] != "passed":
        report.update(execution_status="blocked_environment_resource_budget", resource_preflight=resource)
        dump(folder / "results.json", report)
        return report
    app, project = None, folder / "native3d.aedt"
    started = time.monotonic()
    try:
        app = Maxwell3d(project=str(project), design="NativeStraightAPhi", version="2025.2",
                        solution_type=SolutionsMaxwell3D.ACMagneticAPhi, non_graphical=True,
                        new_desktop=True, close_on_exit=True, student_version=True)
        if app.solution_type != SolutionsMaxwell3D.ACMagneticAPhi:
            raise InterfaceFailed("Actual design is not AC Magnetic APhi: " + str(app.solution_type))
        report["actual_solution_type"] = app.solution_type
        source, ret, air, ends, geometry, exterior = geometry_model(app, config)
        report.update(geometry=geometry, conductor_terminal_faces=ends, magnetic_exterior_faces=exterior,
                      actual_sigma_S_per_m=float(app.materials["native_litz_copper"].conductivity.value),
                      actual_mu_r=float(app.materials["native_litz_copper"].permeability.value))
        if not math.isclose(report["actual_sigma_S_per_m"], config["conductivity_S_per_m"], rel_tol=1e-12) or not math.isclose(report["actual_mu_r"], 1.0, rel_tol=1e-12):
            raise InterfaceFailed("Actual saved copper material differs from the project invariants.")
        for row in geometry:
            report["tests"].append(check("CAD_area_" + row["name"], row["area_relative_error"], config["tolerances"]["geometry_relative"]))
            report["tests"].append(check("CAD_volume_" + row["name"], row["volume_relative_error"], config["tolerances"]["geometry_relative"]))
        dump(folder / "geometry_validation.json", geometry)
        if any(test["execution_status"] != "passed" for test in report["tests"]):
            raise NumericalFailed("Native geometry unit/volume gate failed before solving.")
        boundaries = assign_terminals(app, config, ends)
        setup = require(app.create_setup(name="NativeAPhiSetup"), "APhi setup creation rejected.")
        setup.props["Frequency"] = str(config["frequency_Hz"]) + "Hz"
        setup.props["MaximumPasses"] = 1
        setup.props["MinimumPasses"] = 1
        setup.props["PercentError"] = 1
        require(setup.update(), "APhi setup update rejected.")
        require(app.mesh.assign_length_mesh([obj.name for obj in source] + [ret.name], inside_selection=True,
                     maximum_length=f"{mesh_length * 1000:.17g}mm", maximum_elements=None, name="MetalResolution"), "Metal mesh operation rejected.")
        require(app.mesh.assign_length_mesh([air.name], inside_selection=True,
                     maximum_length=f"{config['air_mesh_length_m'] * 1000:.17g}mm", maximum_elements=None, name="AirResolution"), "Air mesh operation rejected.")
        require(app.save_project(str(project)), "Native project could not be saved before solving.")
        report["project_exists"] = project.is_file()
        if not project.is_file():
            raise InterfaceFailed("save_project returned without a real native project file.")
        validation = app.validate_simple()
        report["validation_raw"] = validation
        if validation is False or validation == 0:
            raise InterfaceFailed("Native APhi project validation rejected.")
        objects = {obj.name: obj for obj in source + [ret]}
        expressions = current_density_expressions(app, config, ends)
        dump(folder / "calculator_expressions.json", expressions)
        fixed_identity = None

        def solve(label, vs, vr):
            nonlocal fixed_identity
            solve_dir = folder / label
            solve_dir.mkdir()
            for name, terminal in boundaries.items():
                values = voltage_parameters(vr if name == "ReturnCopper" else vs)
                for key, value in values.items():
                    terminal["near"].props[key] = value
                require(terminal["near"].update(), "Voltage change rejected: " + name)
            dump(solve_dir / "excitation_report.json", {"source_voltage_RMS_V": complex_record(vs), "return_voltage_RMS_V": complex_record(vr),
                 "far_terminal_V": 0.0, "voltage_model": config["voltage_excitation_model"],
                 "boundaries": {name: {key: dict(boundary.props) for key, boundary in terminal.items()} for name, terminal in boundaries.items()},
                 "phasor_convention": "exp(+j omega t), AEDT peak voltage=sqrt(2)*RMS; J flux divided by sqrt(2), Joule prefactor 1/(2 sigma)."})
            require(app.save_project(), "Native project save failed before " + label)
            report["solver_started"] = True
            report["actual_solver_attempts"] += 1
            dump(folder / "checkpoint.json", report)
            with ResourceMonitor(app, solve_dir, config) as monitor:
                solved = app.analyze_setup(setup.name, cores=config["solver_cores"], use_auto_settings=False,
                                            revert_to_initial_mesh=False, blocking=True)
            if monitor.reason:
                raise ResourceBlocked(monitor.reason)
            require(solved, "Actual APhi solve failed or was rejected: " + label)
            app.export_mesh_stats(setup.name, output_file=str(solve_dir / "mesh_stats.csv"))
            app.export_convergence(setup.name, output_file=str(solve_dir / "convergence.csv"))
            identity = mesh_identity(project, solve_dir / "mesh_stats.csv")
            if mesh_verifier is not None:
                identity["closure_actual_mesh"] = mesh_verifier(app, project, solve_dir / "mesh_stats.csv", solve_dir)
            dump(solve_dir / "mesh_identity.json", identity)
            if identity["tetrahedra"] > config["student_tetrahedra_limit"]:
                raise ResourceBlocked("Actual mesh exceeds configured Student tetrahedron budget.")
            if fixed_identity is None:
                fixed_identity = identity
            elif identity["identity_sha256"] != fixed_identity["identity_sha256"]:
                raise NumericalFailed("Actual mesh coordinate/connectivity identity changed across voltage basis solves.")
            data = integrate_fields(app, config, expressions, solve_dir, objects)
            report["solves"].append({"label": label, "source_voltage_RMS_V": complex_record(vs),
                                      "return_voltage_RMS_V": complex_record(vr), "mesh_identity": identity, "data": data})
            dump(folder / "checkpoint.json", report)
            return data

        basis_source, basis_return = solve("basis_source", 1 + 0j, 0j), solve("basis_return", 0j, 1 + 0j)
        admittance = np.column_stack([solve_current_vector(basis_source), solve_current_vector(basis_return)])
        condition = float(np.linalg.cond(admittance))
        if not math.isfinite(condition) or condition > 1e12:
            raise NumericalFailed("Actual port admittance is singular or ill-conditioned.")
        target = np.array([config["total_current_RMS_A"] + 0j, -config["total_current_RMS_A"] + 0j])
        voltage = np.linalg.solve(admittance, target)
        actual = solve("verify_20A", complex(voltage[0]), complex(voltage[1]))
        if field_exporter is not None:
            report["field_exports"] = field_exporter(app, config, folder / "verify_20A", dimension=3)
        port_error = float(np.linalg.norm(solve_current_vector(actual) - target) / np.linalg.norm(target))
        near = np.array([complex(actual[key]["real"], actual[key]["imag"])
                         for key in ("near_source_current_RMS_A", "near_return_current_RMS_A")])
        terminal_error = float(np.linalg.norm(near - solve_current_vector(actual)) / np.linalg.norm(target))
        power = float(np.real(np.vdot(near, voltage)))
        power_error = abs(power - actual["total_joule_W"]) / max(abs(power), abs(actual["total_joule_W"]), 1e-30)
        side_bound = sum(row["side_normal_flux_L1_bound_A"] for row in actual["conductors"].values()) / config["total_current_RMS_A"]
        rac = actual["source_joule_W"] / (config["total_current_RMS_A"] ** 2 * config["axial_length_m"])
        tolerance = config["tolerances"]
        report["tests"].extend([check("actual_total_complex_current_constraint", port_error, tolerance["port_relative"]),
                    check("independent_near_far_J_flux_continuity", terminal_error, tolerance["terminal_flux_relative"]),
                    check("independent_volume_Joule_equals_terminal_power", power_error, tolerance["power_relative"]),
                    check("insulated_side_normal_flux_bound", side_bound, tolerance["side_flux_bound_relative"])])
        reference = round_wire_rac(config)
        if reference is not None:
            report["Bessel_diagnostic"] = {**check("source_Rac_Bessel_diagnostic", abs(rac / reference - 1), tolerance["rac_relative"]),
                    "scope": "Infinite straight-wire internal impedance versus finite native segment; full length convergence remains required. This diagnostic does not gate coarse port/interface pilots."}
        currents = [complex(row["current_RMS_A_positive_z"]["far"]["real"], row["current_RMS_A_positive_z"]["far"]["imag"])
                    for name, row in actual["conductors"].items() if name != "ReturnCopper"]
        ideal = config["total_current_RMS_A"] / len(currents)
        report.update(terminal_admittance_S=[[(complex_record(value)) for value in row] for row in admittance],
             terminal_admittance_condition=condition, calibrated_source_voltage_RMS_V=complex_record(complex(voltage[0])),
             calibrated_return_voltage_RMS_V=complex_record(complex(voltage[1])), independent_input_power_W=power,
             independent_total_joule_W=actual["total_joule_W"], source_Rac_ohm_per_axial_m=rac,
             source_Rac_Rdc=rac * config["axial_length_m"] / physical_geometry(config)["source_Rdc_ohm"],
             source_loss_W_per_axial_m=actual["source_joule_W"] / config["axial_length_m"],
             source_copper_volume_m3_per_axial_m=physical_geometry(config)["source_copper_volume_m3"] / config["axial_length_m"],
             mean_arc_length_growth=1.0, strand_currents_RMS_A=[complex_record(current) for current in currents],
             complex_current_deviation_relative=float(np.linalg.norm(np.array(currents) - ideal) / np.linalg.norm(currents)),
             Bessel_reference_Rac_ohm_per_m=reference,
             execution_status="passed" if all(test["execution_status"] == "passed" for test in report["tests"]) else "failed_numerical")
        require(app.save_project(), "Final native solved project save failed.")
        report["project_sha256"] = sha256(project)
    except ResourceBlocked as exc:
        report.update(execution_status="blocked_environment_resource_budget", error=str(exc), traceback=traceback.format_exc())
    except NumericalFailed as exc:
        report.update(execution_status="failed_numerical", error=str(exc), traceback=traceback.format_exc())
    except Exception as exc:
        report.update(execution_status="failed_interface_or_solver", error=str(exc), traceback=traceback.format_exc())
    finally:
        if app is not None:
            try:
                app.save_project(str(project))
                report["project_exists"] = project.is_file()
                if project_freezer is not None:
                    report["saved_project_snapshot"] = project_freezer(app, project, folder)
                elif project.is_file():
                    frozen = folder / "native3d_saved_before_release.aedt"
                    shutil.copy2(project, frozen)
                    report["saved_before_release_project"] = frozen.name
                    report["saved_before_release_project_sha256"] = sha256(frozen)
            except Exception as exc:
                report["project_save_error"] = str(exc)
            try:
                app.desktop_class.release_desktop(close_projects=True, close_on_exit=True)
            except Exception as exc:
                report["desktop_release_error"] = str(exc)
        report["elapsed_seconds"] = time.monotonic() - started
        dump(folder / "test_report.json", {"source_model": config["source_model"], "tests": report["tests"]})
        dump(folder / "results.json", report)
    return report


def summary_tests(config, cases):
    by_name = {case["label"]: case for case in cases}
    tests = []
    if "mesh_fine" not in by_name or "mesh_medium" not in by_name:
        return tests
    fine = by_name["mesh_fine"]["source_Rac_ohm_per_axial_m"]
    tolerance = config["tolerances"]["mesh_and_sensitivity_relative"]
    tests.append(check("three_mesh_finest_Rac_change", abs(fine / by_name["mesh_medium"]["source_Rac_ohm_per_axial_m"] - 1), tolerance))
    for label in ("return_distance", "outer_domain"):
        if label in by_name:
            tests.append(check(label + "_Rac_sensitivity", abs(by_name[label]["source_Rac_ohm_per_axial_m"] / fine - 1), tolerance))
    lengths = [case for case in cases if case["label"].startswith("length_")]
    previous = fine
    for case in lengths:
        current = case["source_Rac_ohm_per_axial_m"]
        tests.append(check(case["label"] + "_Rac_sensitivity", abs(current / previous - 1), tolerance))
        previous = current
    reference = round_wire_rac(config)
    if reference is not None and lengths:
        tests.append(check("longest_source_Rac_Bessel_calibration", abs(lengths[-1]["source_Rac_ohm_per_axial_m"] / reference - 1),
                           config["tolerances"]["rac_relative"]))
    return tests


def prerequisite_check(config, prerequisite):
    if len(config["strand_centers_m"]) == 1:
        return
    if prerequisite is None:
        raise ValueError("Additional strand cases require a prior native single-strand full acceptance report.")
    report = json.loads(Path(prerequisite).read_text(encoding="utf-8"))
    if report.get("full_physical_acceptance") != "passed" or report.get("execution_status") != "passed":
        raise ValueError("Prerequisite has not passed native full physical acceptance; scale-up remains not_run.")


def interface_failure_streak(out, config_hash, implementation_hash):
    """Count failures for unchanged input/code only; an explicit repair starts a new audit."""
    matching = []
    for path in out.parent.glob("*/results.json"):
        if path.parent == out:
            continue
        try:
            report = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        if report.get("source_config_sha256") == config_hash and report.get("implementation_sha256") == implementation_hash:
            matching.append((path.stat().st_mtime_ns, report))
    count = 0
    for _, report in sorted(matching, key=lambda pair: pair[0], reverse=True):
        if not report.get("execution_status", "").startswith("failed_interface"):
            break
        count += 1
    return count


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/native3d_q1_straight.json")
    parser.add_argument("--out", required=True, help="Unique output directory; existing paths are rejected.")
    parser.add_argument("--mode", choices=["pilot", "suite", "preflight"], default="pilot")
    parser.add_argument("--mesh-index", type=int, choices=[0, 1, 2], default=0,
                        help="Pilot only: select coarse/medium/fine resolution without running the suite.")
    parser.add_argument("--prerequisite", help="Prior full native acceptance results.json for multi-strand cases.")
    parser.add_argument("--prepared-output", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out = out.resolve()
    if args.prepared_output:
        marker = out / "runner_parameters.json"
        if not marker.is_file() or any(path.name not in {"runner_parameters.json", "launcher_stdout.txt"} for path in out.iterdir()):
            raise FileExistsError("Prepared output is not a fresh runner-owned directory; previous artifacts will not be overwritten.")
    else:
        out.mkdir(parents=True, exist_ok=False)
    try:
        config = read_config(config_path)
        if args.mode != "preflight":
            prerequisite_check(config, args.prerequisite)
    except Exception as exc:
        state = "blocked_environment_resource_budget" if isinstance(exc, NotImplementedError) else "failed_configuration_or_gate"
        dump(out / "results.json", {"run_id": out.name, "source_model": "native_3D_requested_case_preflight", "execution_status": state,
             "full_physical_acceptance": "not_run", "solver_started": False, "error": str(exc),
             "reason": "native_curved_geometry_not_implemented" if isinstance(exc, NotImplementedError) else "invalid_config_or_unsatisfied_prerequisite",
             "traceback": traceback.format_exc()})
        dump(out / "process_status.json", {"process_exit_code": 1, "finished_UTC": datetime.now(timezone.utc).isoformat()})
        return 1
    archive_snapshot(out, config_path)
    report = {"run_id": out.name, "source_model": config["source_model"], "mode": args.mode,
              "execution_status": "running", "full_physical_acceptance": "not_run", "cases": [], "tests": [],
              "source_config_sha256": sha256(config_path), "implementation_sha256": sha256(Path(__file__)),
              "physical_conventions": "SI, exp(+j omega t), RMS,20C,no independent external field",
              "geometry_implementation": {"straight": "implemented_pending_actual_field_acceptance", "curved_or_helical": "not_run_unsupported_in_this_entrypoint"},
              "scope": config["scope"], "prerequisite": args.prerequisite, "started_UTC": datetime.now(timezone.utc).isoformat()}
    dump(out / "parameters.json", {**config, **physical_geometry(config)})
    (out / "model_assumptions.md").write_text(config["scope"] + "\n\nFluxTangential exterior is a controlled truncated magnetic boundary, not an unbounded-space assertion. Far terminals share an ideal 0V scalar reference; physical termination conductors are not modelled.\n", encoding="utf-8")
    versions = {}
    for package in ("pyaedt", "numpy", "scipy", "psutil"):
        with contextlib.suppress(importlib.metadata.PackageNotFoundError):
            versions[package] = importlib.metadata.version(package)
    dump(out / "environment.json", {"python": sys.version, "platform": platform.platform(), "packages": versions,
                                    "requested_AEDT": "2025.2 Student", "RAM": available_ram(), "source_git_commit": subprocess.run(
                                        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()})
    started, exit_code = time.monotonic(), 1
    try:
        variations = case_variations(config, "suite" if args.mode in {"preflight", "suite"} else "pilot")
        if args.mode == "pilot":
            variations = [(f"mesh_{('coarse', 'medium', 'fine')[args.mesh_index]}", copy.deepcopy(config),
                           config["mesh_lengths_m"][args.mesh_index])]
        if args.mode == "preflight":
            report["cases"] = [{"label": label, "resource_preflight": preflight(case_config, mesh)} for label, case_config, mesh in variations]
            report["execution_status"] = "preflight_only"
            report["solver_started"] = False
            exit_code = 0
        else:
            failures = interface_failure_streak(out, report["source_config_sha256"], report["implementation_sha256"])
            report["consecutive_unchanged_interface_failures"] = failures
            if failures >= config["maximum_consecutive_interface_failures"]:
                report["solver_started"] = False
                raise ResourceBlocked("Unchanged native interface failed twice; an explicit code/input repair or a new approach is required.")
            with (out / "run_log.txt").open("w", encoding="utf-8", buffering=1) as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                for label, case_config, mesh in variations:
                    print("START", label, "mesh_length_m", mesh, flush=True)
                    result = run_one(case_config, mesh, out / label)
                    result["label"] = label
                    report["cases"].append(result)
                    print("FINISH", label, result["execution_status"], flush=True)
                    dump(out / "checkpoint.json", report)
                    if result["execution_status"] != "passed":
                        report["execution_status"] = result["execution_status"]
                        report["stop_reason"] = "gate_failure; next geometries are not_run, no automatic interface retry"
                        break
                else:
                    report["tests"] = summary_tests(config, report["cases"]) if args.mode == "suite" else []
                    report["execution_status"] = "passed" if all(test["execution_status"] == "passed" for test in report["tests"]) else "failed_numerical"
                    if args.mode == "suite" and report["execution_status"] == "passed":
                        report["full_physical_acceptance"] = "passed"
                exit_code = 0 if report["execution_status"] == "passed" else 1
    except ResourceBlocked as exc:
        report.update(execution_status="blocked_environment_resource_budget", error=str(exc), reason="interface_attempt_budget", traceback=traceback.format_exc())
    except Exception as exc:
        report.update(execution_status="failed_interface_or_execution", error=str(exc), traceback=traceback.format_exc())
    finally:
        report["elapsed_seconds"] = time.monotonic() - started
        report["finished_UTC"] = datetime.now(timezone.utc).isoformat()
        dump(out / "results.json", report)
        dump(out / "test_report.json", {"source_model": config["source_model"], "tests": report["tests"],
                                        "case_tests": {case["label"]: case.get("tests", []) for case in report["cases"]}})
        dump(out / "process_status.json", {"process_exit_code": exit_code, "finished_UTC": report["finished_UTC"]})
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
