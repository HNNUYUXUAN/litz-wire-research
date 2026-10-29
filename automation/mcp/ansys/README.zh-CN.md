# Ansys MCP 接入

在 Python 3.12 或更新版本的独立环境中安装 PyAEDT 1.8.0 与 `upstreams.lock.json` 固定的 PyAEDT-MCP 提交。Student 接入使用 `adapters/ansys/StartMCP.py` 和 `LITZ_AEDT_EDITION=student`。先运行 `OwnedAEDTSession.py`，读取所属会话的端口记录，再以匹配的版本调用 `connect_to_aedt`。

外部 CPython／PyAEDT 代码通过 `run_python_code` 执行。AEDT 的 `RunScript` 使用另一套运行环境，调用前按工具和模块的实际接口选择执行位置。

```powershell
python automation/mcp/setup.py ansys --destination build/ansys-env
python automation/mcp/setup.py ansys --destination build/ansys-env --apply
litz-research automation configure --output build/client-config --ansys-python build/ansys-env/Scripts/python.exe
litz-research automation probe ansys --run-id ansys_mcp_probe_01
```

第一条命令显示安装计划，第二条在新目录执行安装。已核验的完整依赖记录为 `ansys-environment.lock`。检查初始化、工具发现、实际调用、AEDT 工程和数值结果；工具返回的普通文本也可能包含业务错误。

默认使用 STDIO。本机 HTTP 可使用 `StartMCP.py --transport http --http-host 127.0.0.1 --http-port 8080` 启动，再生成相应配置。验证矩阵中 HTTP 属于已提供配置的入口，其端到端状态按实际运行记录列出。

长计算使用任务提交、查询和取消接口。卸载时移除所生成的客户端条目与专用 Python 环境；AEDT 及许可证按各自条款管理。

[原生案例复现](../../examples/README.zh-CN.md) · [官方安装说明](https://aedt-mcp.docs.pyansys.com/version/stable/getting_started/installation.html) · [固定来源](../upstreams.lock.json) · [English](README.md)
