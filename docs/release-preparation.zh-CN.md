# 发布准备

[English](release-preparation.md) · [开发说明](development.zh-CN.md)

源码维护、科学构建和公开分发分别保留身份。准备阶段更新仓库接口、文档和发布元数据，并记录该源码版本的检查结果。新的物理研究和稿件重建使用独立运行号及验收记录。

## 标识源码与冻结稿件

使用 `git rev-parse HEAD` 记录精确源码提交，将对应验证记录与发布清单一起保存。当前稿件集由 `publication_review_20261015_03` 标识，包含六份双语完整稿件、六份原生 Notebook 及十八份 PDF。[交付哈希](../provenance/editorial/delivery-manifest.json)与[已上传附件记录](../provenance/editorial/online-assets.json)标识各文件。

出版 ZIP 包含该冻结构建的源码快照和产物。此后的仓库文档、CI 或下载机制调整由当前源码提交标识。使用当前软件和该出版包时，同时引用两者的身份。重新构建出版包需要新的产物身份、哈希及相应的编译／前端检查。

## 验证准备后的工作区

在干净检出的仓库中安装 `automation` 可选依赖后执行：

```text
python -B tools/CheckSourceCheckout.py --output outputs/ci/source-checkout.json
python tools/BuildPublicationIndex.py --check
python tools/BuildAgentCatalog.py --check
python tools/CheckReaderLinks.py
litz-research references verify
```

检查各个 CI 配置组合的结果，如实保留失败或不可用环境的记录。源码检查器验证可移植测试数据和元数据；原生求解器及稿件验收记录仍绑定于产生它们的运行。

根据 Git 跟踪的文件集合检查读者链接，而非仅检查开发者机器上的现有文件。完整 Markdown 稿件及轻量图件应能从源码工作区访问；PDF、Notebook 和 ZIP 链接应指向所选发布附件。索引应从同一份下载元数据重新生成并核验。

`docs/current-edition.json` 应覆盖三部作品的中英文版本，每份稿件包含三种 PDF 版式及一个 Notebook 记录。逐项核对附件名称、SHA256 和交付清单，保留 rc.1 历史索引及其原运行身份。根据来源记录验证 `data/catalog.json` 的数据集依赖、内容对象、文件映射、分片顺序和哈希；恢复所选数据集后应得到相同身份。

## 核验发布附件

对稿件索引或数据目录列出的每个附件，核对目标仓库、发布标签、附件名称、字节数和 SHA256。可以回读远端字节，或使用明确绑定该附件的服务端 SHA256，并记录验证方式。保留 `review_20261015_` 稿件附件的原名称及哈希。检查独立 PDF、Notebook、出版包、LaTeX 源码包、校验文件，以及 rc.1 和 rc.2 所需的数据归档分片。

检查仓库、源码包和分发归档中的凭据、商业授权文件、个人机器路径及第三方声明。原创软件、学术材料和上游组件分别遵循项目的[许可边界](../LICENSES/README.zh-CN.md)。科学软件及字体按各自条款单独安装。

## 发布版本并核验公开访问

发布每个版本时：

1. 确认源码提交、发布目标提交、附件清单、许可补充包和校验值，保持既有冻结产物的身份不变。
2. 将仓库设为 Public，并发布数据目录所需的每个 Release。当前目录使用 `v1.0.0-rc.1` 提供历史证据，使用 `v1.0.0-rc.2` 提供自动化及出版附件。仅公开仓库不会使 Draft 附件可被匿名下载。
3. 将公开目录设置为 `private: false`。每个分片保留用于附件 ID 核验的 API `url`，并在 `public_url` 中提供已核验的浏览器下载地址。确认 CLI 使用公开 URL 时不读取凭据；旧目录可以回退到匿名 API 读取。
4. 核对精确源码提交对应的托管 CI 矩阵。使用退出登录的会话和全新缓存，走通 README 到稿件附件的路径，并通过 CLI 恢复一个小数据集。匿名回读已列出的附件，核验下载字节数和 SHA256，保留每份记录的范围及时间。
5. 记录公开 URL、仓库可见性、Release 状态、源码提交、CI 结果和匿名下载记录，使发布说明与维护中的源码及冻结稿件身份一致。

[公开分发记录](open-source-readiness.zh-CN.md)连接已发布版本的实际观察结果。历史快照保留采集时的仓库与 Release 状态。源码 CI、科学验收和公开下载验证各有对应证据。

## 附件元数据检查工具

按[快照格式](release-snapshot.schema.json)保存 GitHub 仓库与 Release API 响应后执行：

```text
python tools/CheckReleaseReadiness.py --snapshot outputs/public-release-snapshot.json --output outputs/release-check.json
```

工具只比较已登记文件的身份与快照中的服务端 SHA256，不发起下载。检查通过表示附件元数据匹配；仓库可见性、Release 发布、下载目录和匿名回读各自报告状态。历史快照用于重放该次核验，实际发布时须重新获取。

许可补充包随出版 ZIP 一同分发，见[许可与成员清单](../LICENSES/publication-companion/README.zh-CN.md)和[补充附件哈希](../provenance/maintenance/supplemental-assets.json)。公开情况见[分发记录](open-source-readiness.zh-CN.md)。
