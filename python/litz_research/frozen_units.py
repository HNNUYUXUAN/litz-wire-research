"""Normalize frozen scientific JSON and infer explicit physical units."""
from decimal import Decimal
import json
import re

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


