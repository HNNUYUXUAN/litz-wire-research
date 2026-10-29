# 当前设备整合验收报告

验收日期：2026-10-28。当前单仓交付包含科研调研技能、Conda 运行环境、官方 MCP 集成、Student edition 上游补丁、三份双语作品及文本/CLI 研究入口。逐项状态见[任务账本](../automation/integration-plan.json)，可复核摘要见[综合验收回执](../provenance/research-integration/final-acceptance.json)。

## 使用入口

| 工作 | 入口 |
| --- | --- |
| 阅读六份稿件、编辑 LaTeX 主稿 | [稿件目录](../publications/README.zh-CN.md) · [主稿清单](../manuscript/latex-publication.json) |
| 调研、获取论文、评估复用、交接建模任务 | [科研工作流与脚本](../automation/research/README.md) · [四项技能](../automation/skills) |
| 重建和核对运行环境 | [Conda 环境说明](../automation/environments/README.md) · [锁文件](../automation/environments/locks) |
| 配置与验证 MCP | [Codex 接入](../automation/harnesses/codex/README.zh-CN.md) · [官方上游锁](../automation/mcp/upstreams.lock.json) |
| 执行研究任务 | [模型目录](agent-catalog.zh-CN.md) · [20 个文本入口映射](research-entry-migration.json) |

## 环境与实际执行

桌面进程和执行进程观测到同一 Windows Server 2022 Datacenter 21H2、build 20348.4405 主机；Codex、Chrome 和 Explorer 位于桌面会话 1。Windows 10 是用户指定的目标平台，本轮没有观测到 Windows 10 执行宿主。远程访问客户端的系统身份尚无证据，因此当前公开支持范围绑定到实际测试主机。Windows 10、Windows 11 实机验证继续作为目标平台发布门槛。

三个 Conda 环境均按锁在新前缀重建并完成包清单、依赖和版本核验：项目环境 Python 3.12.16、Pandoc 3.13；ANSYS 环境 Python 3.12.16、PyAEDT 1.8.0、官方 MCP 0.2.dev0 固定提交；检索环境 Python 3.12.16、Node.js 24.22.1。当前项目及 Codex MCP 配置已经切换，原配置保存在本地备份。Conda 不接受含空格的环境前缀，其失败记录被保留；中文和空格目录中的稿件源码包另行完成了重建验证。

原生客户端完成 Wolfram 15.0.0 工具调用、12 项测试，以及 AEDT Student 2025 R2 / 2025.2.4 会话连接和身份核验。小型 Maxwell 七股输运案例完成求解，复电流约束相对误差为 5.58818×10⁻¹⁵，功率核对相对误差为 3.94158×10⁻¹⁵；这是单次网格的端口与功率验收，空间与边界收敛仍待研究。退役旧环境后，解析案例再次完成全部 12 项物理检查。

运行策略继续限制八个逻辑处理器、24 GiB 任务内存和至少 8 GiB 系统余量。任务取消、超时、输入身份和 PID 创建身份由回归测试与既有实际生命周期记录覆盖；本轮原生会话的关闭回执确认任务进程已退出。[运行验收摘要](../provenance/research-integration/runtime-validation.json)分别记录连接、工具执行、求解、物理检查和清理。

两套项目专用旧环境已在检查配置引用与运行进程后迁入本地冻结档案，共 33,802 个文件逐项核验；当前运行入口使用 Conda。[环境退役回执](../provenance/research-integration/environment-retirement.json)保留数量及档案身份。

## 科研 skills 与来源复用

四项技能已具备发现入口、安装脚本和确定性处理入口，并接到既有复现、扩展、比较、诊断及报告工作流。广域检索采用已安装的元宝能力；后续通过论文原始页面、学术接口及代码仓库核对具体信息。

本轮实际完成中英文主题检索、精确 DOI 查询、重复归组、冲突元数据保留、来源参数检查、开放全文获取、授权 WebVPN 获取及建模交接。C01 论文的出版商开放 PDF 与授权机构 PDF 均核验为六页，题名和 DOI 匹配，分别保存哈希；ZHU2026 的开放接受稿核验为十三页。C01 的再分发权保持未知，全文留在本地资料区。Crossref 未命中、论坛服务不可访问、浏览器验证阻塞等过程保留各自状态；没有从访问失败推断内容。CLI 研究交接完成解析校准的 12 项检查。

[在线验收摘要](../provenance/research-integration/online-validation.json)记录实际论文身份；[平台核查表](../automation/research/platform-review.md)区分采用的实现与仅评估的候选。采用的 academic-search 七个文件固定到提交 `b9b692ed1334c858eb42d1f2710ccfcae1a43eb8`，保持上游字节、MIT 许可及署名。K-Dense、DeepAgents、Gitee MindScience 和 FEMM 文档各自按原始来源记录用途。引文适配层沿用 C01、ZHU2026 等现有键，输出确定性 BibTeX 并保留字段来源与冲突。

同一 DOI 的三组成对检索阶段实验采用相同解释器、校验器和权限，交替安排实时查询与已核验缓存复用：六次均满足 DOI、题名、作者和日期核对；中位耗时分别为 1.101912 秒和 0.000344 秒，网络调用分别为一次和零次。两组均未调用模型，可观测 tokens 保持缺失。该实验测量确定性检索阶段，排除缓存建立和人工核验成本；不能用于推断整轮智能体调研的时间或 token 收益。完整任务层面的配对评测继续用于后续独立发布判断。[实验条件与原始测量摘要](../provenance/research-integration/retrieval-stage-comparison.json)

