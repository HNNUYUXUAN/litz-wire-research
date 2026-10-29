# RT0 矩阵自由 CPU FFT 入口

`VoxelOperator.wl` 先加载 `VoxelPEEC.wl`，复用其体积分与 24 扇区 Duffy 自项。原模型及历史输出未改变。CPU `Fourier/InverseFourier` 固定 `FourierParameters->{1,-1}`；12 个局部 RT0 核使用零填充 Toeplitz 嵌入，保留全空间远互感，无距离软化。

## 运行与来源

在已有阶段运行器允许 `voxel_operator` 后运行：

```powershell
$env:LITZ_VOXEL_OPERATOR_MODE = 'pilot'
./src/RunNotebookStage.ps1 -Stage voxel_operator -RunId unique_operator_pilot
```

模式 `pilot` 顺序运行 32/128 cells；`equivalence` 添加 1024 cells；`scale` 在前三档同原始致密矩阵/求解独立等价通过后继续 3456/8192 cells。每档分别保存核组装、GMRES 真残差与阶段检查点。原始致密参考本身先做主存预算检查，不能把同一新算子的致密化当成独立参考。

32 cells 只用于代数验证，尺寸为 1×1×4 mm；128 cells 起的空间系列为同一个 1×1×2 mm 长方体。阶段使用均匀 1 mT RMS Bz 和零净输运，损耗不能解释为内禀 `P/I²` 电阻。空间变化 1% 与算法等价、守恒分别验收。

13 项小模型回归入口：

```wolfram
stageRoot = DirectoryName[DirectoryName[absolutePathToVoxelOperatorWLT]];
TestReport[FileNameJoin[{stageRoot,"tests","VoxelOperator.wlt"}]]
```

修改后须由新内核执行；仅 `SyntaxQ=True` 不能称物理测试通过。

## 最小接口

```wolfram
op = LitzVoxelOperator`CreateOperator[{4,4,8},.00025,200000.,10,"transport"];
sol = LitzVoxelOperator`SolveOperator[op];
metadata = LitzVoxelOperator`OperatorMetadata[op];
```

`CreateOperator` 选项为 `ActiveCells`、`ConductorLabels`、`MemoryBudgetBytes`、`TimeBudgetSeconds`、`ProgressFunction`。`ActiveCells` 是规则网格中的整数 cell 坐标列表，标签按同一顺序指定。仅同标签且共享面的 cell 可以交换通量；其余侧面绝缘。每个连通导体域必须抵达全局底面和顶面，否则返回 `UnportedComponent` 或 `NoFluxFaces`，不会静默丢掉孤立体素。所有底端面共享同一个未知电势，顶端面共接电势参考；各标签的实际端口复电流在 `source_conductor_currents_RMS_A` 中保存，不施加 I/N。

`SolveOperator` 默认重启 40、最多 800 次，目标真相对残差 10^-8、时间上限 600 秒；可设 `Tolerance`、`TotalCurrentRMSA`、`TimeBudgetSeconds` 与 `CheckpointFunction`。预条件器为 `diag(R+jωL)` 配合稀疏 `C D^-1 C^T` Schur 因子化。GMRES、体电流/端口约束与功率残差独立保存；时间不足或迭代耗尽给出失败及 `stop_reason`，不产生通过声明。

`DenseReference` 只允许总自由度 ≤600 的诊断性致密化；它不替代旧 `FaceFluxModel` 独立组装。`OperatorMetadata` 可归档几何和参数，省去 FFT 数组与稀疏工作矩阵。

## 尚需独立验收

本接口没有自动完成积分阶数 10/14/18 的敏感性、曲线体素化、圆截面和阶梯边界收敛、真实回流/端接、独立三维 FEM 比较或结构排名。当前实现没有 GPU 优化，不调用已失败的 `GPUArray` 复数 Fourier。已有 CUDALink/cuFFT 仅在后续独立验证后使用。
