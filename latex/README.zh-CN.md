# LaTeX 构建

学术稿件由 `manuscript/` 中的双语 Markdown 和共用清单生成。XeLaTeX 使用宋体排版中文、Times New Roman 排版西文和数字，数学使用对应 TeX 宏包。IEEEtran 按其上游 LPPL 条款分发。

在工程根目录安装文档依赖并检查工具链：

```powershell
python -m pip install -e ".[documents,figures]"
litz-research doctor
litz-research data fetch publication-inputs
python tools/PreparePublicationInputs.py
litz-research build --run-id paper_example_01 --edition paper --language en --form merged --layout all --stage documents
litz-research build --run-id paper_example_01 --edition paper --language en --form merged --layout all --stage pdf
```

`--edition` 支持 `report`、`paper` 和 `automation`；`--layout` 支持 `single`、`ieee-journal`、`ieee-conference`，`all` 生成全部组合。`ieee` 保留为期刊版别名。

可执行文件不在 PATH 时，配置 `LITZ_XELATEX` 与 `LITZ_LATEXMK`。字体通过具有相应许可的操作系统或字体发行包安装。独立模板展示三种版式的正文、公式、表格与引用写法；完整稿件的编号来自共用内容构建。

编译文件、日志、依赖版本、源码哈希和真实退出码写入 `outputs/` 对应运行目录。PDF 结构与页面检查使用文档依赖组中的 pypdf 和 pypdfium2。

[English](README.md)
