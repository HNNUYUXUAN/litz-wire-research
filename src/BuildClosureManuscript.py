"""Rebuild manuscript and scientific figures from frozen JSON/CSV only.

No Wolfram, AEDT, CUDA, matrix assembly or physical solve is called. The only
third-party import is the already installed matplotlib plotting runtime.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "8"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["MPLBACKEND"] = "Agg"

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs/report/pre_manuscript_closure_20261005"
SELECTION = "outputs/closure_20261005_compute_pin_01/selection.json"
INDEX = "outputs/closure_20261005_compute_pin_01/index_after.json"
PEEC_FINAL = "outputs/closure_20261005_peec_m80_l064_self12p10_01/closure_peec_summary.json"
RT0_FINAL = "outputs/closure_20261005_rt0_campaign_collect_01/closure_rt0_collect_summary.json"
APHI = "outputs/closure_fem3_diagnostics_20261005_readonly_02/diagnostic_summary.json"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024**2), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


class Build:
    def __init__(self, out):
        self.out = out
        self.sources = {}
        self.figures = []
        self.checks = []
        self.warnings = []
        self.font = None
        for name in ("figures", "figure_data", "tables"):
            (out / name).mkdir(parents=True, exist_ok=True)

    def source(self, relative):
        p = ROOT / relative
        row = {"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p), "bytes": p.stat().st_size}
        self.sources[row["path"]] = row
        return row

    def load(self, relative):
        self.source(relative)
        return json.loads((ROOT / relative).read_text(encoding="utf-8-sig"))

    def csv(self, relative):
        self.source(relative)
        with (ROOT / relative).open(encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))

    def link(self, path, label=None):
        path = Path(path)
        path = path if path.is_absolute() else ROOT / path
        target = os.path.relpath(path, self.out).replace("\\", "/")
        return f"[{label or path.name}](<{target}>)"

    def table(self, relative, rows):
        p = self.out / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        keys = list(dict.fromkeys(k for row in rows for k in row))
        with p.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=keys)
            writer.writeheader()
            for row in rows:
                writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()})
        return p.relative_to(ROOT).as_posix()

    def md(self, name, text):
        (self.out / name).write_text(text.rstrip() + "\n", encoding="utf-8")

    def check(self, name, passed, evidence):
        self.checks.append({"name": name, "passed": bool(passed), "evidence": evidence})

    def figure(self, figure, fid, title, caption, rows, source_paths, units, scope, routes):
        from matplotlib import pyplot as plt
        data_path = self.table("figure_data/" + fid + ".csv", rows)
        images = {}
        for extension in ("png", "svg", "pdf"):
            p = self.out / "figures" / (fid + "." + extension)
            figure.savefig(p, dpi=180, bbox_inches="tight", facecolor="white")
            images[extension] = p.relative_to(ROOT).as_posix()
        plt.close(figure)
        paths = list(dict.fromkeys(source_paths))
        self.figures.append({"figure_id": fid, "title": title, "caption": caption, "path": images["png"],
              "formats": images, "data_path": data_path, "routes": routes,
              "source_files": [self.source(p) for p in paths], "units": units, "scope": scope,
              "transformations": "Exact frozen scalar/CSV selection; display unit conversions or ratios stated in CSV columns and caption; no physical solve."})


def md_table(headers, rows):
    def cell(x):
        return str(x).replace("|", "\\|").replace("\n", " ")
    return "| " + " | ".join(headers) + " |\n| " + " | ".join("---" for _ in headers) + " |\n" + "\n".join(
        "| " + " | ".join(cell(x) for x in row) + " |" for row in rows)


def unwrap_degrees(values):
    """Keep the first archived principal phase and select adjacent 360-degree lifts."""
    result = []
    for value in values:
        if result:
            value += 360 * round((result[-1] - value) / 360)
        result.append(value)
    return result


def plotting(b):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import font_manager, pyplot as plt
    for p in (Path(os.getenv("LITZ_CJK_FONT",str(Path(os.environ.get("WINDIR","/usr/share/fonts"))/"Fonts/simsun.ttc"))),):
        if p.is_file():
            font_manager.fontManager.addfont(str(p))
            b.font = font_manager.FontProperties(fname=str(p)).get_name()
            break
    if not b.font:
        raise RuntimeError("Set LITZ_CJK_FONT to the installed SimSun font file")
    plt.rcParams.update({"font.family": b.font, "font.size": 10, "axes.titlesize": 12,
          "axes.labelsize": 10, "axes.unicode_minus": False, "svg.fonttype": "path",
          "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
          "grid.color": "#e2e5e8", "grid.linewidth": .65, "figure.constrained_layout.use": True,
          "pdf.fonttype": 42, "lines.linewidth": 1.6})
    return plt


def make_figures(b, selection):
    plt = plotting(b)
    blue, gold, orange, grey = "#2b5c8a", "#a97818", "#bd5b36", "#414950"
    # Q1 analytic profile, already evaluated by the analytic source run.
    p = "outputs/closure_20261005_analytic_01/radial_profile.csv"
    profile = b.csv(p)
    rows = [{"r_mm": float(z["r_m"])*1e3, "abs_J_A_per_mm2": float(z["Abs_J_A_m2"])*1e-6,
             "phase_principal_rad": float(z["phase_rad"]), "phase_principal_deg": math.degrees(float(z["phase_rad"])), "source_run_id": "closure_20261005_analytic_01",
             "source_model": "Bessel_50_digit_analytic"} for z in profile]
    for row, phase in zip(rows, unwrap_degrees([z["phase_principal_deg"] for z in rows])):
        row.update(phase_unwrapped_deg=phase, phase_transform="continuous nearest 360-degree lift; first radius retains archived principal phase")
    b.check("Q1_phase_unwrap_preserves_phasor", all(abs(math.remainder(z["phase_unwrapped_deg"]-z["phase_principal_deg"], 360)) < 1e-10 for z in rows),
            {"rows": len(rows), "transformation": "integer multiples of 360 degrees only"})
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    ax[0].plot([r["r_mm"] for r in rows], [r["abs_J_A_per_mm2"] for r in rows], color=blue)
    ax[1].plot([r["r_mm"] for r in rows], [r["phase_unwrapped_deg"] for r in rows], color=gold)
    for a in ax: a.set_xlabel("半径 r (mm)")
    ax[0].set_ylabel("|Jz| (A/mm², RMS)"); ax[1].set_ylabel("Jz 连续解缠相位 (°)")
    fig.suptitle("Q1 单圆线解析电流密度")
    b.figure(fig, "q1_analytic_profile", "Q1 解析幅值与相位", "D=2 mm、200 kHz、20 A RMS；曲线为已归档 Bessel 解，未调用场解。相位按相邻半径加减360°连续解缠，CSV保留原主值相位；解缠不改变复相量。", rows,
             [p, "outputs/closure_20261005_analytic_01/results.json"], {"r": "mm", "J": "A/mm² RMS", "phase": "degrees"}, "isolated_long_round_conductor_internal_impedance", ["closure_analytic"])
    # Independent 2D disk calibration.
    p = "outputs/rerun_20261005_fem2_report/convergence.csv"
    raw = b.csv(p)
    rows = [{"nodes": int(r["nodes"]), "h_over_a": float(r["h/a"]), "Rac_ohm_per_m": float(r["Rac_ohm_per_m"]),
             "Rac_relative_error": float(r["Rac_error"]), "power_relative_error": float(r["power_error"]),
             "source_run_id": "rerun_20261005_fem2_report", "source_model": "2D_diffusion_FEM"} for r in raw]
    fig, a = plt.subplots(figsize=(7.4, 3.8))
    for k, lab, color, marker in [("Rac_relative_error", "Rac 解析误差", blue, "o"), ("power_relative_error", "功率积分差", gold, "s")]:
        a.loglog([r["nodes"] for r in rows], [r[k] for r in rows], marker=marker, label=lab, color=color)
    a.axhline(.01, color=grey, linestyle="--", label="Rac 初始门槛 1%")
    a.set(xlabel="节点数", ylabel="相对差（无量纲）", title="二维圆盘校准的三档细化"); a.legend(fontsize=9)
    b.figure(fig, "q1_fem2_convergence", "二维圆盘三档细化", "353/1389/5573 节点；独立圆盘扩散问题，不含真实有限端区。", rows, [p],
             {"nodes": "count", "error": "dimensionless", "Rac": "ohm/axial m"}, "2D_scalar_diffusion_calibration_only", ["fem2"])
    # Scalar PEEC case records and finite sensitivity comparisons.
    peec = []
    paths = []
    for pin in selection["route_pins"]:
        if pin["route"].startswith("closure_peec_m"):
            p = f"outputs/{pin['run_id']}/closure_peec_summary.json"
            case = b.load(p)["cases"][0]
            keys = ["case_id", "run_id", "source_model", "m", "length_m", "q", "ag", "pg", "filaments", "nominal_copper_area_m2",
                    "Rac_ohm_per_axial_m", "Rdc_ohm_per_axial_m", "Rac_over_Rdc", "loss_W_per_axial_m", "Bessel_equal_area_Rac_ohm_per_m", "Bessel_Rac_relative_error"]
            peec.append({k: case.get(k) for k in keys}); paths.append(p)
    b.table("tables/peec_cases.csv", peec)
    final = b.load(PEEC_FINAL)
    rows = [r for r in peec if r["q"] == 4 and r["ag"] == 10]
    fig, a = plt.subplots(figsize=(7.6, 4))
    for m, color, marker in [(40, blue, "o"), (80, orange, "s")]:
        group = sorted([r for r in rows if r["m"] == m], key=lambda z: z["length_m"])
        a.plot([r["length_m"] for r in group], [1e3*r["Rac_ohm_per_axial_m"] for r in group], marker=marker, color=color, label=f"m={m}, {group[0]['filaments']} 细丝")
        a.axhline(group[0]["Bessel_equal_area_Rac_ohm_per_m"]*1e3, color=color, linestyle=":", label=f"m={m} 实际面积 Bessel")
    a.set(xlabel="轴向长度 (m)", ylabel="Rac (mΩ/轴向 m)", title="有限长度纵向 PEEC 的 Rac")
    a.legend(fontsize=8.8)
    b.figure(fig, "peec_length", "纵向 PEEC 长度敏感性", "纵轴聚焦数值差异；各 m 使用本档实际铜面积的 Bessel 参照。横向涡流环路与端部重分布不在此基函数内。", rows, paths,
             {"length": "m", "Rac": "ohm/axial m; display mΩ/m"}, "finite_length_longitudinal_volume_filament_PEEC", [p["route"] for p in selection["route_pins"] if p["route"].startswith("closure_peec_m")])
    labels = {"length_016_032": "m40 长度 0.16→0.32 m", "length_032_064": "m40 长度 0.32→0.64 m",
              "length_064_128": "m40 长度 0.64→1.28 m", "fine_length_032_064": "m80 长度 0.32→0.64 m",
              "fine_length_064_128": "m80 长度 0.64→1.28 m", "mutual_q4_to6": "m40 互项积分 q4→q6",
              "mutual_q6_to8": "m40 互项积分 q6→q8", "fine_mutual_q4_to6": "m80 互项积分 q4→q6",
              "fine_mutual_q6_to8": "m80 互项积分 q6→q8", "self_10p8_to12p10": "m40 自项积分 10/8→12/10",
              "fine_self_10p8_to12p10": "m80 自项积分 10/8→12/10", "spatial_l032": "长度0.32 m：m40→m80",
              "spatial_l064": "长度0.64 m：m40→m80", "spatial_l128": "长度1.28 m：m40→m80"}
    rows = [{**r, "display_label": labels[r["id"]], "source_run_id": final["run_id"], "source_model": final["source_model"]} for r in final["comparisons"]]
    shown = [r for r in rows if r.get("execution_status") == "passed"]
    fig, a = plt.subplots(figsize=(9.5, 5.5))
    for i, r in enumerate(shown):
        a.scatter(r["Rac_relative_change"], i, marker="o", color=blue)
        if r.get("complex_current_relative_change") is not None:
            a.scatter(r["complex_current_relative_change"], i, marker="x", color=orange)
    a.set_xscale("log"); a.set_yticks(range(len(shown)), [r["display_label"] for r in shown]); a.invert_yaxis()
    a.axvline(.01, color=grey, linestyle="--"); a.set(xlabel="相邻档相对差（无量纲，对数尺度）", title="PEEC 长度、互项积分、自项积分与横截面敏感性")
    a.scatter([], [], marker="o", color=blue, label="Rac 相对差"); a.scatter([], [], marker="x", color=orange, label="复电流 L2 相对差")
    a.legend(fontsize=9)
    b.figure(fig, "peec_sensitivity", "PEEC 有限验收的相对差", "虚线为本专项 1% 门槛；未运行 1.28 m 的记录仍保留在 CSV，空值不绘成零。m40/m80 铜面积略不同，跨 m 是当前实际几何的离散敏感性。", rows,
             [PEEC_FINAL], {"all_changes": "dimensionless"}, "longitudinal_scope_only", ["closure_peec_m80_l064_q4_s12p10"])
    # RT0 after-processing of preserved face currents.
    rt0 = b.load(RT0_FINAL)
    rtrows = [{k: z[k] for k in ("case_id", "run_id", "cells", "n", "q", "recomputed_loss_W", "recomputed_input_W", "archived_GMRES_iterations")} for z in rt0["recomputed_cases"]]
    for z in rtrows: z.update(source_model=rt0["source_model"], net_transport_current_RMS_A=0, external_B_RMS_T=.001)
    b.table("tables/rt0_cases.csv", rtrows)
    fig, ax = plt.subplots(1, 2, figsize=(10.5, 4))
    group = [z for z in rtrows if z["q"] == 14]
    ax[0].plot([z["cells"] for z in group], [z["recomputed_loss_W"]*1e3 for z in group], marker="o", color=blue, label="q14")
    z = next(z for z in rtrows if z["q"] == 18)
    ax[0].scatter(z["cells"], z["recomputed_loss_W"]*1e3, marker="s", facecolors="none", edgecolors=orange, s=65, label="q18")
    ax[0].set(xlabel="体素数", ylabel="外加场焦耳损耗 (mW)", title="固定长方体空间细化（聚焦尺度）"); ax[0].legend()
    comps = rt0["comparisons"]
    vals = [c["loss_relative_change"] for c in comps]
    ax[1].semilogy(range(3), vals, "o", color=blue, label="损耗相对差")
    ax[1].semilogy(range(3), [c["tolerance"] for c in comps], "_", markersize=20, color=grey, label="各比较门槛")
    ax[1].set_xticks(range(3), ["n16→20", "n20→24", "q14→18"])
    ax[1].set(ylabel="相对差（无量纲）", title="空间与积分的独立比较"); ax[1].legend(fontsize=9)
    rtpaths = [RT0_FINAL]
    for z in rtrows:
        rtpaths.extend([f"outputs/{z['run_id']}/cases/{z['case_id']}/case.json", f"outputs/{z['run_id']}/cases/{z['case_id']}/face_fluxes.csv", f"outputs/{z['run_id']}/closure_rt0_parameters.json"])
    b.figure(fig, "rt0_spatial_quadrature", "RT0 外场长方体细化", "1×1×2 mm 铜长方体，Bz=1 mT RMS，净输运电流为零。q18 原 null/failed 摘要保留；图中量为已通过的冻结面通量 CSV 后处理。", rtrows + [{"case_id": c["before_case_id"]+"->"+c["after_case_id"], **c,
              "source_run_id": Path(RT0_FINAL).parent.name, "source_model": rt0["source_model"]} for c in comps], rtpaths,
             {"loss": "W; display mW", "changes": "dimensionless", "B": "T RMS", "transport": "A RMS"}, "fixed_cuboid_imposed_field_only", ["closure_rt0_campaign_collect"])
    # Same-model CPU/GPU equivalence, historical run evidence only.
    grows, gpaths = [], []
    for m in (40, 80):
        p = f"outputs/closure_20261005_gpu_m{m}_01/gpu_case.json"
        z = b.load(p)
        if "case" in z: z = z["case"]
        if "L_matrix_relative_error" not in z:
            pin = next(pn for pn in selection["route_pins"] if pn["route"] == f"closure_gpu_m{m}")
            z = pin["metrics"]
        grows.append({**{k: z[k] for k in ("filaments", "L_matrix_relative_error", "current_relative_error", "linear_residual", "power_residual", "CPU_assembly_seconds", "GPU_far_assembly_copyback_seconds")},
                      "source_run_id": f"closure_20261005_gpu_m{m}_01", "source_model": "physical_longitudinal_PEEC_CPU_GPU_cross_validation"})
        gpaths.extend([p, f"outputs/closure_20261005_gpu_m{m}_01/test_report.json"])
    fig, a = plt.subplots(figsize=(7.7, 4))
    for k, lab, color, marker in [("L_matrix_relative_error", "体积分 L 矩阵", blue, "o"), ("current_relative_error", "复电流", orange, "s"), ("linear_residual", "线性残差", gold, "^")]:
        a.semilogy([z["filaments"] for z in grows], [z[k] for z in grows], marker=marker, label=lab, color=color)
    a.axhline(1e-10, color=grey, linestyle="--", label="对应门槛 1e−10")
    a.set(xlabel="纵向细丝自由度", ylabel="相对误差（无量纲）", title="归档 CPU/GPU 同模型等价性"); a.legend(fontsize=9)
    b.figure(fig, "gpu_equivalence", "CPU/GPU 同矩阵与复电流误差", "1264/5024 自由度；误差说明算法等价，未用于推断 GPU 物理准确性或真实换位性能。成稿阶段没有运行 CUDA。", grows, gpaths,
             {"errors": "dimensionless", "times": "seconds"}, "same_longitudinal_model_equivalence_only", ["closure_gpu_m40", "closure_gpu_m80"])
    # Preserved A-phi failures normalized by their historical gates.
    ap = b.load(APHI)
    arows = [{"nodes": z["nodes"], "metric": g["id"], "actual": g["actual"], "tolerance": g["tolerance"],
              "actual_over_tolerance": g["actual"]/g["tolerance"], "original_execution_status": g["execution_status"],
              "source_run_id": z["source_run_id"], "source_model": g["source_model"]} for z in ap["cases"] for g in z["historical_gates"]]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8))
    for a, metric, color in zip(axes, ("J_Bessel", "phi", "gauge"), (blue, orange, gold)):
        group = [z for z in arows if z["metric"] == metric]
        a.semilogy([z["nodes"] for z in group], [z["actual_over_tolerance"] for z in group], "o-", color=color)
        a.axhline(1, color=grey, linestyle="--"); a.set(xlabel="原网格节点数", ylabel="实际值 / 原门槛", title=metric)
    fig.suptitle("三维 A–φ 圆柱的原始验收边界")
    b.figure(fig, "aphi_original_gates", "A–φ 三档原场的门槛比", "门槛分别为 J 解析误差 0.01、φ 1e−8、规范 0.001；比值≤1才通过。数值来自原保存场的只读诊断，不修订失败报告。", arows, [APHI],
             {"ratios": "dimensionless", "nodes": "count"}, "original_copper_cylinder_diagnostics_not_curved_Litz", ["closure_fem3_diagnostics"])
    # Valid sampled resource curves; explicitly exclude q18 polluted aggregate.
    resrows, respaths = [], []
    fig, a = plt.subplots(figsize=(8.4, 4))
    for run, lab, color in [("closure_20261005_gpu_m80_01", "GPU m80（归档）", blue),
                            ("closure_20261005_peec_m80_l064_self12p10_01", "PEEC m80 self", orange),
                            ("closure_20261005_rt0_n24_q14_01", "RT0 n24 q14", gold)]:
        p = f"outputs/{run}/resource_curve.csv"
        records = b.csv(p)
        group = [{"elapsed_seconds": float(z["elapsed_seconds"]), "working_GiB": float(z["kernel_working_bytes"])/1024**3,
                  "cpu_seconds": float(z["cpu_seconds"]), "source_run_id": run, "source_model": "sampled_owned_process_tree_resource_observation"} for z in records]
        a.plot([z["elapsed_seconds"] for z in group], [z["working_GiB"] for z in group], color=color, label=lab)
        resrows.extend(group); respaths.extend([p, f"outputs/{run}/resource_summary.json"])
    a.set(xlabel="各任务经过时间 (s)", ylabel="抽样进程树工作集 (GiB)", title="高配计算期间的可用资源曲线"); a.legend(fontsize=9)
    b.figure(fig, "valid_resource_curves", "有归属证据的抽样工作集", "这是归档高配任务抽样曲线，不是当前32 GiB设备复跑。q18混合PID曲线、旧wrapper未知退出、未观测瞬时峰值均不替代为零。", resrows, respaths,
             {"working": "GiB", "elapsed": "s", "cpu": "s"}, "sampled_owned_process_tree_not_exact_continuous_peak", ["closure_gpu_m80", "closure_peec_m80_l064_q4_s12p10", "closure_rt0_n24_q14"])
    # Historical true-circle seven-strand short test, separate from closure polygon.
    p = "outputs/ansys_short_20261005_calibrated20A_final/results.json"
    ansys = b.load(p)
    z = next(z for z in ansys["solves"] if z["label"] == "verify_20A")["data"]
    rows = []
    for name, v in z["winding_currents_RMS_A"].items():
        if name.startswith("W_Copper_strand"):
            value = complex(v["real"], v["imag"])
            rows.append({"strand_id": int(name.rsplit("_", 1)[-1]), "Re_I_RMS_A": value.real, "Im_I_RMS_A": value.imag,
                         "Abs_I_RMS_A": abs(value), "phase_deg": math.degrees(math.atan2(value.imag, value.real)),
                         "source_run_id": ansys["run_id"], "source_model": ansys["source_model"]})
    seven_total = sum(complex(r["Re_I_RMS_A"], r["Im_I_RMS_A"]) for r in rows)
    b.check("historical_seven_export_current_sum", len(rows) == 7 and abs(seven_total-20)/20 < 1e-8,
            {"rows": len(rows), "sum_ReIm_A": [seven_total.real, seven_total.imag], "source_run_id": ansys["run_id"]})
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.7))
    ax[0].plot([r["strand_id"] for r in rows], [r["Abs_I_RMS_A"] for r in rows], "o-", color=blue)
    ax[0].axhline(20/7, color=grey, linestyle=":"); ax[0].set(ylabel="|Ii| (A RMS)")
    ax[1].plot([r["strand_id"] for r in rows], [r["phase_deg"] for r in rows], "s-", color=orange); ax[1].set(ylabel="Ii 相位 (°)")
    for a in ax: a.set_xlabel("物理股线 ID")
    fig.suptitle("七股 Ansys 原生圆粗网格短测的复电流")
    b.figure(fig, "ansys_seven_currents", "历史七股端口短测的幅值与相位", "共同端电压下实际求解20 A，704单元原生圆粗网格；虚线20/7只是均流参照。本轮42边形基线的失败不等于这张图的纯网格变化。", rows, [p],
             {"current": "A RMS", "phase": "degrees"}, "historical_704_element_native_circle_port_short_test_only", ["ansys_port"])
    # Current phase is not replaceable by magnitude, even for 640 strands.
    p = "outputs/3d_20261005_delivery_data_v4/coax640_complex_currents.csv"
    raw = b.csv(p)
    rows = [{"strand_id": int(z["strand_id"]), "Re_I_RMS_A": float(z["Re_I_RMS_A"]), "Im_I_RMS_A": float(z["Im_I_RMS_A"]),
             "Abs_I_RMS_A": float(z["Abs_I_RMS_A"]), "phase_deg": math.degrees(float(z["phase_rad"])),
             "source_run_id": "full_20261005_coax640", "source_model": "archived_2D_coax640_WXF_case3"} for z in raw]
    total = sum(complex(z["Re_I_RMS_A"], z["Im_I_RMS_A"]) for z in rows)
    b.check("coax640_export_current_sum", len(rows) == 640 and abs(total-20)/20 < 1e-8, {"rows": len(rows), "sum_ReIm_A": [total.real, total.imag]})
    fig, ax = plt.subplots(2, 1, figsize=(10, 5.4), sharex=True)
    ax[0].plot([z["strand_id"] for z in rows], [z["Abs_I_RMS_A"] for z in rows], linewidth=.9, color=blue)
    ax[0].axhline(20/640, color=grey, linestyle=":"); ax[0].set(ylabel="|Ii| (A RMS)")
    ax[1].scatter([z["strand_id"] for z in rows], [z["phase_deg"] for z in rows], s=5, color=orange)
    ax[1].set(xlabel="物理股线 ID", ylabel="主值相位 (°)")
    fig.suptitle("二维 640 股共同端电压解的电流幅值与相位")
    exporter = "outputs/3d_20261005_delivery_data_v4/source_snapshot/src/stages/delivery_data.wl"
    if not (ROOT / exporter).is_file(): exporter = "src/stages/delivery_data.wl"
    b.figure(fig, "coax640_currents", "640 股幅值与主值相位", "归档导出器明确选源cases[[3]]（最细原网格，受控回流）；虚线20/640为参照。相位使用−180°至180°主值，图上的跳跃不代表股线断续。", rows,
             [p, "outputs/3d_20261005_delivery_data_v4/coax640_public_data.json", "outputs/full_20261005_coax640/test_report.json", exporter],
             {"current": "A RMS", "phase": "degrees"}, "translation_invariant_2D_coax640_common_voltage_not_finite_curved_Litz", ["coax640"])
    return {"peec": peec, "peec_final": final, "rt0": rt0, "gpu": grows, "aphi": ap, "seven": ansys,
            "coax640_current_sum_ReIm": [total.real, total.imag]}


def make_documents(b, selection, index, d):
    ref = b.load("configs/reference_values.json")["values"]
    geometry = b.load("outputs/closure_20261005_geometry_01/geometry_data.json")
    dtm = b.load("outputs/closure_20261005_geometry_01/DTM_data.json")
    tests640 = b.load("outputs/full_20261005_coax640/test_report.json")["tests"]
    gates640 = {z["id"]: z for z in tests640 if z["id"] in ("640_fine_mesh_change", "640_return_distance_sensitivity", "640_outer_domain_sensitivity")}
    release = b.load("outputs/closure_20261005_high_release_01/results.json")
    recovery = b.load("outputs/closure_20261005_gpu9856_recovery_01/results.json")
    b.source("references/来源与许可.md")
    fine = next(z for z in d["peec"] if z["m"] == 80 and z["ag"] == 12)
    source = lambda p, label=None: b.link(p, label)
    figs = {z["figure_id"]: z for z in b.figures}
    def image(fid):
        z = figs[fid]
        return f"![{z['title']}](figures/{fid}.png)\n\n{z['caption']} 图数据：{source(z['data_path'])}。"
    peec_table = md_table(["细丝", "L (m)", "q / self", "Rac (mΩ/m)", "Rac/Rdc", "P (W/m)", "run_id"],
          [[z["filaments"], z["length_m"], f"{z['q']} / {z['ag']},{z['pg']}", f"{z['Rac_ohm_per_axial_m']*1e3:.8f}", f"{z['Rac_over_Rdc']:.8f}", f"{z['loss_W_per_axial_m']:.8f}", z["run_id"]] for z in d["peec"]])
    b.md("manuscript.md", f"""# Litz 线建模的有限数值验收与成稿证据

