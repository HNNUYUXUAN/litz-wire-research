# Wolfram 环境与执行

Miao Yuxuan · Huainan Normal University

## 模型与假设

Independent kernel execution and native frontend rendering

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

检查本机内核，再按 MCP 工作流验收真实工具调用和 Notebook 操作。

## 运行教程

```powershell
litz-research run wolfram --case tutorial --parameters adapters/wolfram/examples/tutorial.json --run-id wolfram_example_01
```

[交互研究 Notebook](notebooks/wolfram_zh-CN.nb)

## 结果与验收

读取 results.json、验收项、复数实虚部和 results.wxf。执行状态与物理验收分别记录；单档教程网格用于演示，收敛另行验证。

## 接续研究

从教程配置开始，逐次改变一个已支持的参数，保存新的运行身份，检查守恒与离散敏感性，再与冻结证据比较。完整研究任务通过阶段运行器调用。

## 来源

[WOLFRAM](../../references/README.md), [AGENTTOOLS](../../references/README.md)

## 推导与结果解释

先检查实际本机内核与算术。原生 Notebook 在独立进程调用与 CLI 相同的保存任务接口；MCP 案例另行检查工具发现、数值执行、TestReport 及 Notebook 写入回读。
连接成功、数值测试成功和场解验收分别记录；使用版本相关参数前核对实际 AgentTools 版本与可见工具 schema。

## 历史证据

data/evidence/v1.0.0-rc.1/; litz-research data fetch analytic
