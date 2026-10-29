# 开发说明

[English](development.md) · [参与贡献](../CONTRIBUTING.zh-CN.md)

## 源码布局

`models/` 保存七条物理路线；`adapters/` 连接 Wolfram、Ansys 和 GPU 执行；`automation/` 提供工作流、技能及 MCP／客户端配置；`shared/` 提供共用数值和路径工具。`python/litz_research/` 实现 CLI、任务管理、证据恢复与独立解析模型。`src/` 保留兼容入口，稿件转换实现位于 `python/litz_research/latex_publication.py`，编译与审阅工具位于 `tools/`。

新增案例使用明确参数文件和唯一运行号，保存源码哈希、单位、相量约定、材料、边界、用时、实际退出码、执行状态及物理验收。复数量保留实部与虚部。[验收标准](../tests/ACCEPTANCE.zh-CN.md)定义各模型需要的检查。

## 安装源码接口

源码接口需要 Python 3.11 或更新版本。CI 配置覆盖 Windows、Ubuntu 及 Python 3.11、3.12；实际通过的组合以对应任务结果为准。安装 CLI 后保留源码工作区：模型源码、配置和清单从本仓库读取。

Windows Git Bash：

```bash
python tools/CondaEnvironments.py rebuild project --prefix .conda/project
.conda/project/python.exe -B tools/CheckSourceCheckout.py
```

Linux：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[automation]'
.venv/bin/python -B tools/CheckSourceCheckout.py
```

下文的 `python` 和 `litz-research` 均指此环境内的程序。可以直接使用其完整执行路径，或在当前 shell 中激活环境。

## 选择验证范围

| 范围 | 输入与环境 | 验证入口 |
| --- | --- | --- |
| 源码工作区 | Python 及 `automation` 可选依赖 | `python -B tools/CheckSourceCheckout.py` |
| 历史证据 | 按目录恢复的所选数据集 | `litz-research data verify <dataset>` 及相应证据检查 |
| 原生模型 | 所需 Wolfram、Ansys 或 GPU 环境、许可和案例输入 | 对应路线的执行、守恒及敏感性检查 |
| 学术稿件 | 保留图件与数值输入、Pandoc 3.13、文档依赖和 XeLaTeX | 源稿／阅读稿身份、数值映射、引用、编译和页面检查 |

源码检查器使用明确的可移植测试清单及临时数据，验证恢复完整性、参数与进程归属约定、模型入口、参考文献和当前稿件元数据。它阻止启动子进程、建立网络连接和调用物理求解。通过以下命令保存机器可读记录：

```text
python -B tools/CheckSourceCheckout.py --output outputs/ci/source-checkout.json
```

其他测试位于 `tests/`。根据所改实现选择测试，并先提供其要求的可选依赖及数据集。完整测试发现包含原生环境和冻结数据使用者，范围大于源码检查。源码检查说明接口与元数据的一致性；科学结论需要对应模型的验收依据。

## 配置原生工具

Ansys MCP 服务在独立的 Python 3.12 或更新环境中运行，固定依赖及安装步骤见 [Ansys MCP](../automation/mcp/ansys/README.zh-CN.md)。[Wolfram MCP](../automation/mcp/wolfram/README.zh-CN.md)记录其上游和探针。[工具工作流](tool-workflows.zh-CN.md)提供模型教程和完整研究入口。

可执行文件依次从 `LITZ_<TOOL>`、本地 `litz.config.json` 的 `tools.<tool>` 和 PATH 解析。例如，用 `LITZ_WOLFRAMSCRIPT`、`LITZ_XELATEX` 或 `LITZ_LATEXMK` 指定安装位置。使用 `litz-research doctor` 检查实际环境；需要有界的 Wolfram 版本与算术探针时添加 `--kernel`。

原生研究任务遵守八个逻辑处理器、24 GiB 任务内存及 8 GiB 系统空闲内存的资源预算，许可可能进一步限制规模。仅管理任务所属进程，保留中断记录；从核实过的源码与输入身份接续，或创建具有关联关系的新运行。

## 维护证据与稿件

`data/catalog.json` 定义归档分片、内容对象、依赖和原始路径。恢复过程检查分片、对象和最终文件哈希，离线恢复使用相同身份。历史证据保存在对应版本的 `data/evidence/` 根目录，新运行写入 `outputs/`。详见[数据集](datasets.zh-CN.md)。

六份 LaTeX 主稿与 `manuscript/latex-publication.json` 定义三部双语作品，公式、量值、图件身份与文献键和生成 Markdown 共用。先更新 `references/library.bib` 与 `references/sources.json`，再重新构建。[稿件指南](editions.zh-CN.md)说明转换、独立编译、页面审阅和当前构建选择。

同步维护双语读者正文及索引生成器。`docs/current-edition.json` 标识当前六份稿件的 LaTeX 源稿、生成阅读稿和输入哈希；历史出版记录保持原运行身份。`publication_review_20261015_03` 的出版 ZIP 是冻结构建，后续源码维护以独立的 Git 提交和检查记录标识，详见[发布准备](release-preparation.zh-CN.md)。