## 摘要

本研究包在统一 RMS 相量约定下建立了单圆线解析、二维扩散与多股共端场解、几何与加性场路、纵向 PEEC、完整 RT0 体素及 CPU/GPU 数值对照。降配前有限计算专项的 **43 项任务已形成终态**；其中通过结论限于明确模型，接口失败、数值失败、未运行依赖及未知 CLI 退出均保留。固定单圆线截面的纵向 PEEC 在长度、互项积分、自项积分和横向离散的已运行比较中达到 1% 门槛；固定铜长方体、独立外场、零净输运的 RT0 空间相邻变化为 0.6551% 与 0.3629%，积分变化为 1.55×10⁻⁸。二维 640 股已有受控网格/回流/外域证据，实际换位 Litz 的三维性能排名仍没有被这些结果证明。

高配计算已释放，成稿阶段只读缓存、重建图表及编写文稿。本文区分原始单档验收、后处理汇总验收、执行退出和模型适用范围；缓存一致性通过不升级物理结论。

## Abstract

This manuscript consolidates a bounded computational campaign for reproducible Litz-wire modeling. Forty-three tasks reached explicit terminal states. Analytical and two-dimensional calibrations, finite longitudinal PEEC sensitivities, fixed-cuboid RT0 imposed-field refinement, and CPU/GPU equivalence are supported within their stated scopes. Native three-dimensional Ansys probes and the new two-dimensional fixed-mesh validation attempts failed and remain archived. These results do not establish the performance ranking of realistic transposed Litz structures. Post-downgrade preparation uses frozen JSON/CSV data without new physical solves.

