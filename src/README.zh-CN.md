# 科学模块与兼容入口

可安装入口为 `litz-research`，使用方法见[开发说明](../docs/development.zh-CN.md)。本目录保留既有调用路径，维护实现按职责分布于 `models/`、`adapters/`、`shared/` 和 `tools/publication/`。

| 模块 | 职责 |
| --- | --- |
| Q1Analytical.wl | 圆线 Bessel 阻抗、复电流及独立面积积分 |
| NotebookPhysics.wl | 解析、圆盘 FEM、场路与轨迹模型 |
| CoaxFEM.wl | 受控回流几何下的稀疏多股场解 |
| PEEC.wl | 有限长度纵向部分元件模型 |
| VoxelPEEC.wl、VoxelOperator.wl | 体素通量表示与矩阵自由 RT0 算子 |
| GPUValidation.wl 及相关内核 | 设备数值运算与 CPU/GPU 等价检查 |
| ansys_validate.py、ansys_native3d.py | Maxwell 适配与独立验收 |
| RunNotebookStage.ps1 / .wls | 资源监督、唯一运行号与源码快照 |
| PublicationManuscripts.py | 共用 Markdown 解析及多格式学术稿件 |
| BuildPublicationDocuments.wls | Notebook 前端构建、渲染与视角回读 |

`RunCalibration.wls` 提供独立的干净内核解析入口。科学产物记录模型、输入、适用范围、执行状态和物理验收。成稿构建读取共用清单与保存的科学量值。

[English](README.md)
