# 智能体驱动建模与仿真

从研究问题与物理约束开始：智能体读取模型和证据，通过 Wolfram 或 Ansys MCP 探索并建立模型，保存源码，调用受资源限制的运行器，检查独立验收，然后解释结果或继续诊断。

入口为 [Codex 配置](harnesses/codex/README.zh-CN.md)、[通用 MCP 配置](harnesses/generic/README.zh-CN.md)、[固定上游](mcp/upstreams.lock.json)及[完整案例](examples/README.zh-CN.md)。工作流覆盖复现、模型扩展、跨求解器比较、失败诊断和科学成稿。

连接、工具调用、求解执行和物理验收分别记录。保存的源码与输入用于确定性复现；智能体的开发过程允许不同实现，但需要满足相同科学验收。