## 1. 问题、工况与可比较量

计算采用 SI 单位、exp(jωt) 与 RMS 相量，σ=5.8×10⁷ S/m、μr=1、f=200 kHz、20 ℃。主输运工况总电流为20 A，不指定独立外加场；各股沿途绝缘、端部并联，解共同电压和各股复电流，不能强制 Ii=20/N 来证明均流。所有“每米”指轴向米。真实弧长 ℓi 进入 Rdc=(ΣσAi/ℓi)⁻¹ 与铜体积 ΣAiℓi。

Q1 D=2 mm 保留为校准，其名义铜面积为{ref['Q1_area_mm2']:.9f} mm²，Jdc={ref['Q1_Jdc_A_per_mm2']:.9f} A/mm²，超过4 A/mm²约束。后续 Q2 的名义铜截面至少5 mm²，等铜实心参照按实际选定铜面积建立。640×0.100 mm 的理想圆面积为{ref['candidate_640x0_1mm_area_mm2']:.9f} mm²；64边形实际二维面积约5.01848 mm²，不能混用这两个面积。

结果需同时给出绝对 Rac、Rac/Rdc、损耗、铜体积、弧长代价和复电流偏差。独立外场存在时，外场损耗不除以20²作为内禀导体电阻。原题解释及公式来源：{source('docs/建模约定与解析基准.md')}；数值基准：{source('configs/reference_values.json')}。

