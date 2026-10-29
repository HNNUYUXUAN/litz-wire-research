---
name: litz-diagnose
description: 在 Litz 研究工作区执行 diagnose 任务，遵循共用科学约定、运行接口和证据记录。
---

保留原失败和实际工具响应，区分传输、API、求解器、资源与物理失败。测试相关的最小修正，记录依据和代码差异，以新身份重跑，按原容差比较验收结果。

通过 `pyproject.toml` 与 `configs/reference_parameters.json` 定位工作区。阅读 `AGENTS.zh-CN.md`、所选模型路线说明及 `automation/workflows/diagnose/README.zh-CN.md`。指定模型、案例和支持的参数；完整步骤及产物约定以该工作流说明为准。

检查实际可用的 MCP 工具。Wolfram 使用锁定版本的 AgentTools；Maxwell 使用锁定版本的 PyAEDT-MCP，并按环境使用项目的 Student 连接器。正式运行前保存源码和输入，再交给受资源约束的运行器。读取真实返回值和结果文件，包括以文本返回的 API 业务错误。

长任务使用唯一运行号和状态查询。保留失败，并关联修订后的新运行。分别报告执行状态和物理验收，同时说明模型假设与科学适用范围。

[English](SKILL.md)
