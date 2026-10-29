---
name: litz-extend-model
description: 在 Litz 研究工作区执行 extend-model 任务，遵循共用科学约定、运行接口和证据记录。
---

说明新增能力和沿用的科学约定，阅读方程与实现。保存聚焦的代码修改，补充独立物理检查及回归，运行原案例与新案例，解释适用范围和未解决的不确定性。

通过 `pyproject.toml` 与 `configs/reference_parameters.json` 定位工作区。阅读 `AGENTS.zh-CN.md`、所选模型路线说明及 `automation/workflows/extend-model/README.zh-CN.md`。指定模型、案例和支持的参数；完整步骤及产物约定以该工作流说明为准。

检查实际可用的 MCP 工具。Wolfram 使用锁定版本的 AgentTools；Maxwell 使用锁定版本的 PyAEDT-MCP，并按环境使用项目的 Student 连接器。正式运行前保存源码和输入，再交给受资源约束的运行器。读取真实返回值和结果文件，包括以文本返回的 API 业务错误。

长任务使用唯一运行号和状态查询。保留失败，并关联修订后的新运行。分别报告执行状态和物理验收，同时说明模型假设与科学适用范围。

[English](SKILL.md)
