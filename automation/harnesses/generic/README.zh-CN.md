# 其他智能体客户端

接入协议由 MCP STDIO／HTTP 配置、研究工作流、保存参数和本地 CLI 组成。客户端需要支持 MCP 初始化、工具发现和工具调用，并能够访问工作区。自动加载约定的方式不同时，明确读取 `AGENTS.md` 和所需 `SKILL.md`。

使用 `litz-research automation configure` 生成 `mcp.json`，将其中的服务器命令、参数、工作目录或 HTTP URL 映射到客户端配置。核对路径与工具清单，并通过 `automation/mcp/client.py` 独立检查协议。

研究任务由保存输入、源码哈希和结果定义，能够在支持这些接口的客户端中接续。各客户端的端到端验证状态分别记录；已有 Codex 案例见[实际运行索引](../../examples/verification.json)。

[English](README.md)
