# 向量 RT0 体积 PEEC

缪雨轩 · 淮南师范学院

## 模型与假设

(R+jωL)i+e=Cᵀv; Ci=b

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

选择外场或输运激励。外场算例为 1 mT RMS Bz、零净输运。

## 保存输入并执行

在项目根目录运行。先复制并修改参数文件，使用新的运行号。参数字段由 CLI 校验；正式执行前保存源码与输入。

[参数文件](examples/tutorial.json)

```bash
litz-research models rt0
litz-research run rt0 --case tutorial --parameters models/rt0/examples/tutorial.json --run-id rt0_example_01 --dry-run
litz-research run rt0 --case tutorial --parameters models/rt0/examples/tutorial.json --run-id rt0_example_01
```

已安装项目环境可使用 `litz-research`；也可将命令前缀替换为 `.conda/project/python.exe -m litz_research.cli`。

## 异步任务与恢复

```bash
litz-research jobs submit rt0 --case tutorial --parameters models/rt0/examples/tutorial.json --run-id rt0_example_01
litz-research jobs status rt0_example_01
```

同步与异步示例是同一任务的两种执行方式；实际选择其中一种，并分配唯一运行号。取消使用 `litz-research jobs cancel rt0_example_01`。恢复先核实输入和源码，再使用 `jobs resume --help` 指定关联的新运行号。

## 结果与验收

检查 `outputs/rt0_example_01/results.json` 中的 `execution_status`、`physical_acceptance_status`、`checks`、`scope` 和参数。复数量保留实部与虚部；支持原生结果的路线还保存 `results.wxf`。单档教程不证明网格收敛。

任务限制为八个逻辑处理器、24 GiB 内存和至少 8 GiB 系统余量。只管理任务创建且创建身份匹配的进程。

## 推导与结果解释

最低阶 Raviart–Thomas 面通量自由度表示具有单元散度的向量电流；相邻单元共享带方向的面通量，关联矩阵 C 实现离散电流连续性。
混合 PEEC 系统为 (R+jωL)i+e=Cᵀv、Ci=b。外场教程采用 Bz=1 mT RMS、零净输运，分别由重构电流与电阻二次型计算损耗。
检查真实线性残差、连续性、积分及空间敏感性。外场损耗是诊断量；用另设输运电流的平方去除它，不能据此定义内禀电阻。

## 接续研究

每次改变一个受支持的参数，保存新的运行身份并检查守恒、离散、边界与长度敏感性。保持回流、实际弧长、铜体积和传统多级 Litz 基线可比。

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## 历史证据与来源

data/evidence/v1.0.0-rc.1/; litz-research data fetch rt0

[P03](../../references/README.md), [RUEHLI1974](../../references/README.md), [RT1977](../../references/README.md), [GMRES1986](../../references/README.md)