## 2. 解析与二维校准

孤立长直圆线采用 κ=(1+j)/δ，δ=(πfμσ)⁻¹ᐟ²，Jz(r)=IκI0(κr)/(2πaI1(κa))，Zint/长度=κI0(κa)/(2πaσI1(κa))。Zint 只含内部阻抗，不含由回流决定的外部电感。归档50位解析和12项回归通过，δ={ref['delta_mm']:.12f} mm，Rdc={ref['Q1_Rdc_mohm_per_m']:.12f} mΩ/m，Rac={ref['Q1_Rac_mohm_per_m']:.12f} mΩ/m，Rac/Rdc={ref['Q1_Rac_Rdc']:.12f}，P={ref['Q1_P_W_per_m']:.12f} W/m。

{image('q1_analytic_profile')}

独立二维圆盘扩散解从单位边界场求得后按总复电流归一化。353、1389、5573节点的三档细化中，最细 Rac 解析相对误差为1.79233×10⁻⁶，功率积分差为3.06800×10⁻⁶。它验证孤立圆柱内场的标量模型，没有有限端场。

{image('q1_fem2_convergence')}

二维共端多股采用 Az 与未知公共端场，保留股内邻近分布与股间复电流。冻结640股测试报告23项通过：最细两档 Rac 变化{gates640['640_fine_mesh_change']['actual']*100:.6f}%，回流距离变化{gates640['640_return_distance_sensitivity']['actual']*100:.6f}%，外域变化{gates640['640_outer_domain_sensitivity']['actual']*100:.6f}%，各门槛1%。回流损耗与束内损耗须单独报告。来源：{source('outputs/full_20261005_coax640/test_report.json')}。

