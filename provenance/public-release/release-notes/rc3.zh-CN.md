# Litz Wire Research v1.0.0-rc.3

本次源码维护发布为 Litz Wire Research 提供公开下载器、可复现的源码 CI 与双语阅读入口。源码标签标识维护后的代码；历史数据和冻结稿件继续附于 rc.1 与 rc.2。

## 阅读与复现

- 从 [README](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/README.zh-CN.md) 或[自动化指南](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/automation/README.zh-CN.md)进入。
- 阅读[完整研究报告、自动化方法论文与物理研究论文](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/publications/README.zh-CN.md)。三部作品各有独立中英文版本，共六份 Markdown 稿件、六份原生 Wolfram Notebook，以及通用期刊单栏、IEEE 期刊和 IEEE 会议三种版式的十八份 PDF。
- 从 [rc.2](https://github.com/HNNUYUXUAN/litz-wire-research/releases/tag/v1.0.0-rc.2) 下载当前选用的 27 个出版附件：18 份 PDF、六份 Notebook 和三个 ZIP。使用出版包时同时下载 `litz_publication_licenses_20261020.zip`；其中的成员索引列出适用许可和第三方声明。
- 按[数据指南](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/docs/datasets.zh-CN.md)恢复所需研究证据。公开下载无需账号或令牌。数据目录从 [rc.1](https://github.com/HNNUYUXUAN/litz-wire-research/releases/tag/v1.0.0-rc.1)取得历史证据，从 rc.2 取得自动化证据。

## 源码维护

本次维护增加按任务组织的阅读入口、机器可读的模型／工作流／稿件目录、自动生成的出版索引、双语贡献与开发指南，以及 Windows／Ubuntu × Python 3.11／3.12 源码 CI。下载器保留 GitHub 附件 ID，采用核验过的公开下载地址，并检查分片及恢复文件的哈希。

本次发布检查对应的源码提交：[`01aa0bc3dc12a548301a148f8fc99e12a241e075`](https://github.com/HNNUYUXUAN/litz-wire-research/commit/01aa0bc3dc12a548301a148f8fc99e12a241e075)。源码与维护测试：四个矩阵组合各通过 59 项测试。托管 CI：四个组合全部通过（[运行记录](https://github.com/HNNUYUXUAN/litz-wire-research/actions/runs/39289553044)）。匿名下载与恢复结果：127/127 个 Release 附件完成无凭据全量下载，8,578,518,566 字节及全部 SHA256 一致；rc.3 源码 ZIP 的 972 个文件全部匹配提交; 全新 Python 3.12 环境恢复全部 874 个解析文件；679 个依赖及数据对象（660,867,640 字节）哈希全部通过；未使用凭据或认证子进程。[公开分发记录](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/docs/open-source-readiness.zh-CN.md)链接源码、发布状态与下载证据。

## 科学内容与产物身份

稿件以 `publication_review_20261015_03` 冻结；附件保留 `review_20261015_` 文件名和原始 SHA256 身份。出版 ZIP 包含该次构建的源码快照，此后的 CI、阅读入口和下载器维护由上列源码提交标识。rc.3 标签标识维护后的源码。既有 rc.1 与 rc.2 标签继续标识原提交，其数据和出版附件各有独立清单。

研究统一使用 SI 单位、`exp(+jωt)` 和 RMS 相量。直径 2 mm 的圆导线用于校准；最终 Q2 设计要求名义铜截面至少 5 mm²。模型依据股间绝缘和共同端电压求解，不预先规定股间均流。200 kHz、1 mT RMS 外场下的 RT0 长方体采用零净输运条件，末两次空间细化损耗变化为 0.655090% 和 0.362916%，达到已记录的 1% 细化目标。保存的三维 A–φ 圆柱仍未通过标量势与规范验收。真实换位结构的性能排名需要对齐端接和回流条件，并完成三维验证与受控实验。本次维护发布未新增物理求解或重建稿件。

原创软件采用 MIT 许可；原创正文、图件和数据采用 CC BY 4.0。上游组件保留各自条款，Wolfram 与 Ansys 为外部授权软件。详见[许可说明](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/LICENSES/README.zh-CN.md)、[致谢](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/ACKNOWLEDGMENTS.zh-CN.md)与[引用指南](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/docs/citation-guide.zh-CN.md)。

后续公开下载入口与验收工具提交 `76323f6` 的四组 CI 各通过 74 项测试（[运行记录](https://github.com/HNNUYUXUAN/litz-wire-research/actions/runs/39293290975)）。
