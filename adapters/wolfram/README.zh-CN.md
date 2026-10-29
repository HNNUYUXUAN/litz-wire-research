# Wolfram 环境与执行

缪雨轩 · 淮南师范学院

## 模型与假设

Independent kernel execution and native frontend rendering

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

检查本机内核，再按 MCP 工作流验收真实工具调用和 Notebook 操作。

## 保存输入并执行

在项目根目录运行。先复制并修改参数文件，使用新的运行号。参数字段由 CLI 校验；正式执行前保存源码与输入。

[参数文件](examples/tutorial.json)

```bash
litz-research models wolfram
litz-research run wolfram --case tutorial --parameters adapters/wolfram/examples/tutorial.json --run-id wolfram_example_01 --dry-run
litz-research run wolfram --case tutorial --parameters adapters/wolfram/examples/tutorial.json --run-id wolfram_example_01
```

已安装项目环境可使用 `litz-research`；也可将命令前缀替换为 `.conda/project/python.exe -m litz_research.cli`。

## 异步任务与恢复

```bash
litz-research jobs submit wolfram --case tutorial --parameters adapters/wolfram/examples/tutorial.json --run-id wolfram_example_01
litz-research jobs status wolfram_example_01
```

同步与异步示例是同一任务的两种执行方式；实际选择其中一种，并分配唯一运行号。取消使用 `litz-research jobs cancel wolfram_example_01`。恢复先核实输入和源码，再使用 `jobs resume --help` 指定关联的新运行号。

## 结果与验收

检查 `outputs/wolfram_example_01/results.json` 中的 `execution_status`、`physical_acceptance_status`、`checks`、`scope` 和参数。复数量保留实部与虚部；支持原生结果的路线还保存 `results.wxf`。单档教程不证明网格收敛。

任务限制为八个逻辑处理器、24 GiB 内存和至少 8 GiB 系统余量。只管理任务创建且创建身份匹配的进程。

## 推导与结果解释

先检查实际本机内核与算术。原生 Notebook 在独立进程调用与 CLI 相同的保存任务接口；MCP 案例另行检查工具发现、数值执行、TestReport 及 Notebook 写入回读。
连接成功、数值测试成功和场解验收分别记录；使用版本相关参数前核对实际 AgentTools 版本与可见工具 schema。

## 接续研究

每次改变一个受支持的参数，保存新的运行身份并检查守恒、离散、边界与长度敏感性。保持回流、实际弧长、铜体积和传统多级 Litz 基线可比。

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## 历史证据与来源

data/evidence/v1.0.0-rc.1/; litz-research data fetch analytic

[WOLFRAM](../../references/README.md), [AGENTTOOLS](../../references/README.md)