{image('coax640_currents')}

## 3. 场路、轨迹与换位边界

共端增广系统为 Zi+e=V1、1ᵀi=It。Q=IN−11ᵀ/N，在解唯一时均流条件为 Q[(It/N)Z1+e]=0；没有独立外场时等价于阻抗行和相同。该条件属于指定线性模型，不是连续三维几何定理。相量相位必须保留。

本专项几何使用400/800/1600轴向采样，记录物理股线ID、位置周期、间隙、曲率、弧长、Rdc和铜体积；60项检查通过，但旧wrapper代码1、内核实际退出未保存，执行状态保持unknown。现有7/14/28合成分段测试的 Ztot=ΣΔzk PkᵀZkPk 是加性置换模型：同一组带权块重排不改变总和。因此其均流不能支持传统多级 Litz 与跨层结构的真实性能排名。几何原始量：{source('outputs/closure_20261005_geometry_01/geometry_data.json')}；合成模型：{source('outputs/closure_20261005_geometry_01/DTM_data.json')}。

传统多级 Litz 必须保留为强基线。名义等铜不等于轴向每米铜体积相等；结构改善须大于相关数值不确定性并由真实电磁模型或实验支持。

## 4. 有限长度纵向 PEEC

本路线以纵向均匀体积细丝求有限长度部分电感和共同端口；1264与5024细丝分别对应m40/m80横截面。它保留有限长度核与外部部分电感，但基函数省略横向涡流环路和端部重分布。因面积/边界离散变化，m40/m80分别使用各自实际铜截面的Bessel参照，不把不同几何误差归为纯网格误差。

{image('peec_length')}

{image('peec_sensitivity')}

最终5024细丝、0.64 m、q4、自项12/10的Rac为{fine['Rac_ohm_per_axial_m']*1e3:.9f} mΩ/轴向m，Rac/Rdc={fine['Rac_over_Rdc']:.9f}，损耗{fine['loss_W_per_axial_m']:.9f} W/轴向m，与本档等面积Bessel差{fine['Bessel_Rac_relative_error']*100:.6f}%。两个粗长度增量、一个细长度增量、q4/6/8与自项10/8→12/10均满足专项1%门槛。按有限计划，已通过后不追加1.28m；未运行档保持not_run。最细模型电流 L2 不均匀度是体积分细丝量，不能当作沿途绝缘物理股线的不均流排名。

{peec_table}

完整精度表：{source((b.out/'tables/peec_cases.csv').relative_to(ROOT))}；汇总源：{source(PEEC_FINAL)}。旧m80 q6/q8的wrapper1与native退出未知保留；科学数值被独立缓存一致性核查读取，并未补造process exit 0。

## 5. RT0 完整体素的外场校准

RT0算例是1×1×2 mm均质铜长方体、1 mT RMS独立Bz、零净输运，使用面通量自由度及连续性/端口约束，三轴 FFT 核装配与 GMRES。它的功率平衡包含外场做功，不作为20A输运Rac。专项参数文件优先于保留的generic项目20A默认。

{image('rt0_spatial_quadrature')}

8192、16000、27648体素 q14 的冻结重算损耗分别为0.927463、0.933539、0.936927 mW；相邻变化0.655090%与0.362916%，均低于1%。27648体素q18与q14的损耗相对差1.54941×10⁻⁸、复面通量差1.39291×10⁻⁸，低于0.1%积分门槛。各档35次GMRES；守恒与功率核查由保存的CSV重构。原q18摘要的null指标与failed_numerical未改写，新的66项后处理验收另列。结论限于固定长方体外场模型，没有曲线掩膜Litz、独立边界通量或真实端场交叉验证。

来源：{source(RT0_FINAL)}。因q18旧监控聚合混入非物理PID，其精确全程内存峰值/CPU未知；保存排除证据而不画混合曲线。

## 6. GPU 等价性和资源

{image('gpu_equivalence')}

5024自由度的L矩阵误差7.48149×10⁻¹⁶、复电流误差7.78082×10⁻¹⁴，所验算法门槛1e−10。CPU/GPU组装、上传、编译和求解耗时分别归档，不能将不同批次或不同算法的时间混合为严格加速比。9856细丝历史单档检查通过并恢复复电流，原20108档资源停止与whole-run异常退出仍保留；缺失的矩阵、复端电压和连续场没有恢复值。恢复源：{source('outputs/closure_20261005_gpu9856_recovery_01/results.json')}。

{image('valid_resource_curves')}

