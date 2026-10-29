# 方法、实现、测试与证据

| 路线 | 文献 key | 实现入口 | 独立检查 | 实际证据 |
| --- | --- | --- | --- | --- |
| 解析 | BESSEL | models/analytic/src/Q1Analytical.wl；python/litz_research/analytical.py | tests/Q1Analytical.wlt；电流与功率积分、直流极限 | Wolfram 校准与频率扩展案例 |
| 二维 FEM | FEMDOC、P04 | models/fem2/src/Physics.wl | Bessel 差异、独立积分、功率、历史网格序列 | rc2_route_fem2_01；fem2 数据集 |
| 共端场路 | P01、P02 | models/common_terminal/src/CoaxFEM.wl | 总复电流、线性残差、功率、独立 Maxwell 对照 | cross-solver 案例；common-terminal 数据集 |
| 几何 | P01、N01 | models/geometry/src/Physics.wl；TopologyCandidates.py | 间隙、弧长、体积、拓扑测试 | geometry 教程及数据集 |
| 纵向 PEEC | RUEHLI1974、P03 | models/peec/src/PEEC.wl | tests/ClosurePEEC.wlt；互易性、端口与功率 | rc2_route_peec_01；peec 数据集 |
| RT0 矢量 PEEC | RT1977、RUEHLI1974、GMRES1986 | models/rt0/src/VoxelPEEC.wl；VoxelOperator.wl | 连续性、真残差、功率、tests/VoxelOperator.wlt | RT0 教程与数据集 |
| A–φ | FEMDOC、GMRES1986 | models/aphi/src/stages/closure_fem3_diagnostics.wl | 保存场导数复现、原有势与规范门槛 | aphi-diagnostics 案例；aphi 数据集 |
| MCP／客户端 | AGENTTOOLS、PYAEDTMCP、PYAEDT、MCP、CODEX | automation/mcp/client.py；adapters/ansys/MCPMaxwellCase.py | 初始化、发现、实际调用及原生产物 | automation/examples/verification.json 六类案例 |
| GPU | CUDA | adapters/gpu/；adapters/wolfram/RunResearchCase.wls | 同矩阵、已知解、真残差、FFT 往返 | rc2_gpu_full_small_01；GPU 教程 |
| 成稿 | IEEEtran、XeLaTeX 与 Pandoc 3.13 | python/litz_research/latex_publication.py | 双语段落与文献身份、科学哈希及编译页面检查 | provenance/current-publication |

文献 key 由[统一题录](../references/README.zh-CN.md)解析。执行能力和物理范围分别记录；完整网格、长度、边界和几何研究使用各路线的独立验收。[案例记录](../automation/examples/verification.json)与 [Notebook 回执](../provenance/rc2/notebook_verification.json)绑定具体运行和保存产物。

[English](method-evidence-map.md)
