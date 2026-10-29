"""Independent high-precision round-wire Bessel calibration, SI and RMS."""
import math
import platform
import time
import mpmath as mp
from .common import read, sha, write

def solve(parameters):
    with mp.workdps(50):
        scalar = lambda value: mp.mpf(str(value))
        f = scalar(parameters["frequency_Hz"])
        sigma = scalar(parameters["conductivity_S_per_m"])
        mu = 4 * mp.pi * mp.mpf("1e-7") * scalar(parameters["relative_permeability"])
        radius = scalar(parameters["q1"]["solid_diameter_m"]) / 2
        current = scalar(parameters["current_RMS_A"])
        delta = mp.sqrt(2 / (2 * mp.pi * f * mu * sigma))
        k = (1 + 1j) / delta
        impedance = k * mp.besseli(0, k * radius) / (2 * mp.pi * radius * sigma * mp.besseli(1, k * radius))
        rdc = 1 / (sigma * mp.pi * radius**2)
        density = lambda r: current * k * mp.besseli(0, k * r) / (2 * mp.pi * radius * mp.besseli(1, k * radius))
        integrated_current = 2 * mp.pi * mp.quad(lambda r: density(r) * r, [0, radius])
        power = 2 * mp.pi / sigma * mp.quad(lambda r: abs(density(r))**2 * r, [0, radius])
        low_k = mp.sqrt(1j * 2 * mp.pi * mp.mpf("0.001") * mu * sigma)
        low_z = low_k * mp.besseli(0, low_k * radius) / (2 * mp.pi * radius * sigma * mp.besseli(1, low_k * radius))
        values = dict(delta_mm=delta * 1000, Q1_Rdc_mohm_per_m=rdc * 1000,
                      Q1_Rac_mohm_per_m=mp.re(impedance) * 1000, Q1_Xint_mohm_per_m=mp.im(impedance) * 1000,
                      Q1_Rac_Rdc=mp.re(impedance) / rdc, Q1_P_W_per_m=current**2 * mp.re(impedance),
                      Q1_Jdc_A_per_mm2=current / (mp.pi * radius**2) / 1e6)
        diagnostics = dict(current_error=abs(integrated_current-current)/abs(current),
                           power_error=abs(power-current**2*mp.re(impedance))/(current**2*mp.re(impedance)),
                           low_frequency_error=abs(mp.re(low_z)/rdc-1))
        profile = [[float(radius*n/100), float(mp.re(density(radius*n/100))), float(mp.im(density(radius*n/100)))] for n in range(101)]
        return {k: float(v) for k,v in values.items()}, {k: float(v) for k,v in diagnostics.items()}, profile

def execute(root, output, overrides=None, case='tutorial'):
    import csv
    start = time.monotonic()
    p = read(root / "configs/reference_parameters.json")
    p.update(overrides or {})
    reference = read(root / "configs/reference_values.json")["values"]
    values, diagnostics, profile = solve(p)
    baseline = read(root / "configs/reference_parameters.json")
    is_reference = p == baseline
    checks = [{"name": key, "passed": abs(values[key]/reference[key]-1) < 1e-6} for key in
              ("delta_mm", "Q1_Rdc_mohm_per_m", "Q1_Rac_mohm_per_m", "Q1_Xint_mohm_per_m", "Q1_Rac_Rdc", "Q1_P_W_per_m")] if is_reference else []
    checks += [{"name": key, "passed": value < 1e-8} for key,value in diagnostics.items()]
    checks += [{"name": "passivity_and_phasor_sign", "passed": values["Q1_Rac_Rdc"] >= 1 and values["Q1_Xint_mohm_per_m"] > 0},
               {"name": "RMS_power_convention", "passed": math.isclose(values["Q1_P_W_per_m"], p["current_RMS_A"]**2*values["Q1_Rac_mohm_per_m"]/1000, rel_tol=1e-12)},
               {"name": "Q1_current_density_condition", "passed": math.isclose(values["Q1_Jdc_A_per_mm2"], p['current_RMS_A']/(math.pi*(p['q1']['solid_diameter_m']/2)**2)/1e6, rel_tol=1e-12)}]
    result = dict(run_id=output.name, source_model="isolated_long_round_conductor_internal_impedance_Bessel_solution",
                  execution_status="completed", physical_acceptance_status="passed" if all(c["passed"] for c in checks) else "failed",
                  parameters=p, values=values, diagnostics=diagnostics, checks=checks, elapsed_seconds=time.monotonic()-start,
                  environment={"python":platform.python_version(),"mpmath":mp.__version__},
                  inputs={name:sha(root/name) for name in ["configs/reference_parameters.json","configs/reference_values.json"]},
                  scope="Isolated straight round-wire internal impedance; SI, exp(+j omega t), RMS; 20 degrees C.")
    result['reference_comparison_applicable']=is_reference
    result['case']=case
    if case=='frequency-sweep':
        rows=[]
        for frequency in [1.,100.,1000.,10000.,100000.,200000.,1000000.]:
            quantities,errors,_=solve(p|{'frequency_Hz':frequency})
            rows.append({'frequency_Hz':frequency,'values':quantities,'diagnostics':errors})
        result['frequency_sweep']=rows
        result['checks'].append({'name':'sweep_integrals','passed':all(max(row['diagnostics'].values())<1e-8 for row in rows)})
        result['physical_acceptance_status']='passed' if all(c['passed'] for c in result['checks']) else 'failed'
    write(output / "results.json", result)
    with (output / "radial_current_density.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream); writer.writerow(["r_m","Re_J_A_per_m2","Im_J_A_per_m2"]); writer.writerows(profile)
    return result
