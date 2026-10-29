# 研究目录接口

[English](agent-catalog.md) · [简体中文](agent-catalog.zh-CN.md)

使用[机器目录](agent-catalog.json)查找物理路线、研究工作流、已有自动化案例或完整稿件。[llms.txt](../llms.txt)提供简明导读，[llms-full.txt](../llms-full.txt)进一步列出已登记条目及阅读路径。

在仓库根目录执行检索，无需安装 Python 依赖包或启动求解器：

```bash
python tools/BuildAgentCatalog.py --search "common_terminal"
python tools/BuildAgentCatalog.py --search "解析"
python tools/BuildAgentCatalog.py --show case/aphi-diagnostics
python tools/BuildAgentCatalog.py --show manuscript/automation/zh-CN
```

工具仅使用 Python 标准库，需要 Python 3.11 及以上和 Git。查询按空白分词，要求每个词都出现在标识、标题、摘要、模型接口、引用 key 或保存的状态字段中，大小写等价。命中后返回完整 JSON 条目；未命中返回空列表和退出码 1。`--root PATH` 可指定其他工作副本，支持路径含空格。

## 稳定标识与登记来源

| 标识 | 登记依据 | 继续阅读 |
| --- | --- | --- |
| `route/<route>` | `configs/research_entries.json` | 双语文本与 CLI 教程、参数文件与实现 |
| `adapter/<route>` | `configs/research_entries.json` | Wolfram、ANSYS、GPU 文本与 CLI 入口 |
| `skill/<name>` | `automation/skills/*/SKILL.md` | 按需加载技能入口及参考资料 |
| `workflow/<directory>` | `automation/workflows/` 下成对的 README | 必要输入、操作步骤与完成标准 |
| `case/<case>` | `automation/examples/verification.json` 及各案例 `task.json` | 可见工具事件、执行记录与实际代码差异 |
| `manuscript/<edition>/<language>` | `docs/current-edition.json`、`publications/manifest.json` 与交付记录 | LaTeX 主稿、章节源文件、生成 Markdown 与输入身份 |

现有标识覆盖七条物理路线、三项适配器、九项 skills、五项工作流、六个已有案例和六份完整稿件。案例标题与状态标识保留已记录任务的原文；双语解释见[中文案例指南](../automation/examples/README.zh-CN.md)和[英文指南](../automation/examples/README.md)。

`reference_keys` 指向统一[题录](../references/library.bib)，实际使用关系见 [sources.json](../references/sources.json)。目录不维护第二份题录。章节源文件用于写作与构建，稿件入口指向完整阅读版。

## 文件身份与已有结果

每份受版本控制的资源包含仓库相对路径、阅读与原文件 URL、字节数和 SHA-256。`hash_basis: raw-bytes` 表示直接计算工作区文件原始字节的摘要，不转换换行或 Unicode。仓库的 `.gitattributes` 保留这些字节。URL 跟随 `main`；引用结果时应同时记录实际读取的提交和资源摘要。

生成器只读取 Git 登记的路径和明确登记的来源，不打开被忽略的 `outputs/` 或已恢复的 `data/evidence/` 产物，也不执行计算、下载 Release 或探测本机许可证。`input_resources` 用精确摘要绑定实际读取的文件。输出不写入构建时间或当前 Git HEAD，相同输入字节对应相同输出。

`recorded_runs` 分别保留已有执行和物理验收状态。稿件条目的 `resources` 指向 LaTeX 主稿与生成阅读稿，`chapter_sources` 与 `input_hashes` 记录章节及全部构建输入。历史发布附件通过 `historical_releases` 连接到保留版本身份的附件页。

## 更新与检查

```bash
python tools/BuildAgentCatalog.py
python tools/BuildAgentCatalog.py --check
```

构建写入 `docs/agent-catalog.json`、`llms.txt` 和 `llms-full.txt`。`--check` 不写文件；发现生成内容过期或缺失时返回 1，并列出对应路径。登记无效、受版本控制的输入缺失或稿件预览摘要不符时返回 2。先修改登记源或源文档，再生成目录，并在同一提交中纳入生成文件。

需要在独立目录检查时使用 `--output-dir PATH`，随后可对同一目录执行 `--check`。检索与准确标识查询始终只读。本接口参考的仓库构建方法记录在[来源比较清单](../provenance/maintenance/repository-patterns.json)中。
