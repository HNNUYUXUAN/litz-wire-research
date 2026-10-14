# Scientific modules and compatibility entry points

The installed entry point is `litz-research`; see [Development](../docs/development.md). This directory preserves existing invocation paths. Maintained implementations reside in `models/`, `adapters/`, `shared/` and `tools/publication/`.

| Module | Responsibility |
| --- | --- |
| Q1Analytical.wl | Round-wire Bessel impedance, complex current and independent area integrals |
| NotebookPhysics.wl | Analytical, disk FEM, circuit-field and trajectory models |
| CoaxFEM.wl | Sparse multistrand field solutions with a controlled return |
| PEEC.wl | Finite-length longitudinal partial elements |
| VoxelPEEC.wl, VoxelOperator.wl | Voxel flux representation and matrix-free RT0 operators |
| GPUValidation.wl and associated kernels | Device arithmetic and CPU/GPU equivalence checks |
| ansys_validate.py, ansys_native3d.py | Maxwell adapters and independent acceptance |
| RunNotebookStage.ps1 / .wls | Resource supervision, unique run IDs and source snapshots |
| PublicationManuscripts.py | Shared Markdown parsing and scholarly formats |
| BuildPublicationDocuments.wls | Notebook frontend construction, rendering and viewpoint roundtrip |

`RunCalibration.wls` provides analytical checks in a clean kernel. Scientific outputs identify their model, inputs, scope, execution status and physical acceptance. Publication builds read the common manifest and saved scientific quantities.

[简体中文](README.zh-CN.md)
