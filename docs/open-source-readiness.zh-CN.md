# 公开分发记录

[English](open-source-readiness.md) · [简体中文](open-source-readiness.zh-CN.md)

记录日期：2026 年 10 月 20 日。源码维护于 [HNNUYUXUAN/litz-wire-research](https://github.com/HNNUYUXUAN/litz-wire-research)，出版产物继续使用 `publication_review_20261015_03` 的运行身份。

## 维护后的源码与出版产物

README 按读者任务提供入口。自动生成的目录覆盖七条建模路线、五项工作流、六个自动化案例和六份完整稿件，附源码路径和原始字节哈希。[参考仓库记录](../provenance/maintenance/repository-patterns.json)列出本次查阅 general-physics-lab、thermal-pde-audit、phy-sim-llm 和 cluetide-review 的精确提交。

当前稿件索引和下载文件名统一从交付记录生成，旧 rc.1 索引按原始字节归档。贡献指南和开发说明均有独立中英文版本。Windows／Ubuntu 与 Python 3.11／3.12 的 CI 矩阵检查基础源码接口、阅读链接、目录检索以及后续稿件更新。

出版 ZIP 保留原构建的源码与产物。此后仓库维护使用自己的源码提交和测试记录。下载的 PDF、Notebook 与 ZIP 保留原始哈希；配套的[许可补充包](../LICENSES/publication-companion/README.zh-CN.md)记录冻结归档成员的许可范围与声明。

## 准备阶段的证据

下列检查记录于 2026 年 10 月 20 日的源码准备阶段，对应当时的准备版本。发布版本与公开访问的实测记录另列于下一节。

| 检查 | 实际结果 |
| --- | --- |
| 全新安装 | 独立 Windows Python 3.12 环境和含空格工作目录；依赖检查通过 |
| 基础源码与维护测试 | 本地通过 43 项测试 |
| 文献与模型发现 | 校验 60 条文献；发现 15 个 CLI 模型入口 |
| 阅读路径 | Git 跟踪文件内的 Markdown 相对链接检查通过；外部 URL 和标题锚点不在该检查器范围内 |
| 发布附件元数据 | 66 个数据分片、27 个出版附件和一份许可补充包与 API 名称、字节数及 SHA256 一致 |
| 冻结身份 | 原出版 ZIP 哈希和归档 rc.1 索引保持原样 |
| 许可补充包 | 索引原 ZIP 内的 1,315 个成员；确定性构建与包内成员校验通过 |

证据：[源码测试](../provenance/maintenance/source-checkout-20261020.json)、[维护测试](../provenance/maintenance/maintenance-tests-20261020.json)、[安装环境](../provenance/maintenance/fresh-environment-20261020.json)、[阅读路径](../provenance/maintenance/reader-links-20261020.json)、[附件元数据](../provenance/maintenance/release-assets-20261020.json)、[保留身份](../provenance/maintenance/preserved-identities-20261020.json)。

针对性的[公开内容检查](../provenance/maintenance/source-disclosure-20261020.json)记录已检查的源码与历史范围、所配置的凭据或私钥签名、文件数量及排除项。该记录分别说明二进制内容和外部证据归档的检查边界。

## 发布版本与公开访问

维护源码版本为 `v1.0.0-rc.3`；冻结证据与稿件继续附于 rc.1 和 rc.2。发布检查对应的源码提交：[`01aa0bc3dc12a548301a148f8fc99e12a241e075`](https://github.com/HNNUYUXUAN/litz-wire-research/commit/01aa0bc3dc12a548301a148f8fc99e12a241e075)。观测时间：`2026-10-19T17:41:25.820878+00:00`。

| 检查 | 观测结果 |
| --- | --- |
| 托管 Windows／Ubuntu × Python 3.11／3.12 矩阵 | 四个组合全部通过 |
| 仓库可见性 | Public（公开） |
| `v1.0.0-rc.1` 历史证据 Release | 已发布 |
| `v1.0.0-rc.2` 自动化与出版 Release | 已发布 |
| `v1.0.0-rc.3` 维护源码 Release | 已发布 |
| 发布版本的源码与维护测试 | 四个矩阵组合各通过 59 项测试 |
| 公开数据目录与免凭据 CLI 恢复 | 全新 Python 3.12 环境恢复全部 874 个解析文件；679 个依赖及数据对象（660,867,640 字节）哈希全部通过；未使用凭据或认证子进程 |
| 匿名附件回读与哈希核验 | 127/127 个 Release 附件完成无凭据全量下载，8,578,518,566 字节及全部 SHA256 一致；rc.3 源码 ZIP 的 972 个文件全部匹配提交 |

证据：[托管 CI 运行](https://github.com/HNNUYUXUAN/litz-wire-research/actions/runs/39289553044)、[发布状态与元数据](../provenance/public-release/repository-releases.json)、[匿名下载与恢复](../provenance/public-release/README.zh-CN.md)。每份记录注明源码版本、时间和检查范围。

公开数据目录保留含附件 ID 的 API 地址，并提供已核验的浏览器下载地址。CLI 使用公开下载模式，不读取 GitHub 凭据。[数据指南](datasets.zh-CN.md)介绍按需恢复和离线复用；[发布流程](release-preparation.zh-CN.md)说明后续版本如何重复执行源码、附件和匿名访问检查。历史快照保留各自采集时观测到的可见性与 Release 状态。

本轮维护未执行物理求解或重建稿件。既有数值验收与待研究问题继续绑定各自的原始证据。

公开入口和验收工具提交 `76323f60fa3812e8e817a7b756d490dfa37ffb15` 的后续 CI 同样四组全过，每组 74 项测试；见[记录](../provenance/public-release/ci-maintenance.json)。
