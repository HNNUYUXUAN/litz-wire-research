# Matrix-free RT0 CPU FFT interface

[简体中文](VoxelOperator_README.zh-CN.md)

`VoxelOperator.wl` loads `VoxelPEEC.wl` and reuses its volume integration and 24-sector Duffy self term. CPU `Fourier/InverseFourier` uses `FourierParameters->{1,-1}`. Twelve local RT0 kernels use zero-padded Toeplitz embedding, retaining long-range mutual inductance without distance softening.

## Execution and evidence

Run through the stage supervisor with the `voxel_operator` stage enabled:

```powershell
$env:LITZ_VOXEL_OPERATOR_MODE = 'pilot'
./src/RunNotebookStage.ps1 -Stage voxel_operator -RunId unique_operator_pilot
```

`pilot` runs 32 and 128 cells sequentially; `equivalence` adds 1024 cells. `scale` continues to 3456 and 8192 cells after the first three levels pass independent equivalence against the original dense assembly and solution. Each level retains kernel assembly, GMRES true residuals and checkpoints. The original dense reference undergoes a memory preflight; densifying the new operator is a separate diagnostic.

The 32-cell algebraic case measures 1×1×4 mm. The spatial series from 128 cells onward uses the same 1×1×2 mm cuboid, a uniform 1 mT RMS Bz and zero net transport. Report imposed-field absorption for this excitation. The 1% spatial-change target, algebraic equivalence and conservation have separate checks.

The thirteen small-model regressions run with:

```wolfram
stageRoot = DirectoryName[DirectoryName[absolutePathToVoxelOperatorWLT]];
TestReport[FileNameJoin[{stageRoot,"tests","VoxelOperator.wlt"}]]
```

Execute changes in a fresh kernel. Physical acceptance requires the regression outputs in addition to syntax checks.

## Interface

```wolfram
op = LitzVoxelOperator`CreateOperator[{4,4,8},.00025,200000.,10,"transport"];
sol = LitzVoxelOperator`SolveOperator[op];
metadata = LitzVoxelOperator`OperatorMetadata[op];
```

`CreateOperator` accepts `ActiveCells`, `ConductorLabels`, `MemoryBudgetBytes`, `TimeBudgetSeconds` and `ProgressFunction`. Active cells are integer coordinates on a regular grid; labels follow their order. Flux passes only across shared faces of cells with the same label. Other side faces are insulating. Every connected conductor must reach the global bottom and top; otherwise the interface returns `UnportedComponent` or `NoFluxFaces`. Bottom faces share an unknown potential and top faces share the reference potential. Actual complex port currents are recorded in `source_conductor_currents_RMS_A`.

`SolveOperator` defaults to restart 40, at most 800 iterations, a true relative residual target of 10⁻⁸ and a 600-second time limit. Options include `Tolerance`, `TotalCurrentRMSA`, `TimeBudgetSeconds` and `CheckpointFunction`. The preconditioner combines `diag(R+jωL)` with sparse `C D^-1 C^T` Schur factorization. GMRES, volume-current/port constraints and power residuals are saved independently. Time or iteration exhaustion records failure and `stop_reason`.

`DenseReference` supports diagnostic densification only up to 600 total degrees of freedom. The original `FaceFluxModel` supplies independent assembly. `OperatorMetadata` archives geometry and parameters while omitting FFT arrays and sparse working matrices.

## Further validation

Integral-order sensitivity at 10/14/18, curved voxelization, circular-section and staircase-boundary convergence, actual returns and terminations, independent three-dimensional FEM comparisons and structural rankings require additional studies. This interface uses CPU execution. The recorded CUDALink/cuFFT route requires its own validation before integration; the failed complex `GPUArray` Fourier route remains documented in historical diagnostics.
