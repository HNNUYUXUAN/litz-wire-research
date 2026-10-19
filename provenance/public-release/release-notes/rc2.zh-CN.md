# Litz Wire Research v1.0.0-rc.2 — 自动化与冻结出版产物

本 Release 保留自动化研究与稿件产物。既有标签继续指向 [`15df5069e4f370c130ac0306bc65f441a64b7ad5`](https://github.com/HNNUYUXUAN/litz-wire-research/commit/15df5069e4f370c130ac0306bc65f441a64b7ad5)；后续稿件附件由各自的运行身份与清单独立标识。

[自动化示例](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/automation/examples/README.zh-CN.md)覆盖六类具有实际记录的案例：Wolfram 建模与 Notebook 创建、原生 Maxwell 建模求解、Wolfram—Maxwell 比较、模型扩展、错误诊断与修复，以及未通过物理验收时的分析。连接、工具执行、求解完成和科学验收分别记录。使用当前 CLI 的 `automation-rc2` 数据集可以恢复这些保存证据。

## 当前稿件附件

当前选用的出版集为 `publication_review_20261015_03`，包含 27 个保留 `review_20261015_` 文件名前缀的附件：

- 十八份 PDF：三部作品 × 两种语言 × 三种版式，即通用期刊单栏、IEEE 期刊和 IEEE 会议。
- 六份原生 Wolfram Notebook：完整研究报告、自动化方法论文与物理研究论文，各有独立中英文版本。
- 三个 ZIP：出版包、可独立编译的 LaTeX 源码包和视觉候选包。

[出版索引](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/publications/README.zh-CN.md)链接六份完整 Markdown 稿件与单份附件。本 Release 还提供 `review_20261015_SHA256SUMS.txt`。使用冻结出版 ZIP 时一并下载 `litz_publication_licenses_20261020.zip`，其中附许可文本、第三方声明与逐成员许可索引。较早的源码归档、参考稿与示例稿保留原文件名。

出版 ZIP 包含当次构建的源码快照。维护后的源码、公开下载器与当前源码 CI 请使用 [rc.3](https://github.com/HNNUYUXUAN/litz-wire-research/releases/tag/v1.0.0-rc.3)。数据目录从 [rc.1](https://github.com/HNNUYUXUAN/litz-wire-research/releases/tag/v1.0.0-rc.1) 恢复历史科学证据。[公开分发记录](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/docs/open-source-readiness.zh-CN.md)链接公开访问与哈希核验的实际记录。

## 科学范围与复用

七条建模路线保留各自假设、单位、边界条件和验收状态。冻结的外场 RT0 长方体证据记录末两次空间细化损耗变化为 0.655090% 和 0.362916%，达到该算例的 1% 细化目标；其物理对象是零净输运条件下的外场吸收。保存的 A–φ 圆柱标量势与规范检查仍未通过。二维 Maxwell 自动化及限定条件下的比较保留独立证据，并与历史 Ansys 原生三维接口诊断分别记录。真实换位结构排名与实验验证仍属后续研究。这些结论来自原有科学记录，本次公开发布未执行求解或重建稿件。

原创软件采用 MIT 许可；原创正文、图件和数据采用 CC BY 4.0。上游组件保留各自条款，Wolfram 与 Ansys 为外部授权软件。详见[许可说明](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/LICENSES/README.zh-CN.md)、[致谢](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/ACKNOWLEDGMENTS.zh-CN.md)与[引用指南](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/docs/citation-guide.zh-CN.md)。
