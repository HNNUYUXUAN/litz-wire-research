---
name: litz-compare-solvers
description: 在 Litz 研究工作区执行 compare-solvers 任务，遵循共用科学约定、运行接口和证据记录。
---

对齐几何、铜面积、材料、频率、RMS/峰值约定、轴向长度、端口约束、回流与边界。分别求解，比较复电流、功率与 Rac，并报告离散和几何差异。

通过 `pyproject.toml` 与 `configs/reference_parameters.json` 定位工作区。阅读 `AGENTS.zh-CN.md`、所选模型路线说明及 `automation/workflows/compare-solvers/README.zh-CN.md`。指定模型、案例和支持的参数；完整步骤及产物约定以该工作流说明为准。

检查实际可用的 MCP 工具。Wolfram 使用锁定版本的 AgentTools；Maxwell 使用锁定版本的 PyAEDT-MCP，并按环境使用项目的 Student 连接器。正式运行前保存源码和输入，再交给受资源约束的运行器。读取真实返回值和结果文件，包括以文本返回的 API 业务错误。

长任务使用唯一运行号和状态查询。保留失败，并关联修订后的新运行。分别报告执行状态和物理验收，同时说明模型假设与科学适用范围。

[English](SKILL.md)