## 7. 三维 A–φ 与 Ansys 的失败结果

{image('aphi_original_gates')}

原A–φ圆柱三档1683/3672/9108节点按历史J、φ、规范门槛核查。制造解通过与物理圆柱失败并存：边界值满足及导数交叉核查通过不能证明内部φ/规范精度。诊断仅抽样侧面和至多128节点导数，并非全域最大量。原场和网格均已保存，未通过项限制三维模型结论。来源：{source(APHI)}。

{image('ansys_seven_currents')}

历史七股原生圆704单元短测已实际求解共同端口20A，电流残差2.71156×10⁻¹⁵，功率差3.04114×10⁻¹⁵；它只有单档端口证据。本专项native探针r1/r2均在J named-expression加载时失败，未启动native场解；不再追加第三次接口修订。本专项2D两次42边形尝试均在两个单位电压基解的实际网格坐标/连接一致性处失败：1544真实二维三角形处于Student上限内，但未形成最终20A/common-port验证；后续细档、回流、外域停止。原生圆704基线与本轮42边形参考几何分别保留，不能将差异当纯网格敏感性。

Student体64k、表面8k、二维2k与四核上限属于该路线执行边界；启发式预估不替代真实网格统计。二维已计算场、网格、解实体保留，锁标记排除另列；native r2另有工程design缺失，不能作为可恢复的完整场解工程。J/B共享字段接口不可得只记not_run_field_export，未填造采样值。四次失败与后继停止状态见{source((b.out/'failure_boundaries.md').relative_to(ROOT))}。

## 8. 成稿结论与交接

本包支持解析/二维/纵向PEEC/固定长方体RT0各自范围内的复现与数值验收，保存三维A–φ及Ansys的可解释失败。它尚不支持满足5mm²的真实换位结构性能排名、热温升/绝缘可制造性保证或有限端三维FEM–PEEC一致性声明。

43项终态矩阵见[专项验收矩阵](acceptance_matrix.md)，63条冻结路线见[来源与再分发](sources_and_redistribution.md)，轻设备操作见[设备交接](device_handoff.md)。冻结选择：{source(SELECTION)}；高配释放：{source('outputs/closure_20261005_high_release_01/results.json')}。所有图表均可从冻结JSON/CSV重建，不重算物理。
""")
    # Exact terminal state and original route status are separate columns.
    taskrows = []
    for task, row in selection["task_finalizations"].items():
        taskrows.append({"task_id": task, "final_status": row["final_status"], "source_run_ids": row["source_run_ids"],
                         "reason": row["reason"], "original_execution_status": row.get("original_execution_status"),
                         "original_physical_acceptance_status": row.get("original_physical_acceptance_status", row.get("physical_acceptance_status"))})
    b.table("tables/task_acceptance_matrix.csv", taskrows)
    route_rows = [{"route": route, "selected_run_id": row.get("selected_run_id"), "execution_status": row.get("execution_status"),
                   "physical_acceptance_status": row.get("physical_acceptance_status"), "source_model": row.get("source_model"), "scope": row.get("scope")}
                  for route, row in index["routes"].items()]
    b.table("tables/frozen_routes.csv", route_rows)
    tasks_md = md_table(["task_id", "专项终态", "原执行/物理状态", "证据与范围"], [[z["task_id"], z["final_status"],
              f"{z['original_execution_status'] or '按原报告'} / {z['original_physical_acceptance_status'] or '按原报告'}",
              "; ".join(source(f"outputs/{run}/results.json", run) if (ROOT/f"outputs/{run}/results.json").exists() else source(f"outputs/{run}", run) for run in z["source_run_ids"]) + "。" + z["reason"]] for z in taskrows])
    routes_md = md_table(["冻结路线", "run_id", "execution_status", "physical_acceptance_status", "source_model"],
              [[z["route"], source(f"outputs/{z['selected_run_id']}", z["selected_run_id"]), z["execution_status"], z["physical_acceptance_status"], z["source_model"]] for z in route_rows])
    b.md("acceptance_matrix.md", f"# 专项验收矩阵\n\n共{len(taskrows)}任务、{len(route_rows)}冻结路线；本专项新增31路线。终态表示有限工作已封口，不代表物理全通过。completed_scope_pass必须连同reason和原状态阅读；unknown不是0。缓存与导出验收为数据层。\n\n## 43项任务\n\n{tasks_md}\n\n## 冻结路线\n\n{routes_md}\n\n数据：[task_acceptance_matrix.csv](tables/task_acceptance_matrix.csv)、[frozen_routes.csv](tables/frozen_routes.csv)。选择与索引SHA见[来源表](source_manifest.json)。")
    # Failure reproduction is archive-only: historical commands are not run.
    failruns = ["closure_20261005_ansys_probe_r1", "closure_20261005_ansys_probe_r2", "closure_20261005_ansys_2dmesh_01", "closure_20261005_ansys_2dmesh_02"]
    failures = []
    for run in failruns:
        result = b.load(f"outputs/{run}/results.json")
        status = b.load(f"outputs/{run}/process_status.json")
        errors = [z["error"] for z in result.get("cases", []) if z.get("error")]
        saves = [z["project_save_error"] for z in result.get("cases", []) if z.get("project_save_error")]
        failures.append({"run_id": run, "source_model": result.get("source_model"), "execution_status": result.get("execution_status"),
                         "physical_acceptance_status": result.get("physical_acceptance_status", "not_verified"),
                         "full_physical_acceptance": result.get("full_physical_acceptance"), "solver_started": result.get("solver_started"),
                         "process_exit_code": status.get("process_exit_code"), "failure": result.get("failure_reason", result.get("error")) or errors,
                         "original_save_errors": saves})
    for p in ("outputs/closure_20261005_ansys_process_audit_01/owned_process_exit.json",
              "outputs/closure_20261005_ansys_probe_r2/release_and_retained_artifacts.json",
              "outputs/closure_20261005_ansys_2dmesh_01/mesh_factor_1/post_release_freeze_manifest.json",
              "outputs/closure_20261005_ansys_2dmesh_02/mesh_factor_1/native_project_results_manifest.json"):
        b.source(p)
    b.table("tables/ansys_failure_attempts.csv", failures)
    failure_md = md_table(["run_id", "原执行", "退出", "物理状态", "原错误文件"], [[z["run_id"], z["execution_status"], z["process_exit_code"], z["physical_acceptance_status"], source(f"outputs/{z['run_id']}/run_log.txt")] for z in failures])
    b.md("failure_boundaries.md", f"""# 失败边界与最小复现

这里的最小复现指读取原始失败证据和重建诊断图。设备降配后不启动原场解。原求解脚本、配置、已取得的工程数据与source_snapshot按run_id保留，工程完整性失败亦保留；新研究另开明确任务和新run_id，现专项的修订预算不重新打开。

## Ansys两次接口与两次二维尝试

{failure_md}

native r1使用未定义named quantity，r2按已装接口以fundamental J修订，仍在LoadNamedExpressions失败，solver_started=False。两次预算用尽；Q1粗档/套件/七股按failed prerequisite停止。二维scalar模式只跳过已知J/B字段加载、保留真实端口/功率/网格；第一次基解坐标/连接不一致，第二次恢复revert_to_initial_mesh=True仍未通过严格identity。两次同样得到1544真实三角形而未通过20A验证。细档、回流、外域无accepted scalar case，保持not_run。

