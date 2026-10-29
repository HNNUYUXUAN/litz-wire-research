# 复跑前准备与验收

[English](reproduction-readiness.md) · [自动化入口](../automation/README.zh-CN.md)

使用 `.conda/project` 执行 CLI 任务，`.conda/ansys` 运行已锁定的 Ansys MCP；其路径保存在忽略版本控制的 `litz.config.json` 中。环境、连接、求解和物理验收分别记录。

## 配置与依赖

按已导出的锁文件重建项目和 Ansys 环境：

```bash
python tools/CondaEnvironments.py rebuild project --prefix .conda/project
python tools/CondaEnvironments.py rebuild ansys --prefix .conda/ansys
```

`pip check` 只检查声明的依赖关系，不能代替实际导入测试或锁定版本核对。`automation readiness` 同时检查这些项目。已有环境使用[环境核验入口](../automation/environments/README.md)检查；该说明也提供 Miniconda 可执行文件参数。Ansys 的身份依据[固定上游说明](../automation/mcp/ansys/README.zh-CN.md)。

本机 `litz.config.json` 的 `tools` 配置 `python`、`ansys_python`、`ansysedt`、`wolfram_kernel`、`wolframscript` 和 `powershell`。`mcp_servers` 保存与桌面客户端一致的 `command`、`args`、`cwd`、`env`。从实际安装生成模板：

```bash
.conda/project/python.exe -m litz_research automation configure --output build/client-config --ansys-python .conda/ansys/python.exe
```

将生成的 `mcp.json` 中 `mcpServers` 合并到本机配置的 `mcp_servers`，并把相应 TOML 条目合并到 Codex 配置。保留其他服务和设置，不把本机路径提交到仓库。

Ansys 的显式环境包括 `PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`、Windows `APPDATA`、已验证的 `ANSYSEMSV_ROOTxxx` 或 `ANSYSEM_ROOTxxx`，以及版本对应的 edition 设置。Wolfram 保留授权用户的目录配置。两者都设置 `LITZ_PROJECT`；兼容适配入口使用 `LITZ_PYTHON` 指向项目 Python。生成器只复制相关变量，不导出整个进程环境。

## 每次新研究前

下面是 Git Bash 命令。每次生成新编号；已有目录不覆盖。

```bash
stamp=$(date +%Y%m%d_%H%M%S)
py=.conda/project/python.exe
"$py" -m litz_research automation readiness --run-id "ready_${stamp}" --client-config "$USERPROFILE/.codex/config.toml"
```

通过条件是退出码 0、`readiness_status=passed_preflight` 和空的 `failed_checks`。报告在 `outputs/<run-id>/results.json`，覆盖项目/Ansys 依赖导入与版本、上游 commit、显式启动配置、桌面配置一致性、源码测试、路线输入和内存余量。首次恢复数据或迁移存储后加 `--verify-data` 做完整内容哈希校验。

安装、配置、系统用户或工作区变化后，再用全新会话验证两条 MCP 链路：

```bash
"$py" -m litz_research automation probe ansys --run-id "ansys_probe_${stamp}" --clean-environment
"$py" -m litz_research automation probe wolfram --run-id "wolfram_probe_${stamp}" --clean-environment
```

`--clean-environment` 去掉从终端继承的应用变量，只保留基础系统环境，再由保存的服务配置提供运行所需变量。这能发现终端可用、桌面不可用的问题。探针会拒绝“未找到 AEDT”和 Wolfram `TestReport` 失败/空测试的假成功。查看实际工具事件及 stderr；受控进程在完成收据写入后被清理时，操作系统退出码可能非零，应同时查看 `completion_receipt_observed` 和 `cleanup_reason`。

已运行的 MCP 进程不会自动获得修改后的环境变量。完成全部配置后统一重载客户端；不要把旧会话的检测结果当作新配置验收。

## 从小案例进入正式复跑

```bash
"$py" -m litz_research run analytic --case tutorial --run-id "analytic_${stamp}"
"$py" -m litz_research jobs submit peec --case tutorial --run-id "peec_${stamp}"
"$py" -m litz_research jobs status "peec_${stamp}"
"$py" -m litz_research jobs submit ansys --case maxwell-seven --run-id "maxwell_${stamp}"
"$py" -m litz_research jobs status "maxwell_${stamp}"
```

长任务用 `jobs submit/status/cancel/resume`。`running` 且 `worker_status=finishing` 表示已保存求解结果，但会话清理尚未结束。等待最终状态后再继续或恢复。每个正式运行保存输入、源文件与依赖锁哈希、资源记录和结果。

[文本研究入口](research-entry-migration.json)连接各路线的参数文件与 CLI。稿件编译及视觉审阅采用[当前出版工作流](../manuscript/README.md)。

## 验收边界

- 准备检查通过只表示运行条件就绪。解析、FEM、PEEC、RT0 和 Maxwell 各自检查电流、功率、残差及适用范围。
- 单网格七股 Maxwell 案例验证端口/功率与运行链路；结构排名仍须网格、边界、长度与数值不确定度研究。
- A–φ 入口复现保留场的势函数/规范条件失败；其成功执行不能改写成物理验收通过。
- 统一使用 SI、exp(+jωt)、RMS、20 °C 铜。2 mm Q1 是校准；最终 Q2 名义铜面积至少 5 mm²，传统多级 Litz 是强基线。

物理验收以 [tests/ACCEPTANCE.md](../tests/ACCEPTANCE.md) 和所选路线 README 为准。
