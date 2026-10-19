# 开源准备记录

[English](open-source-readiness.md) · [简体中文](open-source-readiness.zh-CN.md)

记录日期为 2026 年 10 月 20 日。源码候选维护于 `HNNUYUXUAN/litz-wire-research`，出版产物继续使用 `publication_review_20261015_03` 的运行身份。

## 已完成的维护

README 按读者任务提供入口。自动生成的目录覆盖七条建模路线、五项工作流、六个自动化案例和六份完整稿件，附源码路径和原始字节哈希。[参考仓库记录](../provenance/maintenance/repository-patterns.json)列出本次查阅 general-physics-lab、thermal-pde-audit、phy-sim-llm 和 cluetide-review 的精确提交。

当前稿件索引和下载文件名统一从交付记录生成，旧 rc.1 索引按原始字节归档。贡献指南和开发说明均有独立中英文版本。Windows／Ubuntu 与 Python 3.11／3.12 的 CI 矩阵检查基础源码接口、阅读链接、目录检索以及后续稿件更新。

## 已记录的检查

| 检查 | 实际结果 |
| --- | --- |
| 全新安装 | 独立 Windows Python 3.12 环境和含空格工作目录；依赖检查通过 |
| 基础源码与维护测试 | 本地通过 43 项测试 |
| 文献与模型发现 | 校验 60 条文献；发现 15 个 CLI 模型入口 |
| 阅读路径 | Git 跟踪文件内的 Markdown 相对链接检查通过；外部 URL 和标题锚点不在该检查器范围内 |
| 发布附件 | 66 个数据分片、27 个出版附件和一份许可补充包与 API 名称、字节数及 SHA256 一致 |
| 冻结身份 | 原出版 ZIP 哈希和归档 rc.1 索引保持原样 |
| 许可补充包 | 索引原 ZIP 内的 1,315 个成员；确定性构建与包内成员校验通过 |

证据：[源码测试](../provenance/maintenance/source-checkout-20261020.json)、[维护测试](../provenance/maintenance/maintenance-tests-20261020.json)、[安装环境](../provenance/maintenance/fresh-environment-20261020.json)、[阅读路径](../provenance/maintenance/reader-links-20261020.json)、[附件元数据](../provenance/maintenance/release-assets-20261020.json)、[保留身份](../provenance/maintenance/preserved-identities-20261020.json)、[包内许可](../LICENSES/publication-companion/README.zh-CN.md)。

针对性的[公开内容检查](../provenance/maintenance/source-disclosure-20261020.json)在已检查的 UTF-8 源码和历史文本中未发现所配置的凭据或私钥签名。记录列明提交范围、文件数量及排除范围；二进制内容和外部证据归档未纳入该文本扫描。

记录准备情况时，托管 CI 矩阵仍在排队。请在 [GitHub Actions](https://github.com/HNNUYUXUAN/litz-wire-research/actions/workflows/ci.yml) 查看对应源码提交的结果；此处未将排队作业计作通过。

## 公开发布转换

仓库保持 Private，rc.1 和 rc.2 保持 Draft，数据目录仍使用认证访问。公开分发需完成[发布流程](release-preparation.zh-CN.md)中的可见性与 Release 转换、公开下载元数据更新及匿名下载验证。附件元数据核验不代表匿名访问已经通过。

本轮维护未执行物理求解或重建稿件。既有数值验收与待研究问题继续绑定各自的原始证据。