锁标记 *.semaphore 仅为工程冻结排除项；mesh/field/solution实体不因此丢弃。mesh01在release后完整复制，mesh02保留排除清单与逐件SHA。旧真圆704短测不改写，42边形参数与独立Wolfram参考另有来源绑定。

native r2保存报告明确为failed_missing_expected_design：其3976字节.aedt虽存在，却未通过design完整性检查，也没有已求解场。应保留加载错误、CLC与原工程字节供接口诊断，不能将它列为完整可恢复场工程。二维mesh01的原pre-release锁复制失败保留，后取得的post_release_freeze_manifest独立列；mesh02保存native_project_results_manifest与锁标记排除清单，不覆盖第一次失败。来源：{source('outputs/closure_20261005_ansys_probe_r2/release_and_retained_artifacts.json')}；{source('outputs/closure_20261005_ansys_2dmesh_01/mesh_factor_1/post_release_freeze_manifest.json')}；{source('outputs/closure_20261005_ansys_2dmesh_02/mesh_factor_1/native_project_results_manifest.json')}。

四次退出来源：{source('outputs/closure_20261005_ansys_process_audit_01/owned_process_exit.json')}。历史creationtime未保存，审计只支持保存PID、日志SHA与当前absence；不宣称历史创建时间已验收。

## A–φ原场

读{source(APHI)}的historical_gates即可复现三档J/φ/gauge门槛比。完整mesh、u/ψ、A/φ/J与抽样导数CSV位于同目录。制造解通过不替代圆柱失败；侧壁J与至多128节点导数最大量只覆盖标明的样本。

## 执行未知与资源污染

geometry、A–φ诊断、m80 q6/q8的原wrapper=1，native/kernel实际退出未知；wrapper_resource_observation单列，不写0。q18保存resource_identity_exclusions，精确全程peak/CPU未知。数据后处理重新读取原CSV通过时，原summary failed/null仍保留。9856缓存只恢复保存的复电流/标量；20108历史资源边界与whole-run异常未抹除。

## 不含求解的重建命令

在具有既有matplotlib的Python运行时执行：

```powershell
& $PythonWithMatplotlib -B src/BuildClosureManuscript.py --figures-only
```

该脚本读冻结JSON/CSV、做单位转换和图表绘制；不读WXF矩阵、不装配算子、不调用CUDA/AEDT/Wolfram。图源、原门槛及SHA在figures_manifest.json，失败说明保持独立。
""")
    b.md("device_handoff.md", f"""# 成稿设备交接

用户选定的当前设备为32 GiB主存、16个OS逻辑处理器、8 GB GPU。成稿执行上限是8 CPU线程、24 GiB进程工作预算、8 GiB系统空闲储备；本阶段不使用CUDA。OS逻辑数与Wolfram $ProcessorCount=8应分别记录，8线程上限不等于物理机器只有8个逻辑处理器。

高配释放证据为{source('outputs/closure_20261005_high_release_01/results.json')}，其物理状态mixed_scopes_and_preserved_failures。旧释放报告的严格low32/no-GPU实际切换待验口径保留为历史记录；当前交付环境口径按用户选择，不改写旧报告。当前设备的实际环境验收由新的成稿运行报告提供，本文不将高配成功替代为低设备仿真能力证明。

## 轻量可执行内容

本目录静态图和表来自原JSON/CSV：解析径向数据、二维误差/电流、PEEC案例与比较、RT0 CSV汇总、GPU原等价误差、A–φ诊断、有效抽样资源曲线。无需重新求解。Notebook采用archive模式读图、读表、显示已求值Output，Markdown是独立可读成稿。

```powershell
$env:OMP_NUM_THREADS='8'
$env:OPENBLAS_NUM_THREADS='8'
$env:MKL_NUM_THREADS='8'
$env:CUDA_VISIBLE_DEVICES=''
& $PythonWithMatplotlib -B src/BuildClosureManuscript.py
```

脚本由工程根目录派生输入/输出，目录可含空格。已有PyAEDT venv中的matplotlib可作为纯绘图运行时；不导入PyAEDT，不打开Desktop，不需要其许可证求解。bundled Python缺matplotlib时不自动安装，也不将其失败标成绘图成功。

## 保存与恢复

必须保留冻结index/selection、43任务终态、17原始数值案例、JSON/CSV/WXF、必要完整场/mesh/端口工程、源快照、SHA及真实process_status。校验仅发现损坏，不能证明物理正确。大文件恢复要确认Git LFS实体，不能拿pointer充当模型。

迁移后依次检查环境→完整性→JSON/CSV读回→图表轻量重建→Notebook打开/静态Output→中文字体与路径含空格恢复。包级原数据清单、恢复演练和最终SHA由主控另行生成，本文不冒充这些包级检查。新增附件：[图清单](figures_manifest.json)、[来源清单](source_manifest.json)、[43任务矩阵](acceptance_matrix.md)。

封存的Ansys失败不追加第三次，A–φ/真实端场/真实换位/热实验列为后续研究边界。现设备交付能够写稿和回放档案，不由此承诺可复跑全部高配模型。
""")
    # Source and redistribution are an inspectable candidate inventory, not a licence grant.
    repo_meta = b.load("references/github_repository_metadata_2026-10-03.json")
    repo_rows = [{"category": "external_repository_metadata_only", "name": z["repository"], "path_or_url": z["url"],
                  "recorded_license": z.get("license"), "redistribution_status": "具体提交与LICENSE尚须复核；本项目未整体继承其许可", "evidence": "references/github_repository_metadata_2026-10-03.json"} for z in repo_meta["repositories"]]
    literature_rows = []
    for p in ("references/literature_20261004/manifest.json", "references/literature_20261004_supplement/manifest.json", "references/literature_20261004_delivery/manifest.json"):
        manifest = b.load(p)
        for z in manifest.get("items", manifest.get("files", [])):
            literature_rows.append({"category": "literature_or_manufacturer", "name": z.get("title", z.get("id", z.get("file"))),
                  "path_or_url": z.get("file", z.get("path", z.get("source_url"))), "recorded_license": z.get("license_note", z.get("copyright", "unknown")),
                  "redistribution_status": "unknown（未从当前manifest取得统一再分发授权）" if "CC BY" not in str(z.get("license_note")) else "仅该文件按原CC BY声明及署名条件处理",
                  "evidence": p})
    candidates = [{"category": "original_problem", "name": "原题ZIP、problem原件和摘录", "path_or_url": "originals/; problem/", "recorded_license": "unknown", "redistribution_status": "用户本地研究可保留；对外再分发权unknown", "evidence": "references/来源与许可.md"},
                  {"category": "project_authored", "name": "新文稿、图表、项目实现", "path_or_url": "docs/report/pre_manuscript_closure_20261005/; src/", "recorded_license": "未新增整体开源许可", "redistribution_status": "候选分享前检查隐私、来源及原文件许可；不以外仓库LICENSE覆盖整包", "evidence": "references/来源与许可.md"},
                  {"category": "licensed_native_software_artifacts", "name": "Wolfram/Ansys工程、许可证相关环境", "path_or_url": "outputs/", "recorded_license": "软件/Student授权独立", "redistribution_status": "候选分享保留模型来源；安装包/账号/许可证/个人环境路径不列为可公开内容", "evidence": "references/来源与许可.md"}, *repo_rows, *literature_rows]
    b.table("tables/redistribution_candidates.csv", candidates)
    redist = md_table(["类别", "名称/文件", "历史许可/来源", "再分发候选状态"], [[z["category"], z["name"], z["recorded_license"], z["redistribution_status"]] for z in candidates])
    b.md("sources_and_redistribution.md", f"""# 来源与再分发候选清单

