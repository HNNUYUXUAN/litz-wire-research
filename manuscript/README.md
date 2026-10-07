# Litz 双语学术成稿源

作者：缪雨轩 / Miao Yuxuan。单位：淮南师范学院 / Huainan Normal University。

`publication.json` 管理报告、论文、双语段落身份、公式、图件、文献及冻结来源。`report/` 与 `paper/` 中的 Markdown 是人工编辑正文；各语言以稳定的块身份配对。报告包括十二章与四项附录，论文包括五章与三项补充材料。

正文块以 `<!-- id: ... -->` 声明身份。`{{metric:...}}` 引用冻结数值；`{{equation:...}}` 和 `{{figure:...}}` 指定展示位置；`{{eqref:...}}` 引用公式；`[@P01; @N01]` 引用共享 BibTeX 库。每张图在每套合并稿中具有一个展示位置。章节稿提取合并稿的对应正文块，使用相同的显示编号。

在项目虚拟环境执行 `python -m pip install -e ".[documents,figures]"` 安装构建依赖，已验收的 Windows Python 3.12 版本组合见 `requirements-windows-py312.lock`。Windows 编译环境包括 MiKTeX、XeLaTeX、BibTeX、latexmk 和 Wolfram 前端。构建参数由工程根目录派生路径，支持目录名包含空格。

```powershell
litz-research data fetch publication-inputs
litz-research build --run-id publication_YYYYMMDD_01 --stage all
```

Python 入口为 `src/BuildPublicationEdition.py`。可选参数包括 `--edition report|paper|all`、`--language zh-CN|en|all`、`--source-manifest`、`--form merged|chapters|all`、`--layout single|ieee|all` 和 `--stage`。阶段顺序为正文及图件准备、Notebook、PDF、验收、封装。独立阶段通过相同运行号接续；正式构建使用新运行号。

构建读取冻结计算、已验收单图与正文；新图件由 Wolfram 导出。过程保留来源、源码、参数、编译退出码及产物 SHA256。任务使用最多八个逻辑处理器、24 GiB 内存并保留 8 GiB 系统空闲内存。

字体为中文宋体和西文 Times New Roman，独立图宽 88.9 mm、组图宽 182 mm。Notebook 保存静态正文、图表、公式和原生三维图形。PDF 提供单栏阅读版与 IEEE 风格双栏版。

模板来源与许可见 `references/templates/manifest.json`。IEEEtran 保留原有 LPPL 许可；文献与项目数据按各自的权利记录管理。正文使用统一文献身份，文献条目与来源记录共同支持核查。

图题保存在共享图件的 `title` 字段，报告与论文的双语说明保存在 `descriptions`。图题居中，说明另段左对齐；子图标号位于面板上方。示意图由 `PublicationDiagrams.py` 定义节点、关系和分组，Wolfram 按物理尺寸独立导出。
