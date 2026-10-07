# Litz-Wire Modeling and Numerical Verification: Comprehensive Research Report · C Acceptance, Diagnostics, and Reproduction

Miao Yuxuan · Huainan Normal University

[Merged manuscript](report_en.md#chapter-C)

<a id="chapter-C"></a>
## C Acceptance, Diagnostics, and Reproduction

Each route retains model, parameter, source-code, and run identities. Original WXF files, checkpoints, Ansys projects, logs, and failure files are not overwritten by conversions. JSON/CSV companions retain real and imaginary parts, units, and strand identity. Ambiguous historical unit annotations are interpreted through source-model definitions and additional notes without rewriting original files. Per-figure mappings record data sources, expressions, independent PDF/SVG/PNG hashes, and composition layout. Valid field integrals and complete spatial-field exports remain separate records; partial recovery is not expanded into an invented complete field.

A minimal failure reproduction includes triggering inputs, the actual error, targeted corrections attempted, stop conditions, and the resources or license needed to continue. Repeated solving of identical code and inputs after a known interface error does not create additional scientific evidence. New inventories point to existing sources and logs without deleting historical abnormal exits or backfilling successful postprocessing as successful original solving. This preserves usable research boundaries for subsequent investigators.

Publication runs limit CPU threads, task memory, and reserved system memory and perform cache reading and postprocessing only. Notebooks save static text, equations, and graphics. Native Graphics3D permits front-end rotation, but opening a manuscript does not run FEM, PEEC, or GPU solving. Missing attachments identify the specific file. Restoration in a path containing spaces, hash consistency, and lightweight reading are part of handover acceptance. Successful layout or export does not change physical acceptance.

q1_fem2_convergence.csv

| nodes | h_over_a | Rac_ohm_per_m | Rac_relative_error |
| --- | --- | --- | --- |
| 353 | 0.24 | 0.02015722 | 0.007045247 |
| 1389 | 0.12 | 0.02002081 | 0.0002302695 |
| 5573 | 0.06 | 0.02001617 | 1.79233e-06 |

peec_length.csv

| filaments | length_m | Rac_ohm_per_axial_m | Rac_over_Rdc |
| --- | --- | --- | --- |
| 1264 | 0.16 | 0.01989922 | 3.647128 |
| 1264 | 0.32 | 0.01995864 | 3.65802 |
| 1264 | 0.64 | 0.01998848 | 3.663488 |
| 5024 | 0.32 | 0.01998302 | 3.639307 |
| 5024 | 0.64 | 0.02001274 | 3.64472 |

rt0_cases.csv

| cells | recomputed_loss_W |
| --- | --- |
| 8192 | 0.0009274631 |
| 16000 | 0.0009335389 |
| 27648 | 0.0009369268 |
| 27648 | 0.0009369268 |

gpu_equivalence.csv

| filaments | L_matrix_relative_error | current_relative_error |
| --- | --- | --- |
| 1264 | 7.075722e-16 | 3.281741e-14 |
| 5024 | 7.481492e-16 | 7.780817e-14 |
<a id="references"></a>
## References