## 上游贡献

ANSYS Student 参数修复已提交 [PyAEDT-MCP PR #155](https://github.com/ansys/pyaedt-mcp/pull/155)，覆盖启动、连接与服务自动启动，保留标准版默认值。补丁相对上游基线的九个新增回归用例先失败后通过；相关测试共 141 项通过，Ruff 检查通过。独立 Python 3.13.18、PyAEDT 1.9.0 环境完成本机 Student 启动、连接、自动连接和进程关闭验证。

最终回读确认目标 `main`、补丁提交 `1be069a960da7a8ea2d567ef39728edc59664138`、五个改动文件、126 行增加和两行删除。PR 当前开放待上游审查；检查接口未返回 CI 检查或状态。上游合并及发布时间由维护者决定，当前锁定版本继续保留项目适配。[贡献记录](../automation/mcp/contributions/student-edition.json) · [最终 PR 回读](../provenance/research-integration/upstream-pr.json)

## 稿件与研究入口

六份 LaTeX 主稿及 64 个章节源完成迁移，正文、前置内容和图注由 LaTeX 维护；Markdown 由固定 Pandoc 3.13 和项目适配层生成。完整报告采用单栏，两篇论文采用 IEEE journal。指标来自同一份已核验映射；现有 A–φ 未通过状态、Maxwell 收敛缺口和各模型适用范围继续保留。

最终构建为 `latex_delivery_20261028_07`。报告中文/英文分别 30/33 页，物理论文 13/15 页，自动化论文 5/6 页，共 102 页。六份独立编译完成，全部页面有视觉检查记录；原始 540 个正文块完成对应核对，原档案及当前 TeX 的哈希再次验证。Markdown 重复生成一致。源码 ZIP 在中文及空格目录中解包后重新编译，102 页渲染像素与审阅版本一致。

[编译](../provenance/current-publication/compilation.json) · [阅读稿](../provenance/current-publication/reading-receipt.json) · [逐页审阅](../provenance/current-publication/visual-review.json) · [文本迁移](../provenance/current-publication/migration-text-audit.json) · [独立源码包](../provenance/current-publication/package-portability.json)

20 个研究入口已迁为双语文本教程、参数文件和现有 `run/jobs` CLI。七条模型路线的算法与证据保留，包含实际科学计算或任务管理功能的模块继续使用。默认出版流程、模型目录、代理目录、打包和 CI 契约已经更新。

## 清理与公开材料

共 215 个旧维护文件完成逐项归档、哈希核对和移除：27 个研究 Notebook 包装及辅助文件、172 个出版维护链文件、16 个实际磁盘中的论文 Notebook。两份原本地导航另行保存完整字节后更新了当前入口，[导航迁移回执](navigation-migration-receipt.json)保留其身份。原始求解资料、失败记录和独立修改继续保存；旧环境另行归档。当前维护目录不含 Notebook、Word 或演示文稿。PDF 作为本地编译和预览产物保留；必要图件、BibTeX、类文件和数据随源码维护。

[保留位置与哈希复核](../provenance/research-integration/retention-validation.json) · [研究入口清理](text-entry-cleanup-receipt.json) · [出版维护链清理](publication-chain-cleanup-receipt.json) · [磁盘清理](publication-disk-cleanup-receipt.json)

许可核查覆盖本次实际分发的来源：项目代码 MIT，原创论文与图件 CC BY 4.0，academic-search 原始 MIT，AgentTools MIT 声明，PyAEDT-MCP Apache-2.0 声明，以及四份字节一致的 IEEEtran 类及 LPPL 文本。元宝通过已安装能力调用。第三方全文、软件及字体按各自权利记录处理。[第三方声明](../THIRD_PARTY_NOTICES.zh-CN.md)与[公开材料审查回执](../provenance/research-integration/public-review.json)记录检查范围；模式扫描命中的两处模拟会话参数均位于拒绝凭据的测试用例。

## 验证汇总与后续门槛

| 检查 | 结果 |
| --- | --- |
| 项目 Python 回归 | 228 项运行，227 项通过、1 项因隔离环境依赖跳过 |
| ANSYS 独立环境回归 | 10 项通过，覆盖项目环境中跳过的 ANSYS 依赖检查 |
| 纯源码检查 | 35 项通过；来源与文献记录通过 |
| academic-search Node 测试 | 71 项通过、2 项跳过、0 项失败 |
| ANSYS 上游修复相关测试 | 141 项通过；九项新增用例在原上游基线失败 |
| 主稿与阅读稿 | 六份编译、102 页审阅、重复生成和源码包重建通过 |
| 保留映射 | 215 个移除文件、540 个原正文块、七个复用文件、四份类文件通过哈希核对 |
| 目录与链接 | 出版索引、代理目录及当前阅读入口检查通过 |

GitHub Actions 配置已更新；本轮结果来自本机执行，当前工作区版本尚未以项目提交触发远端 CI。该工作区交付和上游 PR 是本轮成果。Windows 目标平台实测、跨领域任务验证、完整智能体调研收益评测及独立拆仓按后续发布门槛推进。
