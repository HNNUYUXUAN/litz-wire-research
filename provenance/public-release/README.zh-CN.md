# 公开发布验收

[English](README.md) · [简体中文](README.zh-CN.md)

仓库以及 rc.1、rc.2、rc.3 三个预发布版本均已公开。源码版本 `v1.0.0-rc.3` 对应提交 `01aa0bc3dc12a548301a148f8fc99e12a241e075`。这些记录保存 2026 年 10 月 20 日（Asia/Shanghai）发布前后的实际验收。

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 发布源码 CI | Windows／Ubuntu × Python 3.11／3.12，四个组合各通过 59 项测试 | [CI](ci-source.json) |
| 后续公开入口与验收工具 CI | 提交 `76323f6`，相同四个组合各通过 74 项测试 | [维护 CI](ci-maintenance.json) |
| 仓库与 Release 状态 | 仓库 Public，三个预发布版本均已发布 | [API 元数据](repository-releases.json) |
| 版本标签身份 | rc.1、rc.2 保持原始提交；rc.3 标识本次维护源码 | [远端标签](tag-identities.json) |
| rc.1／rc.2 全部附件 | 127 个附件完成匿名全量下载，共 8,578,518,566 字节，SHA256 全部一致 | [下载收据](anonymous-assets.json) |
| 已登记分发资产 | 66 个证据分片、27 个出版文件和一个许可配套包，全部发布条件满足 | [清单验收](release-readiness.json) |
| 公开 rc.3 源码包 | 972 个文件、80,001,469 原始字节与固定 Git 提交完全一致 | [源码收据](verification/public-receipts/source-verification.json) |
| 全新环境、缓存中的已安装 CLI | 恢复 874 个解析文件；679 个唯一对象、660,867,640 字节通过核验 | [CLI 收据](verification/public-receipts/cli-restoration-verification.json) |

[汇总与收据哈希](summary.json)。127 个附件包括 rc.1、rc.2 上传的全部历史文件，其中 94 个属于当前登记资产。GitHub 自动生成的 rc.3 源码归档有独立收据。下载字节数与恢复对象字节数分别描述不同阶段，不应相加。

保存的发布说明：[rc.1](release-notes/rc1.zh-CN.md)、[rc.2](release-notes/rc2.zh-CN.md)、[rc.3](release-notes/rc3.zh-CN.md)。同目录保存各版对应的英文来源。

附件和源码通过无凭据 HTTPS 下载，不使用 Cookie 或环境代理凭据。已安装 CLI 执行实际参数解析、下载、解包和恢复代码；验收器对 HTTP 传输加入观测和拦截，以拒绝认证请求头及认证子进程。所有登记目标和缓存最初均为空。[再现指南](verification/INTEGRATION.zh-CN.md)说明这些观测与拦截的具体范围。

匿名 API 元数据请求受到限流后，附件身份清单由有仓库权限的 GitHub CLI 读取。元数据读取和匿名内容下载分别提供证据。下载收据记录完整 GET 与哈希；清单验收器只核对提供的元数据和收据。本机路径标记、原始及便携收据的哈希见[转换清单](verification/public-receipts/portable-receipts-manifest.json)。

源码与 CLI 验收工具在 rc.3 标签之后维护，其 14 项离线测试与该标签的 59 项 CI 测试分别记录。[独立安装清单审计](verification/public-receipts/installed-package-binding.json)还将全部 13 个已安装 Python 文件与不可变 Git 文件清单逐项核对。稿件图件、PDF、Notebook、源码 ZIP 和科学验收继续保留冻结构建与运行身份。本次发布转换没有新增物理求解或重建稿件。

从仓库根目录使用新的输出路径，可重复全部附件验收：

```text
python tools/VerifyAnonymousReleaseAssets.py --snapshot provenance/public-release/repository-releases.json --output outputs/new-anonymous-downloads.json --all-assets --workers 4
python tools/CheckReleaseReadiness.py --snapshot outputs/new-anonymous-downloads.json --output outputs/new-release-audit.json
```

保存的元数据属于历史观测。检查后续版本时，应重新获取仓库与 Release 快照。源码及已安装 CLI 的再现步骤见[双语指南](verification/INTEGRATION.zh-CN.md)。
