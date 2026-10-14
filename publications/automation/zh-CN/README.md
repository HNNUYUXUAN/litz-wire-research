# 智能体驱动的可复核建模与仿真：Wolfram–Ansys MCP 工作流及 Litz 案例

缪雨轩 · 淮南师范学院

- [01 研究问题与方法定位](#chapter-01)
- [02 软件连接与分层架构](#chapter-02)
- [03 任务身份与物理验收](#chapter-03)
- [04 建模、扩展与跨求解器比较](#chapter-04)
- [05 失败诊断与恢复](#chapter-05)
- [06 讨论与结论](#chapter-06)

<a id="abstract"></a>
## 摘要

本文提出以任务身份、保存源码和独立验收为基础的智能体建模与仿真流程，通过 Codex、Wolfram 和 Ansys MCP 将研究问题连接到可追溯的计算产物。工作流、执行适配与物理模型分别承担任务组织、软件连接及数值实现，并通过共同参数和结果接口协作。六类已有案例覆盖解析校准与 Notebook、Maxwell 原生建模求解、跨求解器比较、频率扩展、接口修复和 A–φ 失败诊断。七股共同端口比较的复电流相对 L2 差异为 0.0106814%，电阻相对差异为 0.00132823%；这些结果对应保存网格，空间与边界收敛尚待进一步检查。案例说明了协议状态、执行状态和物理验收如何共同支持研究接续。工作流、配置、适配代码、模型与运行记录共同构成可复用的研究材料。

关键词：Litz 线；分层验证；趋肤与邻近效应；共端场路；有限长度 PEEC；可复现数值研究

<a id="chapter-01"></a>
## 1 研究问题与方法定位

科学计算中的一次结果通常经历模型选择、参数解释、软件调用、求解、后处理和论述等环节。这些环节使用不同的数据表示与成功判据：工具能够连接并不说明模型设置正确，求解器正常退出也不说明电流、功率或离散误差满足研究要求。智能体参与建模时，需要把自然语言任务转化为可执行对象，并把每项判断连接到可保存、可检查的证据。

本研究以 Litz 线为实例，将 Codex 客户端、模型上下文协议 MCP、Wolfram Language 与 Ansys Electronics Desktop 组合为自动化研究流程。Codex 承担任务分解、源码编辑、工具调用和结果解释；MCP 提供工具发现与调用；项目运行器负责输入校验、源码身份、进程资源和产物保存；物理验收由独立计算与明确容差完成。该分工使交互中的探索能够转化为接手者可继续执行的研究对象。[1, 2, 3, 4]

Litz 建模对这一流程提出了具体要求。解析圆线、二维共端模型、有限长度 PEEC、外场 RT0 和三维 A–φ 保留的自由度与激励不同，结果需要按对应观测量解释。换位方法与多尺度建模文献提供了选择模型的基础；逐股复电流、实际铜面积和回流条件则决定不同实现能否直接比较。[5, 6, 7, 8]

本文研究三个工程问题：如何使客户端、工具和求解器共享可追溯的任务身份；如何把协议检查与物理验收组织成相互衔接的步骤；以及如何在代码扩展、接口错误和数值未通过时保留足够的恢复信息。评价材料来自 rc.2 的六类运行案例，结论对应这些案例实际覆盖的功能。客户端比较、人工操作耗时对照和大样本成功率需要另外设计实验。

<a id="fig-model_hierarchy"></a>
![Fig. 1](../../assets/zh-CN/model_hierarchy.png)

<p align="center">图 1. 分层模型与可比较观测量。</p>

输运模型按物理对象与观测量分组：圆线内场用于解析与二维校准，多股二维场路求解共同端口下的复电流，纵向 PEEC 检验有限长度效应。连线标明内部场校准或等面积电阻参照。RT0 外场损耗与三维 A–φ 场诊断各自构成独立研究范围。

<a id="chapter-02"></a>
## 2 软件连接与分层架构

系统分为研究工作流、执行适配和物理模型三个层次。工作流定义任务输入、操作顺序、检查依据和完成条件；适配层管理 Wolfram、AEDT 及数值后端的连接和执行；模型层保存公式、离散实现与路线测试。参数与产物通过共同任务接口流转，使命令行、Notebook 和 MCP 入口能够引用同一份已保存输入。

Wolfram 接入固定 AgentTools 2.2.0，来源提交为 9c99e2da5286c2ff7ac2298956107cd9334c6e90；既有验证记录使用 Wolfram 内核 15.0.0。工具提供代码执行、测试以及 Notebook 读写。内核计算和前端保存分别检查：数值表达式的返回值支持计算检查，Notebook 则通过前端打开、保存、重开与图形回读检查交付内容。[9]

Ansys 接入固定 PyAEDT-MCP 0.2.dev0，来源提交为 80ae7c3cb47e5de7b744a2898061510299d3bcef；建模适配采用 PyAEDT 1.8.0。服务器在独立 CPython 环境中运行，项目运行器启动并记录所属 AEDT Student gRPC 会话，再由 MCP 连接到该会话。AEDT 内置脚本环境与外部 CPython 具有不同的模块和对象接口，调用记录因此保留实际执行位置、工具名与返回值。[10, 11, 12]

默认配置采用本地标准输入输出传输，配置生成器也提供本机 HTTP 方式。安装材料固定上游来源、依赖和许可，连接诊断核对实际路径与工具清单。Wolfram、AEDT 及字体是运行环境的组成部分，版本和许可证条件随运行记录保存。其他 MCP 客户端可使用相同任务说明和协议接口，本文端到端记录对应 Codex 与标准 MCP 客户端桥接。

研究源码与软件连接之间保留清晰边界，使模型能够通过命令行独立运行，也便于定位失败发生在哪一层。客户端会话中产生的临时代码在正式验收前写入文件；运行清单记录文件哈希和参数。由此，后续修订能够通过代码差异和新的运行身份追溯到原始尝试。

<a id="chapter-03"></a>
## 3 任务身份与物理验收

任务提交包含案例、参数文件、运行号和资源策略。长任务先返回运行号，再将状态、日志和结果持续写入所属目录。客户端连接超时后查询该运行的状态，避免将通信中断解释为求解器停止并重复启动。结果同时记录执行状态与物理验收状态；取消、预算耗尽、程序异常和未收敛分别保留其原因。

运行器管理自己创建的进程树，依据进程创建身份实施取消和清理。项目预算为八个逻辑处理器、24 GiB 任务内存及 8 GiB 系统空闲内存；Student 案例另受其实际许可证限制，并请求四个求解器核。资源记录用于解释执行能力和中止原因，避免将受限运行与完整计算混在同一比较中。[13, 14]

接续前核对请求、源码快照和检查点身份。已有教程的恢复通过关联的新运行号重新执行保存输入；完整数值路线则按各自的检查点协议恢复。连接恢复、任务重启和数值检查点恢复具有不同含义，产物中的父任务关系与恢复说明保留这些差别。

物理约定从统一参数文件进入各执行入口：SI 单位、exp(jωt)、RMS 相量、20 ℃ 铜、σ=5.8×10⁷ S/m 和 μr=1。主要输运工况为 200 kHz、20 A RMS。沿途绝缘的股线在端部并联，共同端电压与总电流共同确定逐股复电流，所对应的增广系统见下式。

<a id="E04"></a>
$$
\begin{bmatrix} Z&-\mathbf1\\ \mathbf1^T&0\end{bmatrix}\begin{bmatrix}\mathbf i\\V\end{bmatrix}=\begin{bmatrix}-\mathbf e\\I_t\end{bmatrix}.\tag{1}
$$

式中的 Z 为所选模型的耦合阻抗矩阵，e 为独立感应电压项，i 与 V 为待求复电流和端电压。验收检查电流约束、功率平衡与离散敏感性，并核对回流和边界。Q1 的 2 mm 圆线承担解析校准，其直流电流密度约为 6.366 A/mm²；Q2 候选要求至少 5 mm² 名义铜截面。小股数端口案例用于验证接口和约束，其面积条件随案例保留。

<a id="fig-common_terminal"></a>
![Fig. 2](../../assets/zh-CN/common_terminal.png)

<p align="center">图 2. 多股共同端口与回流。</p>

各股沿途绝缘，在两端并联，逐股复电流由共同端电压及总电流约束求解。耦合矩阵 Z 与激励项 e 包含指定模型中的阻抗和场作用。受控回流承担反向总电流，并具有独立的端场。图中给出已知输入及待求复电流和电压。

<a id="chapter-04"></a>
## 4 建模、扩展与跨求解器比较

<a id="auto.04.heading1"></a>
### 4.1 Wolfram 校准与模型扩展

Wolfram 案例记录 MCP 初始化、工具发现和实际调用，并将解析计算、测试、图形及 Notebook 保存连接起来。单圆线基准在 200 kHz 下给出 Rac=20.0162 mΩ/m、损耗 8.00648 W/m；复电流积分与焦耳功率积分分别检验归一化及 RMS 约定。解析基准及原生 Notebook 的工具能力分别来自数学定义与 AgentTools 接口。[15, 9]

<a id="fig-q1_profile"></a>
![Fig. 3](../../assets/zh-CN/q1_profile.png)

<p align="center">图 3. 单圆线径向电流幅值与相位。</p>

铜导体直径 2 mm，200 kHz、20 A RMS。 (a) RMS 幅值；(b) 连续显示的相位。 相位显示采用径向连续提升，幅值保留 RMS 归一化。径向样本来自保存的 Bessel 解析数据。

频率扩展案例将单频解析实现扩展为频率研究，保存源码差异、参数和新运行结果，并检验积分、低频极限及原单频回归。该案例说明智能体修改可以通过确定性检查进入研究流程；其验收范围是解析实现及所测频率条件，后续增加材料频散或热耦合时需建立相应物理检查。

<a id="auto.04.heading2"></a>
### 4.2 Maxwell 建模、求解与交叉比较

Ansys 案例从运行器所属会话连接进入 MCP，完成小型七股 Maxwell 模型的材料、激励、求解和结果回读。rc2_maxwell_mcp_verified_01 及关联恢复运行通过端口与功率范围内的检查；协议探针自身的结果保留为协议状态。任务取消和新运行恢复另有独立记录，因而可以检查从任务身份到实际 AEDT 执行的对应关系。

Wolfram 与 Maxwell 比较采用直线绝缘七股、共同端电压、总电流约束及受控铜回流。对齐项目包括股数、多边形截面、股径、回流内外半径、外域半径、轴向深度、频率和总电流。保存比较中的逐股复电流相对 L2 差异为 0.0106814%，束内 Rac 相对差异为 0.00132823%；相应电阻为 318.290316 和 318.294544 mΩ/轴向m。

这些数值描述该案例的跨实现一致程度。两套实现使用独立网格和插值阶次，导体截面为 42 边形，回流分段也可能不同；Maxwell 使用一次自适应求解，尚未建立空间和边界收敛。案例铜面积小于 Q2 要求。因此，比较结果作为共同端口实现的交叉核查，进一步的精度估计需改变网格与边界并分析结果变化。

<a id="chapter-05"></a>
## 5 失败诊断与恢复

失败诊断案例保留了一次实际单位换算 API 错误及其修复。原 MCP 调用的传输返回并不能单独代表业务执行成功：工具可能以普通字符串返回错误，而协议层 isError 仍为 false。诊断需要检查实际返回内容、异常上下文和预期结果结构，随后修正 API 调用，并在新运行中核对成功响应及后续求解产物。

该修复保持原物理参数和约束。失败调用、修订后的调用与关联 Maxwell 结果构成对照，使读者能够识别修复发生在接口层。协议报告据此说明工具是否完成预期操作，物理报告则继续负责端口和功率验收；二者通过运行身份关联。

A–φ 案例展示另一类诊断。执行器读取已有场、势和导数诊断，记录 completed 执行状态，同时保留 failed_retained_phi_gauge 物理状态。采样参数和显示参数的修改只改变保存场的观察方式。原场输入、采样位置、诊断公式与验收门槛共同决定解释依据，后续修订需要回到势与规范条件的数值实现。[16]

<a id="fig-aphi_gates"></a>
![Fig. 4](../../assets/zh-CN/aphi_gates.png)

<p align="center">图 4. A–φ 圆柱校准指标。</p>

三档网格与各指标门槛分别展示。 圆柱三档含 1683、3672、9108 节点。误差以各自验收门槛归一化，水平线标出单位比值。

Wolfram 工具记录还包含前端工作完成后的进程清理：保存回执已确认，所属辅助进程最终退出码为 137，清理原因单独记录。分析这类运行时，需要同时读取完成回执、已保存产物和进程终止原因。单个退出码无法完整表达跨前端与内核的工作状态。

六类案例共同覆盖校准与 Notebook、原生建模求解、跨求解器比较、源码扩展、接口修复及数值失败解释。其共同产物是可定位的输入、源码、调用、结果和验收说明。接手者可以选择具体失败层重现问题，并以新的运行身份继续研究。

<a id="chapter-06"></a>
## 6 讨论与结论

自动化研究的可复核性取决于任务与证据之间的连续关联。可见任务、工具事件、源码差异和确定性测试足以组织本文案例的执行记录；科学判断仍需要明确模型适用条件、比较量和验收容差。代码能够运行、图形能够生成和论文能够排版，分别对应软件执行、结果表达和文档构建，它们与物理可靠性通过验收步骤连接。

研究过程同时涉及可编辑对象与稳定对象。参数、源码和后续研究任务需要便于修改；用于支撑结论的输入与结果则通过哈希固定。版本化数据目录保存原始文件身份，新运行写入独立目录。图件从保存数据重绘时记录来源与变换，双语稿件共享公式、图表和引用编号，使阅读层的变化可以追溯到同一科学内容。

这种流程特别适合逐层推进的模型研究。解析和二维案例提供低成本回归，少股模型检查共同端约束，有限长度及三维路线逐步引入新的自由度。原生 Notebook 允许读者检查三维几何及保存场的视角；真实中心线保留股线身份、弧长和局部位置，为后续模型扩展提供输入。结构性能比较还需匹配实际铜体积、回流、端区和数值不确定性。

<a id="fig-geometry_comparison"></a>
![Fig. 5](../../assets/zh-CN/geometry_comparison.png)

<p align="center">图 5. 股线中心线的三维结构比较。</p>

面板依次展示直束、单级、传统多级局部和跨层结构。 24 股结构使用 0.100 mm 铜径，传统多级面板展示 3 mm 局部。蓝色标记保持选定股线的物理身份。

本文交付了工作流、接入配置、运行适配、模型源码和可追溯案例。已有记录支持 Codex 通过 Wolfram 与 Ansys MCP 完成指定建模任务、扩展解析实现并依据错误证据修复接口；跨求解器和 A–φ 案例进一步说明验收状态如何限制结果解释。下一步方法评价可增加独立客户端、重复任务和人工基线，研究不同任务复杂度下的完成率、资源代价与修复稳定性。

Wolfram、AgentTools、PyAEDT-MCP、PyAEDT 及相关开源数值与文档工具共同支持了本研究的实现。AI 参与源码检查、模型与适配代码、调用编排、诊断和文稿整理；作者负责物理假设、验收依据与研究结论。软件环境和上游来源随仓库提供，读者可沿方法、实现、测试和结果的索引继续研究。
<a id="references"></a>
## 参考文献

[1] OpenAI. Codex. 2026. https://developers.openai.com/codex/

[2] Model Context Protocol contributors. Model Context Protocol. 2026. https://modelcontextprotocol.io/

[3] Wolfram Research. Wolfram Language and Notebook. 2026. https://www.wolfram.com/language/

[4] ANSYS, Inc.. Ansys Electronics Desktop / Maxwell. 2026. https://www.ansys.com/products/electronics/ansys-maxwell

[5] Silvano Cruciani, Tommaso Campi, Francesca Maradei, Mauro Feliziani. Numerical Modeling of Litz Wires Based on Discrete Transpositions of Strands and 2-D Finite Element Analysis. IEEE TPEL, 38, 5, 6710--6719, 2023. https://doi.org/10.1109/TPEL.2023.3240338

[6] Xinsheng Zhang, Fei Xiao, Ruitian Wang, Shunjun Chen, Xuexin Fan, Xin Li. AC Impedance Modeling of Composite Litz Wire With Nonideal Transposition Based on Improved Discrete Transposition Model. IEEE TPEL, 41, 7, 11003--11019, 2026. https://doi.org/10.1109/TPEL.2026.3661080

[7] Ruehli, A.E.. Equivalent Circuit Models for Three-Dimensional Multiconductor Systems. IEEE Transactions on Microwave Theory and Techniques, 22, 3, 216--221, 1974. https://doi.org/10.1109/tmtt.1974.1128204

[8] Raviart, P. A., Thomas, J. M.. A mixed finite element method for 2-nd order elliptic problems. Mathematical Aspects of Finite Element Methods, Springer, 606, 292--315, 1977. https://doi.org/10.1007/bfb0064470

[9] Wolfram Research. Wolfram AgentTools. 2026. https://github.com/WolframResearch/AgentTools

[10] ANSYS, Inc.. PyAEDT-MCP. 2026. https://github.com/ansys/pyaedt-mcp

[11] ANSYS, Inc.. PyAEDT. 2026. https://github.com/ansys/pyaedt

[12] ANSYS, Inc., contributors. ansys-common-mcp. 0.3.5, 2026. https://github.com/ansys/pyansys-common-mcp

[13] Giampaolo Rodola, contributors. psutil. 2026. https://github.com/giampaolo/psutil

[14] Python Software Foundation. Python. 2026. https://www.python.org/

[15] NIST. NIST Digital Library of Mathematical Functions, Modified Bessel Functions. 2026. https://dlmf.nist.gov/10.25

[16] Wolfram Research. Wolfram quasistatic magnetic field models. 2026. https://reference.wolfram.com/language/PDEModels/tutorial/Electromagnetics/QuasistaticMagneticFields.html
