# 研究数据集

[English](datasets.md)

在 Python 3.11 或后续版本的虚拟环境中，从仓库根目录安装 CLI：

```powershell
python -m pip install -e .
```

通过 CLI 选择所需路线，依赖会一并恢复。还原后核对文件身份：

```powershell
litz-research data list
litz-research data fetch publication-inputs
litz-research data verify publication-inputs
```

## 下载与身份验证

本目录设置为 `private: false`，已发布的公开附件可直接下载，无需 GitHub CLI 或登录。

公开模式优先使用分片的 `public_url`。恢复器核对其与 `repository`、数据集的 `source_version`（缺省时使用目录的 `tag`）及附件文件名完全对应，URL 使用 `https://github.com/<repository>/releases/download/<version>/<name>`，文件名按 URL 编码。未提供 `public_url` 的旧目录继续使用 `url`，不附带身份凭据。

私有历史目录保留 `private: true`，始终使用分片的 API `url` 并忽略 `public_url`。凭据仅用于 HTTPS 的 `api.github.com` 请求，跨主机跳转时移除。公开发布要求附件所属的 Release 已发布；仅将仓库设为公开不会使 Draft 附件可下载。

| 数据集 | 文件映射 | 压缩 MiB | 内容 |
| --- | ---: | ---: | --- |
| `academic-editions` | 665 | 337.48 | 历史双语报告、论文、Notebook、PDF、图件及文档验收记录 |
| `analytic` | 874 | 1.38 | 圆线 Bessel 校准、径向电流和解析验收 |
| `ansys` | 1,980 | 4.28 | Maxwell 输入、工程、接口探针、网格限制和验证记录 |
| `aphi` | 2,057 | 3200.49 | 三维 A–φ 保存场、校准诊断及求解边界 |
| `common-terminal` | 1,401 | 693.62 | 共同端电压场路模型、逐股复电流及受控回流 |
| `fem2` | 470 | 6.28 | 二维有限元校准、网格、场和敏感性检查 |
| `geometry` | 1,155 | 94.24 | 股线身份、中心线、弧长、铜体积及几何检查 |
| `gpu` | 4,746 | 301.36 | CPU/GPU 矩阵和复电流比较、资源与退出状态 |
| `peec` | 3,289 | 989.54 | 有限长度纵向 PEEC 输入、解及长度和积分敏感性 |
| `publication-inputs` | 311 | 46.57 | 成稿使用的独立面板、绘图数据和观测量 |
| `research-records` | 11,389 | 929.57 | 跨路线运行记录、验证摘要和保存源码 |
| `research-shared` | 0 | 125.87 | 由路线依赖恢复的去重共享内容对象 |
| `rt0` | 3,613 | 522.57 | 外场 RT0 解、面通量重构、空间收敛和算子检查 |
| `automation-rc2` | 10,569 | 14.70 | 自动化源码快照、可见工具事件、原生求解、任务恢复及 Notebook 记录 |

## 数据身份与离线恢复

`data/catalog.json` 定义分片顺序、依赖、对象与文件 SHA256。表中压缩体积为各数据集自身分片大小，共享依赖会增加首次下载量。每个分片至多 128 MiB。历史科学记录恢复到 `data/evidence/v1.0.0-rc.1/`，自动化记录恢复到 `data/evidence/v1.0.0-rc.2/`，并保留原相对路径。新运行写入 `outputs/`。

```powershell
litz-research data fetch publication-inputs --offline --cache "C:/Research Cache"
```

恢复器检查分片、归档成员、对象与最终文件；现有文件通过哈希核验后复用。损坏对象保留明确诊断。外场损耗、输运电阻、几何量及三维诊断使用各自模型定义。当前本地稿件见[学术文件](../publications/README.zh-CN.md)，历史成稿由 `academic-editions` 定位。