本地研究保存、数据完整性和再分发许可是不同事项。本文件只整理本包已有来源记录，不构成新增许可或对外发布。原题、论文、厂商资料的再分发unknown必须保留；公开可下载不自动授权再分发。外部仓库license标签来自既有只读元数据，应以具体提交及LICENSE核验，移植时保留版权；不以BSD/MIT/GPL/MPL标签覆盖整个交接包。

核心依据：{source('references/来源与许可.md')}。仓库日期和许可是历史记录，未以这次成稿声称重新核查网络最新版本或运行外部代码。项目公式来自本地建模约定和实现；本稿未冒充对全部第三方论文完成独立复现实验。

{redist}

完整机器可读候选表：[redistribution_candidates.csv](tables/redistribution_candidates.csv)。本文献批次含重复传递副本，各manifest保留，不把副本计作独立文献。P08原接收稿的CC BY声明只适用于该文件；其余未确认授权文件保留unknown。

## 证据与生成

静态图清单：[figures_manifest.json](figures_manifest.json)，每图含source_files SHA、单位、模型scope和CSV数据。全文输入：[source_manifest.json](source_manifest.json)，包含冻结index/selection、原run_id/source_model路径。未取到的数据不补零；资源未知不补wrapper0。图像与派生表可以单独携带，但应同时携带来源与适用范围。

高配数值冻结的17案例/914检查/256文件SHA通过属于缓存一致性；没有替代物理精度、当前环境验收或全文再分发许可。
""")
    catalogs = []
    for z in b.figures:
        catalogs.append(f"## {z['figure_id']} — {z['title']}\n\n{z['caption']}\n\n![{z['title']}](figures/{z['figure_id']}.png)\n\nCSV：{source(z['data_path'])}；格式：PNG/SVG/PDF；单位：`{json.dumps(z['units'], ensure_ascii=False)}`。\n\n来源：" + "; ".join(source(s["path"]) + " (`" + s["sha256"] + "`)" for s in z["source_files"]) + "。")
    b.md("figure_catalog.md", "# 科学图与源映射\n\n每张图由冻结JSON/CSV轻量重建；单位转换保留在CSV列名和图注。\n\n" + "\n\n".join(catalogs))
    b.md("README.md", "# 2026-10-05 成稿包\n\n[主文稿](manuscript.md) · [43任务验收矩阵](acceptance_matrix.md) · [失败边界](failure_boundaries.md) · [设备交接](device_handoff.md) · [来源与再分发](sources_and_redistribution.md) · [图源目录](figure_catalog.md)。\n\n机器可读输入来源见[source_manifest.json](source_manifest.json)，Notebook嵌图入口为[figures_manifest.json](figures_manifest.json)。科学图同时提供PNG、SVG、PDF；原始数值源不在此目录内改写。\n\n重建：`python -B src/BuildClosureManuscript.py`（使用既有matplotlib运行时；8线程CPU，不求解）。")
    b.check("all_43_terminal_tasks_exported", len(taskrows) == 43, {"count": len(taskrows)})
    b.check("63_frozen_routes_exported", len(route_rows) == 63, {"count": len(route_rows)})
    b.check("no_Ansys_failed_attempt_promoted", all(z["process_exit_code"] == 1 and not z["physical_acceptance_status"].startswith("passed") for z in failures), failures)


def main():
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Restored repository root, including paths with spaces")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--figures-only", action="store_true")
    args = parser.parse_args()
    ROOT = args.root.resolve()
    out = args.output.resolve() if args.output else ROOT / "docs/report/pre_manuscript_closure_20261005"
    allowed = (ROOT / "docs/report").resolve()
    if not out.is_relative_to(allowed):
        raise ValueError("Output must remain in this project's new docs/report tree")
    out.mkdir(parents=True, exist_ok=True)
    b = Build(out)
    b.source("src/BuildClosureManuscript.py")
    selection, index = b.load(SELECTION), b.load(INDEX)
    b.check("frozen_selection_SHA_matches_index", b.sources[SELECTION]["sha256"] == index["closure_selection"]["selection_sha256"],
            {"actual": b.sources[SELECTION]["sha256"], "expected": index["closure_selection"]["selection_sha256"]})
    import warnings
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        data = make_figures(b, selection)
        if not args.figures_only: make_documents(b, selection, index, data)
    b.warnings = sorted(set(str(z.message) for z in caught))
    b.check("no_missing_CJK_glyph_warning", not any("Glyph" in z and "missing" in z for z in b.warnings), b.warnings)
    for path, row in list(b.sources.items()):
        b.check("source_unchanged:"+path, sha(ROOT/path) == row["sha256"], row["sha256"])
    write_json(out / "figures_manifest.json", {"schema_version": 1, "source_model": "frozen_JSON_CSV_scientific_figure_rebuild",
               "figures": b.figures, "path_base": "repository_root", "font_family": b.font, "solver_calls": 0, "CUDA_calls": 0})
    write_json(out / "source_manifest.json", {"schema_version": 1, "inputs": list(b.sources.values()),
               "classification": "local_frozen_evidence; static_derived_output", "source_cutoff": "2026-10-05",
               "generation_time_UTC": datetime.now(timezone.utc).isoformat(), "no_physical_solve": True,
               "units_policy": "SI source values; explicit display conversion", "input_parameter_precedence": selection["input_parameter_precedence"]})
    if not args.figures_only:
        links, missing = [], []
        for p in out.glob("*.md"):
            for match in re.finditer(r"\[[^\]]*\]\((?:<([^>]+)>|([^)]+))\)", p.read_text(encoding="utf-8")):
                target = (match.group(1) or match.group(2)).split("#", 1)[0]
                if not target or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", target):
                    continue
                destination = (p.parent / target).resolve()
                entry = {"document": p.relative_to(ROOT).as_posix(), "target": target, "exists": destination.exists()}
                links.append(entry)
                if not entry["exists"]: missing.append(entry)
        write_json(out / "link_validation.json", {"source_model": "local_Markdown_target_existence_check", "links": links,
                  "checked_count": len(links), "missing": missing, "scope": "Full local source tree; lightweight delivery may mark archive-only links separately."})
        b.check("local_Markdown_links_exist", not missing, {"checked_count": len(links), "missing": missing})
    failed = [z for z in b.checks if not z["passed"]]
    write_json(out / "build_validation.json", {"execution_status": "failed" if failed else "passed", "physical_acceptance_status": "not_applicable_document_rebuild",
               "checks": b.checks, "failed_checks": len(failed), "figure_count": len(b.figures), "font_family": b.font,
               "warnings": b.warnings, "actual_python_version": platform.python_version(), "OS_logical_processors": os.cpu_count(),
               "execution_CPU_thread_cap": 8, "working_budget_GiB": 24, "system_free_reserve_GiB": 8,
               "resource_policy_scope": "requested cap; builder does not start computational solvers",
               "solver_calls": 0, "CUDA_calls": 0, "visual_QA": "PNG review pending parent visual inspection"})
    print(json.dumps({"output": out.relative_to(ROOT).as_posix(), "figures": len(b.figures), "failed_checks": len(failed), "warnings": b.warnings}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
