# 开发说明

[English](development.md)

## 源码与科学输入

`models/` 保存七条物理路线；`adapters/` 连接 Wolfram、Ansys 和 GPU 执行；`automation/` 提供工作流、技能及 MCP／客户端配置；`shared/` 提供共用数值和路径工具。`python/litz_research/` 实现 CLI、任务管理、数据恢复与独立解析模型。`src/` 保留兼容入口，学术构建实现位于 `tools/publication/`。

新增案例使用明确参数文件和唯一运行号。记录源码哈希、单位、相量约定、材料、边界、实际退出码、执行状态和物理验收。复数保留实部与虚部。[验收标准](../tests/ACCEPTANCE.zh-CN.md)定义各模型需要的检查。

## 运行环境

基础解析和数据接口支持 Python 3.11 或更新版本。Ansys MCP 使用 Python 3.12 或更新版本及独立固定依赖。成稿通过具有许可证的 Wolfram 创建原生 Notebook，通过 XeLaTeX 和 latexmk 编译 PDF，并使用本机宋体与 Times New Roman。

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[documents,figures,automation,audit]"
.venv/Scripts/litz-research.exe doctor
```

可执行文件依次从 `LITZ_<TOOL>`、本地 `litz.config.json` 的 `tools.<tool>` 和 PATH 解析。例如，用 `LITZ_WOLFRAMSCRIPT`、`LITZ_XELATEX`、`LITZ_LATEXMK` 指定安装位置。资源策略为八个逻辑处理器、24 GiB 任务内存及 8 GiB 系统空闲内存，求解器许可可进一步限制资源。

## 验证与稿件维护

物理方程、端口约束、功率积分、数据身份或进程归属发生改变时执行针对性测试。Python 测试入口为 `python -m unittest discover -s tests`；所需可选依赖及历史数据由对应测试和路线指南说明。新的求解使用独立运行号。

双语 Markdown 章节与 `manuscript/publication.json` 定义三部完整作品。公式、量值、图件身份及每部作品的引用编号在各格式间共用。[稿件指南](editions.zh-CN.md)说明构建、模板和可迁移包。面向读者的双语正文直接维护于 Markdown，索引生成器读取正文并生成清单。

`data/catalog.json` 定义分片、内容对象、依赖和原相对路径。恢复器在复用数据前检查分片、对象和文件哈希；离线恢复使用相同检查。来源记录分别保存原件、元数据派生副本和新运行产物。
