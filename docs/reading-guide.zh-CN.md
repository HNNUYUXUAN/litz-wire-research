# 阅读与首次运行

[English](reading-guide.md) · [返回首页](../README.zh-CN.md) · [合并稿与章节目录](editions.md)

## 选择阅读方式

| 目的 | 操作 | 所需环境 |
| --- | --- | --- |
| 了解研究问题和主要结果 | 从首页打开中文或英文综合论文的 Markdown | GitHub 仓库访问权限 |
| 阅读完整图文与分页版式 | 恢复 `academic-editions`，打开单栏 PDF | Python、GitHub CLI、PDF 阅读器 |
| 查看原生三维图形 | 恢复同一数据集，打开对应 `.nb` | 可读取 Notebook 的 Wolfram 前端 |
| 验算孤立圆线解析解 | 运行下方轻量示例 | Python 3.11+、mpmath |
| 理解模型实现或重建文档 | 按[开发说明](development.zh-CN.md)选择路线 | 对应路线的求解器或文档工具 |

GitHub 上的 Markdown 提供正文、公式和表格，图件由版本附件分发。完整阅读优先使用恢复后的 PDF；Notebook 提供同一正文与原生图形。章节稿的数字、图表和文献编号继承所属合并稿。

## 阅读 PDF 与 Notebook

历史成稿来源版为 `v1.0.0-rc.1`，附件保存在[私有草稿 Release](https://github.com/HNNUYUXUAN/litz-wire-research/releases/tag/untagged-f71ee4e060c0e39537cb)。使用有权访问该私有仓库及草稿版本的 GitHub CLI 身份；`gh auth status` 可检查已登录账户。首次使用可运行 `gh auth login` 完成登录。

在 Windows PowerShell 中，从希望存放项目的目录运行：

```powershell
gh repo clone HNNUYUXUAN/litz-wire-research
cd litz-wire-research
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\litz-research.exe data fetch academic-editions
.\.venv\Scripts\litz-research.exe data verify academic-editions
```

已有仓库时，从仓库根目录执行安装及数据命令即可。下载器按清单获取分片、复用已校验缓存并恢复相对路径。`academic-editions` 连同共享依赖约需下载 **463.4 MiB**；具体文件和大小见[数据集目录](datasets.md)。校验结果应包含 `status: passed`。下载、解包和校验的耗时取决于网络及磁盘速度。

恢复后可直接打开中文单栏论文：

```powershell
Start-Process -FilePath '.\outputs\publication_rc1_20261007_01\documents\paper\zh-CN\paper_zh-CN_single.pdf'
```

其余合并稿的位置如下，路径均相对于本地仓库：

| 稿件 | 单栏 PDF |
| --- | --- |
| 中文研究报告 | `outputs/publication_rc1_20261007_01/documents/report/zh-CN/report_zh-CN_single.pdf` |
| 英文综合论文 | `outputs/publication_rc1_20261007_01/documents/paper/en/paper_en_single.pdf` |
| 英文研究报告 | `outputs/publication_rc1_20261007_01/documents/report/en/report_en_single.pdf` |

双栏版使用同目录的 `_ieee.pdf`。中文论文 Notebook 为 `notebooks/publication/publication_rc1_20261007_01/paper/zh-CN/paper_zh-CN.nb`；可在 Wolfram 前端通过“打开”选择文件。其余 Notebook 和章节稿路径见[完整目录](editions.md)。已保存的正文、图表和三维图形可直接阅读。

离线恢复使用包含分片与对象的完整缓存目录。在下例中，用自己的缓存路径替换引号中的目录：

```powershell
.\.venv\Scripts\litz-research.exe data fetch academic-editions --offline --cache 'D:\Research Cache\litz'
```

## 运行解析示例

完成上述基础安装后，从仓库根目录运行：

```powershell
.\.venv\Scripts\litz-research.exe run analytic
```

每次执行使用独立运行号。返回结果中的 `run_id` 对应 `outputs/<run_id>/`，其中 `results.json` 保存工况、计算值、误差与十二项检查；`radial_current_density.csv` 保存半径及复电流密度实部、虚部。CSV 的半径单位为 m，电流密度单位为 A/m²。

| 参考量 | 预期数值 | 含义 |
| --- | ---: | --- |
| `Q1_Rac_mohm_per_m` | 20.01620363 | 单位长度交流内电阻，mΩ/m |
| `Q1_P_W_per_m` | 8.00648145 | 20 A RMS 下单位长度焦耳损耗，W/m |
| `Q1_Jdc_A_per_mm2` | 6.36619772 | 直径 2 mm 圆线的平均直流电流密度，A/mm² |

该示例采用 200 kHz、20 ℃、电导率 58 MS/m 的孤立直圆线模型。十二项检查核验解析关系、积分和物理约定；其中 Q1 电流密度检查确认原题 2 mm 圆线超过 4 A/mm² 约束这一事实。检查通过的含义见[验收标准](../tests/ACCEPTANCE.md)。

Linux/macOS 的基础安装与示例命令为：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/litz-research run analytic
```

Python 解析示例和数据恢复使用跨平台 Python。保留的科学求解运行器和成稿前端流程使用 Windows 环境，具体依赖见[开发说明](development.zh-CN.md)。

## 遇到问题时

| 现象 | 下一步 |
| --- | --- |
| Release 返回访问错误 | 执行 `gh auth status`，核对登录身份和仓库权限 |
| 本地缺少 PDF、图件或 Notebook | 执行 `data fetch academic-editions`，随后运行 `data verify academic-editions` |
| 校验报告哈希错误 | 保留报错路径与数据集身份，按[开发说明](development.zh-CN.md)检查缓存和恢复记录 |
| Wolfram 或 LaTeX 工具不可用 | PDF 阅读和 Python 解析入口可先使用；相应构建环境按 `doctor` 报告配置 |

图件重建与学术文件编译由[开发说明](development.zh-CN.md)介绍。数据身份、原始来源和模型状态见[数据集](datasets.md)及[来源记录](../provenance/README.md)。
