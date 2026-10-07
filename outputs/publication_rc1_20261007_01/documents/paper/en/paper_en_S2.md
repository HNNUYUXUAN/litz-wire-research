# Hierarchical Verification, Common-Terminal Current Sharing, and Finite-Length Longitudinal PEEC for Litz-Wire Modeling · S2 Complete Sensitivity Data

Miao Yuxuan · Huainan Normal University

[Merged manuscript](paper_en.md#chapter-S2)

<a id="chapter-S2"></a>
## S2 Complete Sensitivity Data

<a id="S2.geometry.heading"></a>
### Geometry, Actual Arc Length, and Discrete Transposition

Archived straight, single-level, traditional multilevel, and cross-layer centerlines support checks of physical strand identity, period, gap, curvature, arc length, and copper volume. Axial sampling at 400, 800, and 1600 segments and 60 geometry checks support numerical consistency of these quantities; the historical wrapper exit and the unrecorded native kernel exit retain their original status. The 24-strand specimen with 0.100 mm copper diameter has only about 0.1885 mm² nominal copper area. It illustrates construction and is not a final bundle satisfying the 5 mm² requirement. Three-dimensional material, lighting, and rotatable views are reading aids.

The current DTM/iDTM demonstration uses additive discrete blocks [(7)](paper_en.md#E06). Reordering the same weighted impedance blocks does not change their sum. Equal sharing in that implementation therefore does not prove the equivalence of distinct realistic transposition paths or the superiority of a cross-layer structure over traditional multilevel Litz. Comparison with [1, 2] should examine longitudinal transposition, noncommuting hierarchical operations, local-field assumptions, and terminals rather than borrowing the method name alone. Geometric fairness, model adequacy, and performance improvement are three questions requiring separate evidence.

<a id="S2.rt0.heading"></a>
### Three-Dimensional RT0 Imposed-Field Example

The RT0 example is fixed to a homogeneous 1×1×2 mm copper cuboid at 200 kHz, an imposed Bz of 1 mT RMS, and zero net transport. Three-component current is represented by face-flux degrees of freedom; continuity, common-port conditions, and imposed-field power are checked separately. With common integration order q14, 8192, 16000, and 27648 cells yield losses of 0.927463, 0.933539, and 0.936927 mW. The final two changes are 0.655090% and 0.362916%, both below 1%. The q18 comparison on the final grid changes loss by 1.54941×10⁻⁸ and complex face flux by 1.39291×10⁻⁸, below the 0.1% integration target.

Field figures are reconstructed from saved face fluxes. Cell-center J is the mean of opposing face fluxes divided by cell area. Cell-average loss density uses the exact local RT0 overlap integral and is not replaced by center |J|²/σ. Three-dimensional arrows display only the real part at phasor phase zero, with a common length scale; the color scale uses the complex RMS vector norm. The actual section position, sparse vector samples, and full-volume integration are identified separately so that a sampled visualization is not interpreted as a whole-field integral or maximum.

The archived GMRES iteration count is 35 for each level, with true residuals meeting the 10⁻¹¹ target. Null metrics and the failed status in the original q18 summary remain unchanged; the new CSV postprocessing checks are separate evidence. Memory rejection by an older dense algorithm and successful solution by the newer matrix-free implementation belong to different implementations and must not be merged into one status. The conclusion is limited to the fixed imposed-field cuboid, without curved Litz masks, independent boundary-flux validation, or realistic transport terminals.

<a id="S2.aphi.heading"></a>
### Preserved Three-Dimensional A–φ Fields and Failure Diagnostics

A–φ current must be reconstructed from the actual preserved A and gradient of φ [(9)](paper_en.md#E07); an unsuccessful φ field must not be replaced by an analytical value. The three cylinder meshes contain 1683, 3672, and 9108 nodes. Radial J calibration on the finest level meets its threshold, while φ and gauge residuals remain unsuccessful on all three original levels; J also fails on the coarser levels. Manufactured-solution checks test the specified equations and implementation but do not automatically validate these physical cylinder solutions.

Diagnostic figures use 128 preserved field and derivative samples with explicit node identities, showing A, φ, J, and the actual gradient of φ separately. They are not inferred from a decorative surface and are not whole-field extrema. Boundary, scaling, derivative, and postprocessing diagnostics should distinguish implementation defects from approximation errors. Once the bounded revision limit is reached, failures are archived with triggers, minimal reproductions, and conditions for further research. Direct factorization, out-of-core, and iterative failures likewise retain their distinct causes.

<a id="S2.ansys.heading"></a>
### Limited Ansys Validation and Interface Boundaries

The historical valid seven-strand two-dimensional port short test uses 704 cells and includes two voltage basis solutions and an actual ±20 A field solution. Common terminal voltage, complex strand currents, and independent power support this single-level example; it is not three-grid convergence. New fixed-mesh and precision attempts did not produce the required full validation. Native three-dimensional J-expression probes also did not yield an accepted physical solution, so no field-result image or invented numerical value is supplied for them.

Archived boundaries use the checked v252 Student limits of 2000 two-dimensional triangles, 64000 three-dimensional volume cells or 8000 surface cells, and four CPU cores. Interface errors, mesh or license limits, and numerical errors have different meanings and are recorded separately. Actual terminals, curved STL geometry, and full-copper-area large bundles still require suitable licensing, mesh capability, and independent validation. A limited short test cannot support a recommendation about realistic transposition performance.

<a id="E07"></a>
$$
\mathbf J=-\sigma\left(j\omega\mathbf A+\nabla\phi\right).\tag{9}
$$

<a id="fig-geometry_comparison"></a>
![Fig. 14](../../../composites/en/geometry_comparison.png)

<p align="center">Fig. 14. Three-dimensional strand centerline structures.</p>

Panels show straight, single-level, local multilevel, and cross-layer structures.

<a id="fig-rt0_sections"></a>
![Fig. 15](../../../composites/en/rt0_sections.png)

<p align="center">Fig. 15. RT0 imposed-field current and loss sections.</p>

The 1×1×2 mm copper cuboid is excited at 200 kHz by a 1 mT RMS field with zero net transport. (a) Cell-average loss density; (b) complex RMS current norm.

<a id="fig-rt0_vectors"></a>
![Fig. 16](../../../panels/en/rt0_vectors.png)

<p align="center">Fig. 16. RT0 reconstructed three-dimensional current vectors.</p>

The 1×1×2 mm copper cuboid is excited at 200 kHz by a 1 mT RMS field with zero net transport. Arrows show the real part at a fixed phase; color represents the complex RMS norm.

<a id="fig-rt0_spatial"></a>
![Fig. 17](../../../panels/en/rt0_spatial.png)

<p align="center">Fig. 17. RT0 spatial and integration comparisons.</p>

The 1×1×2 mm copper cuboid is excited at 200 kHz by a 1 mT RMS field with zero net transport. The q14 spatial sequence and final q18 comparison use the same imposed-field condition.

<a id="fig-aphi_preserved"></a>
![Fig. 18](../../../composites/en/aphi_preserved.png)

<p align="center">Fig. 18. Preserved A–φ field samples.</p>

Panels show A, φ, J, and the actual gradient of φ.

<a id="fig-aphi_gates"></a>
![Fig. 19](../../../panels/en/aphi_gates.png)

<p align="center">Fig. 19. A–φ cylinder calibration metrics.</p>

Three grids and their metric targets are shown separately.

<a id="fig-ansys_seven_current"></a>
![Fig. 20](../../../panels/en/ansys_seven_current.png)

<p align="center">Fig. 20. Ansys seven-strand two-dimensional complex currents.</p>

The valid 704-cell port short test provides strand magnitudes and phases.

<a id="fig-ansys_limits"></a>
![Fig. 21](../../../panels/en/ansys_limits.png)

<p align="center">Fig. 21. Ansys Student capacity and interface diagnostics.</p>

Ansys Student v252 permits up to 2000 two-dimensional triangles, 64000 three-dimensional volume elements, and 8000 surface elements, with at most 4 CPU cores. Parallel groups identify the license limits. Probes of the current-density expression J are recorded separately from mesh capacity; actual solution status is reported in the three-dimensional diagnostics.

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

[1] Silvano Cruciani, Tommaso Campi, Francesca Maradei, Mauro Feliziani. Numerical Modeling of Litz Wires Based on Discrete Transpositions of Strands and 2-D Finite Element Analysis. IEEE TPEL 38(5):6710–6719, 2023. https://doi.org/10.1109/TPEL.2023.3240338

[2] Xinsheng Zhang, Fei Xiao, Ruitian Wang, Shunjun Chen, Xuexin Fan, Xin Li. AC Impedance Modeling of Composite Litz Wire With Nonideal Transposition Based on Improved Discrete Transposition Model. IEEE TPEL 41(7):11003–11019, 2026. https://doi.org/10.1109/TPEL.2026.3661080
