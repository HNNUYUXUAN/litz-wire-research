# Wolfram MCP 接入

按[固定来源清单](../upstreams.lock.json)准备 Wolfram 和 AgentTools 2.2.0。`LITZ_WOLFRAM_KERNEL` 指向具有可用许可证的内核可执行文件。服务器入口为 `PacletSymbol["Wolfram/AgentTools","Wolfram`AgentTools`StartMCPServer"]["WolframLanguage"]`。

在内核中用 `PacletFind["Wolfram/AgentTools"]` 查看已安装版本。需要安装时，使用 `PacletInstall["Wolfram/AgentTools" -> "2.2.0", KeepExistingVersion -> True]` 并检查返回版本。固定提交与 MIT 许可原文随来源记录保存；明确版本安装形式见[官方 PacletInstall 文档](https://reference.wolfram.com/language/ref/PacletInstall.html)。

通过项目配置生成器配置本地 STDIO 连接。执行：

```powershell
litz-research automation probe wolfram --run-id wolfram_mcp_probe_01
```

检查初始化、`tools/list` 和 `tools/call` 事件，以及工具返回值和实际产物。此基线的 `WolframLanguage` 服务器提供七项工具，未命名服务器的工具集合不同；使用生成配置及随附的五工具校准序列。长计算通过受控任务提交和状态查询管理。

内核计算与 Notebook 前端分别验收。既有 20 份研究 Notebook 的验证包括实际打开、保存、回读与渲染；协议初始化记录说明连接能力，数值检查说明模型验收范围。

卸载本接入配置时，移除相应的客户端条目与项目专用环境。Wolfram 应用及其他 MCP 配置按各自的安装方式管理。

[English](README.md)
