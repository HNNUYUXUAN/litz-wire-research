# Ansys MCP 与 Maxwell 工作流

Miao Yuxuan · Huainan Normal University

## 模型与假设

Common terminal voltage and total RMS current

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

执行资源预检；Maxwell 可用时运行原生七股 MCP 案例。

## 运行教程

```powershell
litz-research run ansys --case preflight --parameters adapters/ansys/examples/tutorial.json --run-id ansys_example_01
```

[交互研究 Notebook](notebooks/ansys_zh-CN.nb)

## 结果与验收

读取 results.json、验收项、复数实虚部和 results.wxf。执行状态与物理验收分别记录；单档教程网格用于演示，收敛另行验证。

## 接续研究

从教程配置开始，逐次改变一个已支持的参数，保存新的运行身份，检查守恒与离散敏感性，再与冻结证据比较。完整研究任务通过阶段运行器调用。

## 来源

[PYAEDTMCP](../../references/README.md), [PYAEDT](../../references/README.md)

## 推导与结果解释

本 Notebook 执行资源预检。完整 MCP 案例启动所属 Student gRPC Desktop，连接官方服务，构建七个电压绕组和受控回流，求解两个线性基工况与最终受约束工况。
AEDT 电压输入为峰值；适配层把 RMS 输入乘 √2，并重构 RMS 复电流及功率。CPython/PyAEDT 执行环境与 AEDT 内置 RunScript 不同。
检查实际单位、轴向模型深度、频率、工程内容、网格、复电流及输入损耗平衡；单遍 Student 网格仅支持明示的比较范围。

## 历史证据

data/evidence/v1.0.0-rc.1/; litz-research data fetch ansys

## 统一异步原生求解入口

```powershell
litz-research jobs submit ansys --case maxwell-seven --run-id maxwell_job_01
litz-research jobs status maxwell_job_01
litz-research jobs cancel maxwell_job_01
litz-research jobs resume maxwell_job_01 --new-run-id maxwell_job_02
```

运行器启动所属 Student 会话，保存 MCP 发现、调用和原生结果；取消时关闭所属进程。接续核对保存输入及源码后使用新运行号。Notebook 仍默认执行轻量资源预检。
