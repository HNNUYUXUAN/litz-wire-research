# Litz 线研究工具

本仓库提供 Litz 线分层建模、数值验证、科研数据和双语学术成稿。

**缪雨轩 · 淮南师范学院**

[English](README.md) · [学术文件](docs/editions.md) · [开发说明](docs/development.zh-CN.md) · [物理约定](docs/建模约定与解析基准.md) · [验收标准](tests/ACCEPTANCE.md)

## 使用入口

在 Python 3.11 或更新版本的虚拟环境中安装，以下命令从仓库根目录运行：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[documents,figures]"
litz-research doctor
litz-research run analytic --run-id analytical_example_01
litz-research data list
```

Python 轻量示例独立求解圆线 Bessel 内阻抗，积分复电流与焦耳功率，核验十二项解析条件。每次运行在 `outputs/<run-id>/` 保存参数、结果、诊断及径向电流密度。

## 模型与证据

研究路线包括解析、二维 FEM、共端场路、股线几何、有限长度纵向 PEEC、外场 RT0、三维 A–φ 诊断、Ansys 和 CPU/GPU 对照。执行状态与物理验收状态分别记录。各模型的适用范围、误差及三维校准和真实换位性能的研究边界见报告。

计算采用 SI 单位、RMS 相量和 `exp(+jωt)`。铜导体主工况为 200 kHz、20 A RMS、58 MS/m、相对磁导率 1、20 ℃。股线沿途绝缘，端部使用共同电压约束。RT0 算例采用独立外加磁场，报告外场损耗。

## 数据与学术文件

版本附件提供科研原始证据、图件输入及完整学术文件。`data/catalog.json` 记录数据集、分片及 SHA256。私有候选阶段通过已有 `gh` 身份读取附件。

```powershell
litz-research data fetch publication-inputs
litz-research data verify publication-inputs
litz-research build --run-id publication_example_01 --stage all
```

`manuscript/` 是中英文 Markdown 正文主源。统一构建生成报告、论文、章节稿、原生 Notebook、LaTeX，以及单栏和 IEEE 风格双栏 PDF。相应构建阶段需要 Wolfram 和 XeLaTeX。工具位置可通过 `LITZ_WOLFRAMSCRIPT`、`LITZ_XELATEX`、`LITZ_BIBTEX`、`LITZ_LATEXMK` 或 `litz.config.json` 配置。

`data fetch <数据集> --offline --cache <目录>` 支持离线恢复。附件缺失时，入口给出具体数据集及获取命令。模型计算通过 `run` 明确选择。

本版本是供研究者继续开发的工具快照。开发接口和测试方法见[开发说明](docs/development.zh-CN.md)，引用信息见 [CITATION.cff](CITATION.cff)。原创代码采用 MIT；原创文稿、图件、数据采用 CC BY 4.0；Notebook 代码单元与正文图件分别遵循对应许可。第三方材料采用自身许可，逐件记录见来源清单。
