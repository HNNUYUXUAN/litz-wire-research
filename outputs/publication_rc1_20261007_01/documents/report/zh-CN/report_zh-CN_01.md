# Litz 线分层建模与数值验证：完整研究报告 · 01 引言与研究问题

缪雨轩 · 淮南师范学院

[合并稿](report_zh-CN.md#chapter-01)

<a id="chapter-01"></a>
## 01 引言与研究问题

<a id="01.introduction.heading"></a>
### 引言

将总铜截面分成许多细股，并不能单独保证高频损耗下降。单股直径决定局部趋肤尺度，邻近导体与回流决定外部磁场，沿程位置和共同端接则决定各股复电流。仅比较几何外观、名义铜面积或平均电流，会把不同物理机制混合在同一个指标中。可靠的结构比较应首先确定哪些场量和约束被模型保留，再检查相应的数值不确定性。

现有方法提供了不同尺度的处理途径。离散换位与二维 FEM 相结合的 DTM [1] 将位置置换与截面场解联系起来；非理想复合换位 iDTM [2] 进一步关注层级及子束换位。iSEC [3] 在其指定绕组与分层假设下构造降阶电路；FEM–PEEC 耦合 [4] 和准二维多导体方法 [5] 则采用不同的宏观场、端场与电流约束。连续体模型 [6]、复磁导率均匀化 [7] 降低了大规模绕组的计算成本，但其平均场不能直接替代逐股复电流或真实端区。

本文的重点不是提出已经得到验证的最优换位结构，而是建立结构研究所需的可比较量与验证链。第一项工作是区分解析、二维、纵向和完整体素模型的验证关系；第二项是从共端增广系统推导均流条件，明确其模型范围；第三项是对有限长度纵向 PEEC 进行单因素敏感性检查，并把 CPU/GPU 算法对照与物理验证分别解释。传统多级 Litz 保持强基线；跨层几何作为待验证候选，不预设优越性。

<a id="01.scope.heading"></a>
### 研究问题与贡献

本研究围绕三个问题组织验证：局部趋肤基准能否由独立离散方法复现；共同端电压下的复电流分配由哪些代数条件决定；有限长度纵向核的电阻结果对长度和积分设置有多大敏感性。所给出的贡献是统一物理量、可审查的验证关系和模型内的定量证据，供真实换位结构研究选择合适的下一层模型。

<a id="fig-model_hierarchy"></a>
![Fig. 1](../../../panels/zh-CN/model_hierarchy.png)

<p align="center">图 1. 分层模型与可比较观测量。</p>

输运模型按物理对象与观测量分组：圆线内场用于解析与二维校准，多股二维场路求解共同端口下的复电流，纵向 PEEC 检验有限长度效应。连线标明内部场校准或等面积电阻参照。RT0 外场损耗与三维 A–φ 场诊断各自构成独立研究范围。
<a id="references"></a>
## 参考文献

[1] Silvano Cruciani, Tommaso Campi, Francesca Maradei, Mauro Feliziani. Numerical Modeling of Litz Wires Based on Discrete Transpositions of Strands and 2-D Finite Element Analysis. IEEE TPEL 38(5):6710–6719, 2023. https://doi.org/10.1109/TPEL.2023.3240338

[2] Xinsheng Zhang, Fei Xiao, Ruitian Wang, Shunjun Chen, Xuexin Fan, Xin Li. AC Impedance Modeling of Composite Litz Wire With Nonideal Transposition Based on Improved Discrete Transposition Model. IEEE TPEL 41(7):11003–11019, 2026. https://doi.org/10.1109/TPEL.2026.3661080

[3] Yueyin Wang, Wu Chen, Zhan Shen. Modeling of Litz Wire Winding AC Resistance Based on Improved Segmented Equivalent Circuit. IEEE TPEL 39(1):1135–1149, 2024. https://doi.org/10.1109/TPEL.2023.3321327

[4] Andreas Roßkopf, Eberhard Bär, Christopher Joffe, Clemens Bonse. Calculation of Power Losses in Litz Wire Systems by Coupling FEM and PEEC Method. IEEE TPEL 31(9):6442–6449, 2016. https://doi.org/10.1109/TPEL.2015.2499793

[5] Tamás Bakondi, Sándor Bilicz, Szabolcs Gyimóthy. Finite element modeling of eddy currents in a multiconductor system with quasi-2D symmetry. COMPEL 44(5):730–742, 2025. https://doi.org/10.1108/COMPEL-01-2025-0031

[6] David C. Meeker. An Improved Continuum Skin and Proximity Effect Model for Hexagonally Packed Wires. JCAM 236(18):4635–4644, 2012. https://doi.org/10.1016/j.cam.2012.04.009

[7] Korawich Niyomsatian, Johan Gyselinck, Ruth V. Sabariego. Closed-form complex permeability expression for proximity-effect homogenisation of litz-wire windings. IET SMT 14(3):287–291, 2020. https://doi.org/10.1049/iet-smt.2019.0377
