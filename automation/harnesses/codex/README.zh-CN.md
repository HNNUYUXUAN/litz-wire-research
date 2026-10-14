# Codex 接入

1. 克隆仓库，在独立 Python 环境安装 `python -m pip install -e ".[automation]"`。
2. 按固定版本接入说明准备 Wolfram、AEDT 及其许可证。
3. 执行 `litz-research automation configure --output build/codex-config --ansys-python <Ansys MCP 环境中的 Python 路径>`，生成可检查的配置。
4. 核对生成的 TOML，并合并到所选项目的 `.codex/config.toml`。本机可执行文件路径保存在本地配置中。刷新客户端后查看实际工具清单，执行两项协议探针。
5. 将需要的 `automation/skills/` 目录安装到客户端技能目录，或明确读取对应 `SKILL.md`。根目录 `AGENTS.md` 提供共用研究约定。
6. 从 `automation/examples/` 选取具体任务，检查实际工具返回、源码、结果文件及物理验收。

长任务示例：`litz-research jobs submit peec --case tutorial --run-id peec_job_01`；使用 `litz-research jobs status peec_job_01` 查询。`jobs cancel` 请求取消，`jobs resume --new-run-id` 使用保存输入建立关联的新运行。

已有验证由 Codex 编排 `automation/mcp/client.py` 标准客户端并调用官方工具完成。客户端原生注册状态与桥接执行分别记录。模型和客户端版本采用实际可见信息。

[官方 MCP 配置说明](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) · [English](README.md)。项目配置生成器可通过 WolframScript 查找已安装内核，并明确报告尚未解析的路径。
