# 引用软件、数据与自动化方法

`references/library.bib` 是人工维护的统一题录源。`references/sources.json` 使用相同稳定 key，记录实际作用、实现位置、版本或提交、许可及使用证据。兼容 BibTeX 和 CSL 文件由生成器导出。修改后执行：

```powershell
litz-research references build
litz-research references verify
```

每部完整作品按首次引用生成显示编号；中文、英文及 Markdown、Notebook、LaTeX 共用该作品的编号映射。历史稿件保留原有来源身份。

软件引用示例：缪雨轩，*Litz Wire Research: agent-driven reproducible modeling and simulation*，1.0.0-rc.2，2026。附上[版本链接](https://github.com/HNNUYUXUAN/litz-wire-research/tree/v1.0.0-rc.2)、`git rev-parse v1.0.0-rc.2` 返回的实际提交及访问日期。本地修订应使用本地交付记录中的提交，而非沿用旧标签身份。

数据引用包含仓库版本、数据集名、实际来源运行号、结果文件 SHA256 和目录清单身份。自动化方法引用包含方法文档、版本或提交，以及 `automation/examples/verification.json` 中的对应案例。目前成果未分配 DOI。

`CITATION.cff` 描述软件引用信息。原创文稿、图件与数据采用 CC BY 4.0，上游软件适用其自身许可。来源登记分别记录仓库核查、运行依赖、代码采用和比较证据；AI 参与及作者责任见[致谢](../ACKNOWLEDGMENTS.zh-CN.md)。

[English](citation-guide.md)
