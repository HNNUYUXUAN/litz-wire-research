# 学术稿件与构建

[English](editions.md)

[学术文件目录](../publications/README.zh-CN.md)提供完整研究报告、自动化方法论文及 Litz 物理建模论文的中英文版本。每部作品包含 Markdown、原生 Wolfram Notebook，以及通用单栏、IEEE 期刊和 IEEE 会议三种 LaTeX／PDF 版式。版式共享完整内容，会议版不设置篇幅上限。

## 构建完整作品

安装文档依赖，并按[数据集说明](datasets.zh-CN.md)恢复输入。新的源码工作区在组合当前稿件前需要准备科学图件输入。随交付提供的可迁移稿件包已包含选定面板，可直接编译其中的 LaTeX。

```powershell
python -m pip install -e ".[documents,figures,automation]"
python tools/PreparePublicationInputs.py
litz-research build --run-id scholarly_local_01 --edition all --language all --form merged --layout all --stage documents
litz-research build --run-id scholarly_local_01 --stage pdf
litz-research build --run-id scholarly_local_01 --stage notebooks
litz-research build --run-id scholarly_local_01 --stage verify
litz-research build --run-id scholarly_local_01 --stage package
```

作品选择为 `report`、`paper`、`automation`、`all`；版式选择为 `single`、`ieee-journal`、`ieee-conference`、`all`。旧 `ieee` 选项对应 IEEE 期刊版。输入清单改变时使用新的运行身份。构建产物、编译日志、Notebook 回执及验收详情写入对应 `outputs/` 目录。

## 阅读与复用

PDF 由对应 LaTeX 源码编译。独立模板展示各文档类的作者栏、摘要、图件、公式和引用写法。原生 Notebook 支持检查保存的三维图形。科研计算通过独立[模型入口](tool-workflows.zh-CN.md)执行。

[成稿规范](editorial-style.zh-CN.md)说明样稿 09 的排版方式及 IEEE 适配，[引用指南](citation-guide.zh-CN.md)说明统一题录。历史稿件保留数据集身份，并与当前稿件分别索引。
