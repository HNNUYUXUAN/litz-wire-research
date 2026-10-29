# 二维扩散有限元

缪雨轩 · 淮南师范学院

## 模型与假设

∇⊥²Ez−jωμσEz=0; Jz=σEz

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

修改 mesh_h；收敛判断至少运行三档网格。

## 保存输入并执行

在项目根目录运行。先复制并修改参数文件，使用新的运行号。参数字段由 CLI 校验；正式执行前保存源码与输入。

[参数文件](examples/tutorial.json)

```bash
litz-research models fem2
litz-research run fem2 --case tutorial --parameters models/fem2/examples/tutorial.json --run-id fem2_example_01 --dry-run
litz-research run fem2 --case tutorial --parameters models/fem2/examples/tutorial.json --run-id fem2_example_01
```

已安装项目环境可使用 `litz-research`；也可将命令前缀替换为 `.conda/project/python.exe -m litz_research.cli`。

## 异步任务与恢复

```bash
litz-research jobs submit fem2 --case tutorial --parameters models/fem2/examples/tutorial.json --run-id fem2_example_01
litz-research jobs status fem2_example_01
```

同步与异步示例是同一任务的两种执行方式；实际选择其中一种，并分配唯一运行号。取消使用 `litz-research jobs cancel fem2_example_01`。恢复先核实输入和源码，再使用 `jobs resume --help` 指定关联的新运行号。

## 结果与验收

检查 `outputs/fem2_example_01/results.json` 中的 `execution_status`、`physical_acceptance_status`、`checks`、`scope` 和参数。复数量保留实部与虚部；支持原生结果的路线还保存 `results.wxf`。单档教程不证明网格收敛。

任务限制为八个逻辑处理器、24 GiB 内存和至少 8 GiB 系统余量。只管理任务创建且创建身份匹配的进程。

## 推导与结果解释

在圆截面求解 ∇⊥²Ez−jωμσEz=0；边界常量场通过总复电流归一化。圆周多边形、插值阶次和网格尺寸共同决定数值误差。
弱形式在区域内积分 ∇v·∇Ez+jωμσvEz，并施加给定边界值。对所得电流及焦耳密度独立积分，再将 Rac 与 Bessel 解比较。
教程只用单档网格。精度判断须至少三档递减 h/a，并检查边界及圆周离散；积分守恒本身不构成场误差上界。

## 接续研究

每次改变一个受支持的参数，保存新的运行身份并检查守恒、离散、边界与长度敏感性。保持回流、实际弧长、铜体积和传统多级 Litz 基线可比。

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## 历史证据与来源

data/evidence/v1.0.0-rc.1/; litz-research data fetch fem2

[FEMDOC](../../references/README.md), [P04](../../references/README.md)
