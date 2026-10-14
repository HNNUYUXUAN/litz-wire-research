# 运行模型并解释结果

[English](tool-workflows.md)

从孤立圆线解析案例开始。它依赖 Python 和 mpmath，通过独立积分检查内部阻抗、复电流与 RMS 功率。

```powershell
litz-research models
litz-research doctor
litz-research run analytic --case tutorial --run-id analytic_example_01 --dry-run
litz-research run analytic --case tutorial --run-id analytic_example_01
```

预检显示输入、启动条件和目标目录。实际执行写入 `outputs/analytic_example_01/`，重复运行号会返回诊断。阅读 `results.json` 中的 `source_model`、`execution_status`、`physical_acceptance_status`、量值和检查。2 mm、200 kHz、20 A RMS 案例给出约 20.0162 mΩ/m 和 8.00648 W/m；平均直流电流密度为 6.3662 A/mm²，用于 Q1 解析校准。

## 选择科学路线

`litz-research models <model>` 显示支持案例、工作量、源码和数据集。[模型索引](method-evidence-map.zh-CN.md)连接解析、FEM、共端、几何、PEEC、RT0 和 A–φ 实现及其测试。执行完整研究前阅读对应路线说明。Ansys 和 GPU 适配具有各自的运行环境及许可条件。

## 长任务

```powershell
litz-research jobs submit peec --case tutorial --run-id peec_job_01
litz-research jobs status peec_job_01
litz-research jobs cancel peec_job_01
litz-research jobs resume peec_job_01 --new-run-id peec_job_02
```

客户端超时后先查询状态。取消操作限定于任务所属进程。教程接续核对保存输入和源码后建立关联的新运行；检查点恢复按各路线实际能力执行。解释结果前同时阅读执行状态和物理验收。

## 诊断与研究接续

`doctor` 返回可执行文件、版本命令、Python 导入、字体及资源检查。`doctor --kernel` 另启动有时间限制的 Wolfram 算术与版本探针。检查完成表示报告已生成，各项能力分别有其实际结果。连接、API、求解器、资源及物理失败分别保存证据。

按任务选择[自动化工作流](../automation/README.zh-CN.md)，完成复现、扩展、比较、诊断或成稿。正式运行前保存修改，保留原失败，修订输入使用新的运行号。
