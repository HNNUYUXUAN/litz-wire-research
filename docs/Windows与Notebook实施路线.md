# Windows 科研运行

[English](windows-notebooks.md)

先按 [Conda 环境说明](../automation/environments/README.md)重建环境，再运行 `litz-research doctor`。当前桌面与执行宿主实测为 Windows Server 2022，使用 Wolfram 15.0 与 AEDT Student 2025.2；Windows 10 为待验证目标。

[模型指南](../README.zh-CN.md)提供保存参数与 CLI 命令。Python 和 Wolfram 分别执行解析校准。长任务使用 `jobs submit/status/cancel/resume`，记录输入身份、八个逻辑处理器、24 GiB 任务内存、8 GiB 系统余量及所属进程清理状态。

[六份 LaTeX 主稿](../manuscript/README.md)经 Pandoc 3.13 生成 Markdown 阅读稿。[出版说明](editions.zh-CN.md)给出编译与逐页检查步骤。使用新运行编号执行 `litz-research build --run-id publication_local_01 --stage all`。

通过 `data list`、`data fetch` 和 `data verify` 选择、恢复与核验历史科研数据。文件及归档哈希保持原始证据身份。
