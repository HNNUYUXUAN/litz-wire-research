# 学术稿件与构建

[English](editions.md)

[稿件索引](../publications/README.zh-CN.md)提供六份中英文 LaTeX 主稿及生成的 Markdown 阅读稿。完整报告采用单栏，自动化与物理论文采用 IEEE journal。[出版清单](../manuscript/latex-publication.json)记录身份、章节顺序、版式和证据关系。

## 构建与检查

按 [Conda 环境说明](../automation/environments/README.md)重建项目环境，固定 Pandoc 3.13 并安装文档依赖。XeLaTeX、SimSun 与 Times New Roman 是外部安装。源码目录包含所需图件、题录和保留的数值输入。

```bash
.conda/project/python.exe -m litz_research.cli build --run-id scholarly_local_01
.conda/project/python.exe tools/RenderLatexReview.py --run-id scholarly_local_01
.conda/project/python.exe tools/SelectPublicationBuild.py --run-id scholarly_local_01
.conda/project/python.exe tools/BuildAgentCatalog.py
```

默认构建转换六份主稿、编译 PDF、核验身份并打包 LaTeX、图件、数据和 Markdown。独立阶段为 `preflight`、`documents`、`pdf`、`verify` 和 `package`。`--edition` 与 `--language` 可限制转换范围；编译和交付要求六份主稿齐全。源码改变后使用新运行号。选择构建更新阅读导航，并保留该构建的逐页检查状态。

检查全部渲染页面，记录 PDF 哈希和审阅结论。编译日志检测缺字、超宽溢出和未解析引用，视觉审阅补充检查实际页面。PDF 用于本地预览和验收。

## 主稿与阅读稿一致性

标题、摘要、关键词、正文与图注在 LaTeX 中维护。稳定段落 ID、公式标签、图件身份和文献键连接主稿与阅读稿。数值替换在转换前从保留证据重新计算。遇到未支持命令、未解析引用或往返转换丢失文字与数学内容时构建失败。生成的 UTF-8 文件采用 LF 换行，使各系统具有相同字节身份。

[稿件维护说明](../manuscript/README.md)描述转换契约；[引用指南](citation-guide.zh-CN.md)解释统一题录。[历史发布](../publications/HISTORY.zh-CN.md)保留原附件身份和适用许可。
