# Litz 研究工作约定

先读 README、所选模型路线说明、`docs/建模约定与解析基准.md` 和 `tests/ACCEPTANCE.md`。复现、扩展模型、跨求解器比较、诊断和成稿任务分别使用 `automation/workflows/` 中的入口。

计算采用 SI、exp(+jωt)、RMS 相量，铜电导率 58 MS/m、μr=1、20 ℃。主输运工况为 200 kHz、20 A RMS。Q1 的 2 mm 圆线用于校准，Jdc≈6.366 A/mm²；Q2 的名义铜截面至少 5 mm²。

共同端电压和总复电流联合确定股线电流。保存股线身份、实际弧长、回流和边界假设、复电流、绝对 Rac、Rac/Rdc 及功率。传统多级 Litz 是结构比较的强基线，性能排序需要改善量超过相关数值不确定性。

使用共用 CLI／Notebook 任务接口。正式执行前保存源码和输入，选择明确案例及唯一运行号。记录源码哈希、环境版本、参数、模型假设、执行状态、物理验收和失败原因。

任务预算为八个逻辑处理器、24 GiB 内存及 8 GiB 系统空闲内存；Student 另受实际许可证限制。根据创建身份管理本任务进程，保留历史证据和用户已有修改。

Wolfram 和 PyAEDT MCP 使用 `automation/mcp/upstreams.lock.json` 中的固定来源。检查实际工具和返回值。长任务通过状态接口接续；恢复前核对输入、源码和检查点，重启则建立关联的新运行。

文献 key 来自 `references/library.bib`，实际用途和许可记录于 `references/sources.json`。保留第三方版权，公开示例采用可迁移路径和脱敏工具记录。

[English](AGENTS.md)
