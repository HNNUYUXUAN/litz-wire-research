# Scientific modules and runners

The installable entry is `litz-research`; see the [developer guide](../docs/development.md).

| Module | Responsibility |
| --- | --- |
| Q1Analytical.wl | Round-wire Bessel impedance, complex current and independent area integrals |
| NotebookPhysics.wl | Analytical, disk FEM, field–circuit and trajectory models |
| CoaxFEM.wl | Sparse multistrand fields with controlled return geometry |
| PEEC.wl | Finite-length longitudinal partial-element model |
| VoxelPEEC.wl, VoxelOperator.wl | Volume-flux representation and matrix-free RT0 operator |
| GPUValidation.wl and GPU kernel modules | Device arithmetic and CPU/GPU equivalence |
| ansys_validate.py, ansys_native3d.py | Maxwell adapters and independent acceptance |
| RunNotebookStage.ps1 / .wls | Resource-supervised stages, unique runs and source snapshots |
| PublicationManuscripts.py | Canonical Markdown parsing and multi-format scholarly editions |
| BuildPublicationDocuments.wls | Notebook frontend build, render and viewpoint roundtrip |

`RunCalibration.wls` provides a standalone fresh-kernel analytical run. `stages/` contains route implementations. Scientific outputs record model identity, inputs, scope, execution and acceptance. Build stages read the shared manifest and frozen publication data.
