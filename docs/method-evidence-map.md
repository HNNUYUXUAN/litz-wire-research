# Method → implementation → tests → evidence

| Route | Sources | Implementation | Independent checks | Actual evidence |
| --- | --- | --- | --- | --- |
| Analytical | BESSEL | models/analytic/src/Q1Analytical.wl; python/litz_research/analytical.py | tests/Q1Analytical.wlt; current/power integrals and DC limit | Wolfram calibration and frequency-extension cases |
| 2D FEM | FEMDOC, P04 | models/fem2/src/Physics.wl | Bessel difference, independent quadrature, power; historical mesh series | rc2_route_fem2_01; fem2 dataset |
| Common terminal | P01, P02 | models/common_terminal/src/CoaxFEM.wl | total complex current, linear residual, power; independent Maxwell | cross-solver case; common-terminal dataset |
| Geometry | P01, N01 | models/geometry/src/Physics.wl; TopologyCandidates.py | tests/test_topology_candidates.py; gaps, arc length and volume | geometry tutorial Notebooks; geometry dataset |
| Longitudinal PEEC | RUEHLI1974, P03 | models/peec/src/PEEC.wl | tests/ClosurePEEC.wlt; reciprocity, ports and power | rc2_route_peec_01; peec dataset |
| RT0 vector PEEC | RT1977, RUEHLI1974, GMRES1986 | models/rt0/src/VoxelPEEC.wl; VoxelOperator.wl | tests/VoxelOperator.wlt; continuity, true residual, power | RT0 tutorial Notebooks; rt0 dataset |
| A–phi | FEMDOC, GMRES1986 | models/aphi/src/stages/closure_fem3_diagnostics.wl | saved-field derivative reproduction; original failed potential/gauge gates | aphi-diagnostics case; aphi dataset |
| MCP / harness | AGENTTOOLS, PYAEDTMCP, PYAEDT, MCP, CODEX | automation/mcp/client.py; adapters/ansys/MCPMaxwellCase.py | actual initialization/discovery/calls and saved native results | six cases in automation/examples/verification.json |
| GPU | CUDA | adapters/gpu/; adapters/wolfram/RunResearchCase.wls | CPU/GPU matrix, known solution, true residual, FFT roundtrip | rc2_gpu_full_small_01; gpu tutorial Notebooks |
| Publications | IEEEtran, XeLaTeX and Pandoc 3.13 | python/litz_research/latex_publication.py | paired paragraph and citation identities, scientific hashes, compiled page checks | provenance/current-publication |

Source keys resolve through [the canonical library](../references/README.md). Runtime and physical scope are recorded independently. Tutorial success does not replace full mesh, length, boundary or geometry validation. [Case records](../automation/examples/verification.json) and [Notebook receipts](../provenance/rc2/notebook_verification.json) bind exact run identities and saved artifacts.
