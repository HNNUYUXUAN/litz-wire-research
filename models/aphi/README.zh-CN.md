# 保存 A–φ 场诊断

缪雨轩 · 淮南师范学院

## 模型与假设

J=−σ(jωA+∇φ); ∇·J=0

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

读取实际保存场，复算 J、电势与规范残差，保留原场参数。

## 保存输入并执行

在项目根目录运行。先复制并修改参数文件，使用新的运行号。参数字段由 CLI 校验；正式执行前保存源码与输入。

[参数文件](examples/tutorial.json)

```bash
litz-research models aphi
litz-research run aphi --case diagnostic --parameters models/aphi/examples/tutorial.json --run-id aphi_example_01 --dry-run
litz-research run aphi --case diagnostic --parameters models/aphi/examples/tutorial.json --run-id aphi_example_01
```

已安装项目环境可使用 `litz-research`；也可将命令前缀替换为 `.conda/project/python.exe -m litz_research.cli`。

## 异步任务与恢复

```bash
litz-research jobs submit aphi --case diagnostic --parameters models/aphi/examples/tutorial.json --run-id aphi_example_01
litz-research jobs status aphi_example_01
```

同步与异步示例是同一任务的两种执行方式；实际选择其中一种，并分配唯一运行号。取消使用 `litz-research jobs cancel aphi_example_01`。恢复先核实输入和源码，再使用 `jobs resume --help` 指定关联的新运行号。

## 结果与验收

检查 `outputs/aphi_example_01/results.json` 中的 `execution_status`、`physical_acceptance_status`、`checks`、`scope` 和参数。复数量保留实部与虚部；支持原生结果的路线还保存 `results.wxf`。单档教程不证明网格收敛。

任务限制为八个逻辑处理器、24 GiB 内存和至少 8 GiB 系统余量。只管理任务创建且创建身份匹配的进程。

## 推导与结果解释

采用 exp(+jωt)，由原保存的 A、φ 场重构 J=−σ(jωA+∇φ)，在原输入下比较电流守恒和归一化电势、规范残差。
本入口仅改变诊断采样密度，在保存场上复算导数并与原诊断量比较可复现性，不产生新的物理场解。
原电势与规范验收仍为失败。保留网格、激励、规范及边界假设；明确一致形式并通过守恒、规范和网格研究后再推进。

## 接续研究

每次改变一个受支持的参数，保存新的运行身份并检查守恒、离散、边界与长度敏感性。保持回流、实际弧长、铜体积和传统多级 Litz 基线可比。

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## 历史证据与来源

data/evidence/v1.0.0-rc.1/; litz-research data fetch aphi

[FEMDOC](../../references/README.md), [GMRES1986](../../references/README.md)
