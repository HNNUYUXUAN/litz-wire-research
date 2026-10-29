# 本地工作区维护

日常工作区为 `litz-wire-research-opensource`。历史资料位于被 Git 忽略的 `.local-archive/`；其中 `workspaces/` 保存旧工作区，`snapshots/` 保存阶段归档，`maintenance/` 保存逐批清单及验收记录。本地原题、文献、私有历史和配置按原有权利记录保存。

## 盘点与执行

从项目根目录调用当前 Python 环境。批次目录必须唯一；同一批次在来源身份一致时可续作。

```powershell
$batch = '.local-archive/maintenance/consolidate_20261026_01'
.conda/project/python.exe -B tools/MaintainWorkspaces.py status --batch $batch
.conda/project/python.exe -B tools/MaintainWorkspaces.py inventory --batch $batch
.conda/project/python.exe -B tools/MaintainWorkspaces.py audit-git-temp --batch $batch
.conda/project/python.exe -B tools/MaintainWorkspaces.py plan --batch $batch
.conda/project/python.exe -B tools/MaintainWorkspaces.py apply --batch $batch
```

最后一条只预览。核对 `plan.json`、`duplicate-trees.json` 和 `git-temp-audit.json` 后，显式添加 `--execute` 才执行复制及删除。默认来源限定为本次四个工作区及五个归档；其他目录使用 `--spec` 指定 JSON 来源清单，不自动扩大扫描范围。

执行按原文件身份检查、复制、目标哈希核验、Git/LFS 核验、来源集合核验、来源删除的顺序进行。遇到源文件变化、新增文件、目标内容冲突或外部写入进程时停止，保留来源与已复制文件。中断后重跑同一 `apply --execute`；丢失或改变的来源不能通过重新生成同批清单掩盖。修订来源时另建关联批次。

`inventory.sqlite` 保存全部文件的 SHA256、大小、时间、类型、原位置、处理动作和状态；`events` 表保存操作记录。`path-map.jsonl` 保存验收后的逐文件保留位置。维护记录本身不纳入自身循环哈希。

## 查找和恢复历史资料

完整重复目录只保留一个展开副本。使用原路径查找现位置：

```powershell
.conda/project/python.exe -B tools/MaintainWorkspaces.py locate --batch $batch --source 'C:/Workspaces/repos/litz-wire-modeling-src/README.md'
```

历史 Git 目录中的 `.git` 路径分量保存为 `git-metadata`。其对象、引用、reflog、原索引状态和 LFS 实体随对应工作区保留。原始缺失索引也保留为缺失状态。

需要独立恢复一个历史工作区时，指定全新目录：

```powershell
.conda/project/python.exe -B tools/MaintainWorkspaces.py restore --batch $batch --root-id litz-wire-modeling-src --destination 'C:/Research Restore/Private Stage'
.conda/project/python.exe -B tools/MaintainWorkspaces.py restore --batch $batch --root-id litz-wire-modeling-src --destination 'C:/Research Restore/Private Stage' --execute
```

恢复会按原路径重新复制全部保留文件及被去重目录，复原 `.git` 名称，并核验文件哈希。运行环境缓存需要重新建立。旧链接保存为相邻的 `.link-record.json`，包含目标和原类型属性；恢复时也保留为记录，需使用时先核实目标再重建链接。迁移和清理均不遍历这些链接。

## 缓存与证据

Python 字节码、旧虚拟环境、Node 依赖及普通编译缓存由源码和锁文件重建。当前虚拟环境保留；重建 Python 环境的方法见 README 与 `docs/development.md`。历史 Web 展示目录使用其 `package.json` 和锁文件安装依赖，再按原有脚本构建。

`outputs/`、Notebook、WXF、求解工程、检查点、日志和失败记录按证据处理。忽略规则、目录名称或可重新计算均不构成删除依据。Git 临时 pack 只有在与完整保留对象重新编码后的前缀逐字节一致时才作为缓存清理；未匹配文件保留，详见批次报告。

验收命令：

```powershell
.conda/project/python.exe -B tools/MaintainWorkspaces.py verify --batch $batch
.conda/project/python.exe -B tools/MaintainWorkspaces.py verify-git --batch $batch
.conda/project/python.exe -B tools/CheckSourceCheckout.py
.conda/project/python.exe -B -m litz_research.cli data verify
```

实际迁移数量、保留疑点、数据集及正式成稿检查结果、磁盘空间变化，以批次目录中的最终报告为准。归档字节完整性与原模型物理验收分别记录。
