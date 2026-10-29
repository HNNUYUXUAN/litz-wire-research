# Ansys MCP 与 Maxwell 工作流

缪雨轩 · 淮南师范学院

## 模型与假设

Common terminal voltage and total RMS current

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

执行资源预检；Maxwell 可用时运行原生七股 MCP 案例。

## 保存输入并执行

在项目根目录运行。先复制并修改参数文件，使用新的运行号。参数字段由 CLI 校验；正式执行前保存源码与输入。

[参数文件](examples/tutorial.json)

```bash
litz-research models ansys
litz-research run ansys --case preflight --parameters adapters/ansys/examples/tutorial.json --run-id ansys_example_01 --dry-run
litz-research run ansys --case preflight --parameters adapters/ansys/examples/tutorial.json --run-id ansys_example_01
```

已安装项目环境可使用 `litz-research`；也可将命令前缀替换为 `.conda/project/python.exe -m litz_research.cli`。

## 异步任务与恢复

```bash
litz-research jobs submit ansys --case preflight --parameters adapters/ansys/examples/tutorial.json --run-id ansys_example_01
litz-research jobs status ansys_example_01
```

同步与异步示例是同一任务的两种执行方式；实际选择其中一种，并分配唯一运行号。取消使用 `litz-research jobs cancel ansys_example_01`。恢复先核实输入和源码，再使用 `jobs resume --help` 指定关联的新运行号。

## 结果与验收

检查 `outputs/ansys_example_01/results.json` 中的 `execution_status`、`physical_acceptance_status`、`checks`、`scope` 和参数。复数量保留实部与虚部；支持原生结果的路线还保存 `results.wxf`。单档教程不证明网格收敛。

任务限制为八个逻辑处理器、24 GiB 内存和至少 8 GiB 系统余量。只管理任务创建且创建身份匹配的进程。

## 推导与结果解释

本 Notebook 执行资源预检。完整 MCP 案例启动所属 Student gRPC Desktop，连接官方服务，构建七个电压绕组和受控回流，求解两个线性基工况与最终受约束工况。
AEDT 电压输入为峰值；适配层把 RMS 输入乘 √2，并重构 RMS 复电流及功率。CPython/PyAEDT 执行环境与 AEDT 内置 RunScript 不同。
检查实际单位、轴向模型深度、频率、工程内容、网格、复电流及输入损耗平衡；单遍 Student 网格仅支持明示的比较范围。

## 接续研究

每次改变一个受支持的参数，保存新的运行身份并检查守恒、离散、边界与长度敏感性。保持回流、实际弧长、铜体积和传统多级 Litz 基线可比。

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## 历史证据与来源

data/evidence/v1.0.0-rc.1/; litz-research data fetch ansys

[PYAEDTMCP](../../references/README.md), [PYAEDT](../../references/README.md)
