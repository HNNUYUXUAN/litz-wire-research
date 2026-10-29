# 单圆线解析校准

缪雨轩 · 淮南师范学院

## 模型与假设

∇²Ez−jωμσEz=0; Zint=κ I0(κa)/(2πaσ I1(κa))

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

修改频率与总电流，核对独立电流积分与焦耳积分。

## 保存输入并执行

在项目根目录运行。先复制并修改参数文件，使用新的运行号。参数字段由 CLI 校验；正式执行前保存源码与输入。

[参数文件](examples/tutorial.json)

```bash
litz-research models wolfram-analytic
litz-research run wolfram-analytic --case tutorial --parameters models/analytic/examples/tutorial.json --run-id analytic_example_01 --dry-run
litz-research run wolfram-analytic --case tutorial --parameters models/analytic/examples/tutorial.json --run-id analytic_example_01
```

已安装项目环境可使用 `litz-research`；也可将命令前缀替换为 `.conda/project/python.exe -m litz_research.cli`。

## 异步任务与恢复

```bash
litz-research jobs submit wolfram-analytic --case tutorial --parameters models/analytic/examples/tutorial.json --run-id analytic_example_01
litz-research jobs status analytic_example_01
```

同步与异步示例是同一任务的两种执行方式；实际选择其中一种，并分配唯一运行号。取消使用 `litz-research jobs cancel analytic_example_01`。恢复先核实输入和源码，再使用 `jobs resume --help` 指定关联的新运行号。

## 结果与验收

检查 `outputs/analytic_example_01/results.json` 中的 `execution_status`、`physical_acceptance_status`、`checks`、`scope` 和参数。复数量保留实部与虚部；支持原生结果的路线还保存 `results.wxf`。单档教程不证明网格收敛。

任务限制为八个逻辑处理器、24 GiB 内存和至少 8 GiB 系统余量。只管理任务创建且创建身份匹配的进程。

## 推导与结果解释

均匀长圆柱导体的轴对称内场仅保留 Ez(r)，并有 Jz=σEz。由安培与法拉第定律及 exp(+jωt) 得 (1/r)d(r dEz/dr)/dr=jωμσEz；轴心正则解为 C I0(κr)，κ²=jωμσ。
用 2π∫Jz r dr=It 确定 C，得到内阻抗 Zint=κ I0(κa)/(2πaσ I1(κa))。独立积分 ∫|J|²/σ dA，与 |It|² Re Zint 比较；采用 RMS 相量，无额外 1/2 系数。
κa→0 时 I0→1、I1→κa/2，因此 Rdc=1/(σπa²)。模型不含端效应与回流外电感。Q1 的 a=1 mm 保留为解析校准。

## 接续研究

每次改变一个受支持的参数，保存新的运行身份并检查守恒、离散、边界与长度敏感性。保持回流、实际弧长、铜体积和传统多级 Litz 基线可比。

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## 历史证据与来源

data/evidence/v1.0.0-rc.1/; litz-research data fetch analytic

[BESSEL](../../references/README.md)
