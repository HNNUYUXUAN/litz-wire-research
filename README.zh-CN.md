# Litz Wire Research：智能体驱动建模与仿真

**Miao Yuxuan / 缪雨轩 · Huainan Normal University / 淮南师范学院**

以 Codex 或其他支持 MCP 的智能体驱动可复核科学建模，以 Litz 线损耗提供完整研究案例。

[English](README.md) · [简体中文](README.zh-CN.md) · [Automation](automation/README.md) · [Publications](publications/README.md) · [Sources and acknowledgments](references/README.md)

```mermaid
flowchart LR
  Q[Research question] --> A[Codex / MCP agent]
  A --> M[Wolfram / Ansys MCP]
  M --> S[Saved model and bounded solver]
  S --> V[Independent scientific checks]
  V --> A
  V --> N[Notebook and research findings]
```

## 从研究问题到计算证据

让智能体建立模型、执行求解、检查守恒并诊断失败。项目提供研究工作流、固定 MCP 接入、确定性运行器及完整工具和求解记录。可从 Wolfram 解析校准或 Maxwell 原生七股案例开始。

- [Connect Codex](automation/harnesses/codex/README.md) · [Other MCP clients](automation/harnesses/generic/README.md)
- [Complete automation examples](automation/examples/README.md) · [Architecture and extension](docs/automation-architecture.md)
- [Reproduce](automation/workflows/reproduce/README.md) · [Extend a model](automation/workflows/extend-model/README.md) · [Compare solvers](automation/workflows/compare-solvers/README.md) · [Diagnose](automation/workflows/diagnose/README.md)

任务示例：“通过 Wolfram 与 Maxwell 建立七股绝缘铜线在 200 kHz、20 A RMS 和受控同轴回流下的模型。联立求解共同端电压与复电流，核对功率，并报告网格精度限制。”

[Actual execution and acceptance / 实际执行与验收](automation/examples/verification.json) · [Replay / 复现入口](automation/examples/README.md)

## Litz 案例中的研究认识

在 200 kHz、20 A RMS 下，2 mm 孤立圆线校准的交流内电阻为 20.0162 mΩ/m，焦耳损耗为 8.00648 W/m。共同端电压下仍可能存在复电流差异。有限长度纵向 PEEC 支持其模型范围内的损耗与敏感性比较；外场、几何和端区模型各自保留验收范围。

从成稿中的解析径向分布、640 股复电流和 PEEC 敏感性图进入研究；每张图关联数据、模型和验收证据。

![Round-wire radial current](publications/assets/zh-CN/q1_profile.png)

![Common-terminal strand currents](publications/assets/zh-CN/coax640_currents.png)

![PEEC sensitivity](publications/assets/zh-CN/peec_sensitivity.png)

## 运行第一个结果

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[automation]" -c automation/mcp/project-environment.lock
.venv/Scripts/litz-research.exe run analytic --case tutorial --run-id analytic_example_01
.venv/Scripts/litz-research.exe automation doctor
```

读取 outputs/analytic_example_01/results.json。计算采用 SI、exp(+jωt) 和 RMS；Q1 的电流密度为 6.3662 A/mm²，用作校准，Q2 最终设计要求至少 5 mm² 名义铜面积。

## 选择模型并继续研究

| Route | Research entry |
| --- | --- |
| Bessel calibration | [analytic](models/analytic/README.md) |
| 2D field calibration | [fem2](models/fem2/README.md) |
| Common-terminal currents | [common_terminal](models/common_terminal/README.md) |
| Geometry and transposition | [geometry](models/geometry/README.md) |
| Longitudinal PEEC | [peec](models/peec/README.md) |
| RT0 volume model | [rt0](models/rt0/README.md) |
| A–φ diagnostics | [aphi](models/aphi/README.md) |

每条路线包含双语交互 Notebook、可编辑教程输入、源码和验收。先复现小型案例，再研究网格、边界和长度；真实换位、有限端场和实验沿保存的诊断资料继续推进。

## 阅读、引用与复用

[Publications](publications/README.md) · [Datasets](docs/datasets.md) · [Citation guide](docs/citation-guide.md) · [Acknowledgments](ACKNOWLEDGMENTS.md) · [Licenses](LICENSES/README.md)

原创软件采用 MIT，原创文稿、图件与数据采用 CC BY 4.0；上游软件保留各自许可。Wolfram 与 Ansys 作为外部授权运行条件。候选仓库保持 Private，Release 保持 Draft。
