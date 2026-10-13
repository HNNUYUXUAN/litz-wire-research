# 开发说明

`python/litz_research/` 实现安装入口、命令行、配置、独立 Python Bessel 校准及数据下载。`src/` 保存 Wolfram 科学模块、阶段运行器、Ansys 适配和文档构建；`configs/` 保存物理输入；`tests/` 保存回归；`manuscript/publication.json` 统一正文、公式、图件和量值身份。

模型扩展使用明确的输入记录和独立运行号，保存 `source_model`、`run_id`、执行状态、物理验收状态、单位、相量约定、材料参数、源码哈希、用时和实际退出码。复数保留实部与虚部，幅值与相位由它们计算。物理约定与容差以建模约定和 `tests/ACCEPTANCE.md` 为准。

Python 3.11+ 支持数据读取和解析例子。文档构建依赖通过安装 extras 配置。现有科学基线为 Windows Wolfram 15.0；内核用于科学模块，前端用于 Notebook 和原生三维图形。PDF 使用 XeLaTeX、BibTeX、latexmk，字体为本机宋体和 Times New Roman，各字体遵循自身安装许可。

工具位置按 `LITZ_<工具名>` 环境变量、本地 `litz.config.json` 的 `tools` 字段、PATH 顺序解析。运行器记录本轮进程树及创建身份，保留准确退出码。当前资源策略为八线程、24 GiB 任务内存和 8 GiB 系统余量。Ansys 需要 Maxwell 和匹配的 PyAEDT；Student 网格与四核限制按算例执行。GPU 路线使用对应 Wolfram CUDALink 环境及同模型 CPU 对照。

```powershell
python -m unittest discover -s tests -p test_research_cli.py
litz-research run analytic --run-id analytical_validation_01
litz-research run wolfram-analytic --run-id wolfram_validation_01
litz-research data verify
```

数据目录记录数据集依赖、按顺序拼接的 gzip tar 分片、对象哈希和逻辑文件路径。分片还原后仅包含 `objects/<sha256>` 普通文件。共享对象通过数据集依赖复用。下载、解包和逻辑路径恢复分别核对哈希；已有文件核对后复用，离线模式使用同一缓存。来源记录逐件绑定原始哈希、候选哈希、权利归属、处理方法及科学核验。

修改成稿时先编辑中英文对应段落和共享清单，再统一构建。章节稿从合并稿结构提取；源码、单图、组图、PDF 和保存后的 Notebook 均记录哈希。修改科学数据时建立独立来源身份和验收记录。同一运行号的恢复步骤核对输入清单及已完成依赖。
