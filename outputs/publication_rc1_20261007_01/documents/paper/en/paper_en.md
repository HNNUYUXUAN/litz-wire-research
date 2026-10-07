# Hierarchical Verification, Common-Terminal Current Sharing, and Finite-Length Longitudinal PEEC for Litz-Wire Modeling

Miao Yuxuan · Huainan Normal University

- [01 Introduction](#chapter-01)
- [02 Methods](#chapter-02)
- [03 Results](#chapter-03)
- [04 Discussion](#chapter-04)
- [05 Conclusions](#chapter-05)
- [S1 Theory and Discretization](#chapter-S1)
- [S2 Complete Sensitivity Data](#chapter-S2)
- [S3 Sources and Reproduction](#chapter-S3)

<a id="abstract"></a>
## Abstract

High-frequency loss in Litz wire depends on strand skin effect, local proximity fields, complex current sharing, transposition paths, and terminal constraints. This study establishes a reproducible hierarchy of numerical verification in which the physical content retained by each model is stated explicitly. Individually insulated strands connected in parallel are described by a common terminal voltage and a total complex-current constraint, yielding a current-sharing criterion within a specified linear field–circuit model. Finite-length longitudinal PEEC is then examined through independent changes in axial length, mutual and self integration, and cross-sectional discretization.

For copper at 200 kHz, 20 A RMS, and 20 °C, the round-wire analytical solution and independent two-dimensional calibration establish an internal-field reference. The 640-strand common-terminal model has controlled mesh, return, and exterior-boundary checks. The final 5024-degree-of-freedom longitudinal model gives an axial resistance of 20.012738 mΩ/m, differing by 0.044582% from its equal-area Bessel reference. The final two loss changes in the fixed-cuboid imposed-field RT0 example are 0.655090% and 0.362916%; this example tests an imposed-field operator and does not measure Litz transport resistance. Unsuccessful three-dimensional A–φ validation, new Ansys interfaces, and unresolved realistic-geometry ranking remain explicit boundaries. These results support numerical conclusions within stated models, without establishing the superiority of actual multilevel or cross-layer Litz structures.

Keywords: Litz wire; hierarchical verification; skin and proximity effects; common-terminal circuits; finite-length PEEC; reproducible numerical research

<a id="chapter-01"></a>
## 01 Introduction

<a id="01.introduction.heading"></a>
### Introduction

Dividing a copper cross-section into many fine strands does not by itself guarantee a reduction in high-frequency loss. Strand diameter sets the local skin-effect scale; neighboring conductors and the return determine the surrounding magnetic field; longitudinal positions and common terminals determine complex strand currents. Comparing geometry alone, nominal copper area, or an assumed average current merges distinct mechanisms into a single indicator. A defensible structural comparison first identifies the fields and constraints retained by a model and then checks the numerical uncertainty relevant to those quantities.

Existing approaches address different scales. DTM combines discrete transpositions with two-dimensional FEM [1], linking strand-position permutations to cross-sectional fields; iDTM additionally considers nonideal hierarchical and subbundle transpositions [2]. The improved segmented equivalent circuit [3] constructs a reduced circuit under its stated winding and layer assumptions. FEM–PEEC coupling [4] and quasi-two-dimensional multiconductor modeling [5] use different macroscopic fields, axial electric fields, and current constraints. Continuum models [6] and complex-permeability homogenization [7] reduce the cost of large winding simulations, but their average fields do not directly replace strand-resolved complex currents or realistic end regions.

The emphasis here is a set of comparable quantities and verification relationships needed for structural research. The first contribution separates the analytical, two-dimensional, longitudinal, and full-component voxel models according to what each can verify. The second derives a current-sharing condition from the common-terminal augmented system and states its model scope. The third performs single-factor sensitivity checks for finite-length longitudinal PEEC while interpreting CPU/GPU agreement separately from physical validation. Traditional multilevel Litz remains a strong baseline. Cross-layer geometry is a candidate for subsequent verification, without a presumed performance advantage.

<a id="01.scope.heading"></a>
### Scope

Three questions organize the verification: whether independent discretizations reproduce the local skin-effect reference; which algebraic conditions determine complex current sharing under common terminals; and how strongly the resistance obtained from a finite longitudinal kernel depends on length and integration settings. The contributions are consistent observables, inspectable verification relationships, and quantitative evidence within each model, supporting the selection of the next model for realistic transposition research.

<a id="chapter-02"></a>
## 02 Methods

<a id="02.conventions.heading"></a>
### Operating Conditions, Quantities, and Fair Comparisons

Calculations use SI units, exp(jωt), and RMS phasors. Copper at 20 °C has conductivity 5.8×10⁷ S/m and relative permeability one. The main transport condition is 200 kHz and 20 A RMS with no independent imposed field. Strands are insulated along their paths and connected in parallel at the ends. Every per-metre quantity refers to axial length; actual strand arc lengths are reported separately. A finite-segment terminal voltage V and the axial electric field used by a two-dimensional model have different units, so their length normalization must remain explicit.

The original Q1 conductor with diameter 2 mm is retained as an analytical calibration. Its copper area is 3.141593 mm² and its DC current density is 6.366198 A/mm², exceeding the 4 A/mm² constraint; it therefore does not satisfy the final design condition. Q2 requires at least 5 mm² nominal copper area. The ideal circular area of 640 strands of diameter 0.100 mm is 5.026548 mm², whereas the original two-dimensional 64-sided approximation has an area of approximately 5.018478 mm². Equal-copper references should use the actual chosen area to avoid interpreting an area-discretization difference as a purely electromagnetic improvement.

For unequal strand lengths, DC resistance follows from the sum of parallel conductances [(1)](paper_en.md#E01). Copper volume, arc-length growth, absolute AC resistance, its ratio to DC resistance, loss, and complex strand currents are all reported rather than reducing the comparison to one ratio. RMS Joule loss uses [(2)](paper_en.md#E02) without the one-half factor associated with peak phasors. With an independent imposed field, absorbed power includes work done by that excitation. RT0 imposed-field loss cannot be divided unconditionally by 20² and named intrinsic transport resistance. Equal nominal copper area also does not imply equal copper volume per axial metre.

<a id="02.hierarchy.heading"></a>
### Model Hierarchy and Verification Methods

The hierarchy is organized by unknowns and comparable observables. The analytical round wire supplies internal impedance and radial current for a homogeneous long straight conductor; two-dimensional diffusion verifies the same internal-field problem. The multistrand two-dimensional common-terminal model additionally retains intrastand fields, complex current sharing, and an explicit return, while omitting longitudinal transposition and finite end regions. Longitudinal PEEC retains a finite-length partial-inductance kernel and common-terminal constraints but lacks complete transverse current loops. The three-component RT0 imposed-field example tests a three-dimensional operator, continuity, and field absorption; it remains distinct from transport in curved Litz geometry.

Verification combines solver residuals, constraints, independent power evaluation, and parameter sensitivities. The retained targets are 10⁻⁸ for true linear residuals and common-terminal or total-current constraints, 0.1% for independent power balance, and 1% for relevant mesh, segmentation, boundary, and length changes. Analytical references and analytical current/power integrals have their own stricter targets. RT0 keeps a true GMRES residual target of 10⁻¹¹ and an integration sensitivity target of 0.1%; CPU/GPU matrix and complex-current comparisons use 10⁻¹⁰. These are definitions of the checks performed in this study, not a claim that every physical problem has already attained the same accuracy.

Evidence can be cross-compared only under shared assumptions; a conclusion does not propagate automatically along a diagram arrow. A small linear residual indicates that the assembled system was solved accurately but does not exclude omitted physics or an incorrect boundary. Power balance constrains consistency between the discretization and postprocessing, yet a conservative but inappropriate model may also balance power. Agreement between two levels limits variation under a specified perturbation; it is not an unconditional error bound or a statistical confidence interval. Execution status, numerical-check status, and physical applicability are therefore archived separately.

<a id="02.common.heading"></a>
### Common-Terminal Field–Circuit Model and Complex Current Sharing

Parallel terminals do not require strand currents to be prescribed as equal. Let Z denote the coupled impedance matrix of a specified linear model, e the independently induced term, and i the complex strand-current vector. Common terminal voltage and total current form the augmented system [(3)](paper_en.md#E04). The implementation solves this system rather than relying on an explicit matrix inverse. Both magnitude and phase are determined by the coupled field–circuit problem. Comparing only current magnitudes overlooks the relationship between individual phasors and their complex sum.

Assuming a unique solution of the augmented system, substitution of i=(It/N)1 into the terminal equation shows that equal current sharing holds exactly when [(It/N)Z1+e] lies in the span of 1. Projection by Q gives [(4)](paper_en.md#E05). Without an independent imposed field, the condition reduces to equality of impedance row sums. With an imposed field, the induced term can preserve or break it. This algebraic criterion applies to the specified Z, e, and terminal model; it is not a theorem of equal sharing for arbitrary continuously transposed three-dimensional geometry.

The two-dimensional common-terminal FEM solves the shared axial electric field together with Az degrees of freedom. The preserved u and terminal field are measured in V/m, with Jz=σ(v−u); the return uses its own terminal field, and air is not assigned conductor current. Figures reconstruct Jz from original nodes and material triangles and retain the original coordinate scaling in the integrals. Independent linear-triangle mass integration is compared with complex strand currents, bundle and return losses, and copper area, making the color map auditable. The preserved u itself is not current density.

<a id="02.peec_method.heading"></a>
### Finite-Length Longitudinal PEEC: Theory and Discretization

The longitudinal model carries axial, uniform-in-length complex current in cross-sectional volume filaments. The ohmic term is each filament’s finite-segment resistance, and partial inductance is obtained by integrating the finite-volume 1/|r−r′| kernel [(5)](paper_en.md#E08). A common port and total-current constraint are again solved through [(3)](paper_en.md#E04). Here, 1264 and 5024 count volume-filament degrees of freedom, not insulated Litz strands. Radial concentration can appear through cross-sectional current redistribution, but the basis contains neither complete transverse eddy-current loops nor realistic end redistribution.

Mutual-integration order and self-integration accuracy are archived as separate options. The fixed 1264-degree-of-freedom cross-section is first examined at lengths 0.16, 0.32, and 0.64 m. Integration checks then hold length fixed and change one factor at a time across mutual orders q=4, 6, and 8 and self settings 10/8 to 12/10. The representative 5024 model rechecks the final two lengths and integration settings. Because m40 and m80 have slightly different actual copper areas, each level is interpreted against its own equal-area Bessel reference; an area change is not concealed as pure discretization error.

The external magnetic contribution to partial inductance differs from the internal Bessel impedance of a long straight wire. Analytical comparison therefore focuses on AC resistance while retaining length and actual area. Length variation limits sensitivity of the present finite-kernel calculation to the chosen length but does not introduce transverse basis functions. In comparison with FEM–PEEC literature [4], the longitudinal volume basis, excitation, return, and feedback treatment must each be identified. An assumption of one coupling implementation should not be generalized to every PEEC method.

<a id="E01"></a>
$$
R_{\mathrm{dc}}=\left(\sum_{k=1}^{N}\frac{\sigma A_k}{\ell_k}\right)^{-1},\qquad V_{\mathrm{Cu}}=\sum_{k=1}^{N}A_k\ell_k.\tag{1}
$$

<a id="E02"></a>
$$
P_{\mathrm{Cu}}=\int_{\Omega_{\mathrm{Cu}}}|\mathbf J|^2/\sigma\,\mathrm d\Omega,\quad R_{\mathrm{ac}}=P_{\mathrm{Cu}}/|I_t|^2,\quad r_{\mathrm{ac}}=R_{\mathrm{ac}}/L_z.\tag{2}
$$

<a id="E04"></a>
$$
\begin{bmatrix} Z&-\mathbf1\\ \mathbf1^T&0\end{bmatrix}\begin{bmatrix}\mathbf i\\V\end{bmatrix}=\begin{bmatrix}-\mathbf e\\I_t\end{bmatrix}.\tag{3}
$$

<a id="E05"></a>
$$
Q=I_N-\mathbf1\mathbf1^T/N,\qquad Q\left[(I_t/N)Z\mathbf1+\mathbf e\right]=\mathbf0.\tag{4}
$$

<a id="E08"></a>
$$
R_{\alpha\beta}=\delta_{\alpha\beta}\frac{L_z}{\sigma A_\alpha},\qquad L_{\alpha\beta}=\frac{\mu}{4\pi A_\alpha A_\beta}\int_{V_\alpha}\int_{V_\beta}\frac{\hat{\mathbf t}_\alpha\cdot\hat{\mathbf t}_\beta}{|\mathbf r-\mathbf r'|}\,\mathrm dV\,\mathrm dV'.\tag{5}
$$

<a id="fig-model_hierarchy"></a>
![Fig. 1](../../../panels/en/model_hierarchy.png)

<p align="center">Fig. 1. Model hierarchy and comparable observables.</p>

Transport models are grouped by physical object and observable: round-wire internal fields support analytical and two-dimensional calibration, multistrand field–circuit models resolve common-terminal phasor currents, and longitudinal PEEC examines finite-length effects. Links identify internal-field calibration or equal-area resistance references. RT0 imposed-field loss and three-dimensional A–φ diagnostics occupy separate research scopes.

<a id="fig-common_terminal"></a>
![Fig. 2](../../../panels/en/common_terminal.png)

<p align="center">Fig. 2. Multistrand common terminals and return.</p>

Strands are insulated along their paths and connected in parallel at both ends; their phasor currents follow from the common voltage and total-current constraints. The coupling matrix Z and excitation term e contain the impedance and field contributions retained by the model. The controlled return carries the opposite total current and has its own terminal field. Known inputs and unknown currents and voltage are identified.

<a id="chapter-03"></a>
## 03 Results

<a id="03.analytic.heading"></a>
### Round-Wire Analysis and Independent Two-Dimensional Calibration

The long straight round-wire internal solution uses modified Bessel functions [(6)](paper_en.md#E03). At 200 kHz, the skin depth is 0.147771655 mm, producing pronounced surface concentration relative to the 1 mm radius. Frozen analytical values are 5.488101486 mΩ/m DC resistance, 20.016203628 mΩ/m AC resistance, a ratio of 3.647199980, and loss of 8.006481451 W/m. This internal impedance excludes the external inductance determined by the return path. Radial phase retains the original complex phasor and is displayed with a continuous nearest-neighbor 360° lift; unwrapping changes the display, not the underlying data.

Independent two-dimensional disk diffusion uses 353, 1389, and 5573 nodes and is normalized by total complex current. The finest relative AC-resistance error against the analytical reference is 1.79233×10⁻⁶, and the power-integral discrepancy is 3.06800×10⁻⁶. These results support discretization and normalization for the isolated internal-field problem. Its boundary conditions differ from a finite three-dimensional end region, so this error cannot be transferred directly to that problem. The analytical cross-sectional image is formed by linear interpolation of radial analytical magnitudes followed by an axisymmetric mapping.

<a id="03.coax_results.heading"></a>
### The 640-Strand Two-Dimensional Result and Its Boundaries

The frozen three-grid, return, and exterior checks for the 640-strand straight bundle contain 23 passing checks. The final AC-resistance mesh change is 0.011902%, the return-distance change is 0.000495%, and the exterior-boundary change is 0.000270%, all below the route-specific 1% target. These results show stability of the specified two-dimensional common-terminal model under the perturbations examined; they do not establish convergence of finite end regions in an actual manufactured bundle. Bundle resistance and return loss are reported separately so that heating in the return is not mistaken for an intrinsic conductor improvement.

Individual magnitude and phase reveal current sharing under the common voltage. A line at It/N is only a reference, not a prescribed constraint. Consistency between current integration and the common-terminal condition is a prerequisite for interpreting sharing. In a two-dimensional straight bundle, reducing strand diameter does not imply longitudinal exchange of strand positions. The principal role of this model is to verify multistrand field–circuit coupling with controlled boundaries and provide cross-sectional evidence for later transposition modeling. Final structural ranking still requires a model or experiment that retains longitudinal coupling, actual terminals, and relevant numerical uncertainty.

<a id="03.peec_results.heading"></a>
### Longitudinal PEEC Sensitivity and Results

For 1264 degrees of freedom, the 0.16, 0.32, and 0.64 m cases give axial AC resistances of 19.899215, 19.958642, and 19.988477 mΩ/m. Both length increments change resistance by less than 1%, and the 0.32-to-0.64 m change at 5024 degrees of freedom also meets the target. Mutual orders q4/6/8, self settings 10/8 to 12/10, and the coarse-to-fine comparison of the actual cross-sections satisfy the bounded campaign criteria. One factor changes at a time. The unexecuted 1.28 m level remains unexecuted and is not assigned an extrapolated result or a zero error.

The final 5024-degree-of-freedom case at axial length 0.64 m, mutual order q4, and self setting 12/10 gives 20.012738128 mΩ/m AC resistance, a ratio to DC resistance of 3.644719868, and loss of 8.005095251 W/m. Its difference from the equal-area Bessel reference is 0.044582%. The cross-sectional color map is reconstructed from preserved filament currents and square cells. A filament-current deviation describes redistribution inside the discretized conductor; it is not a sharing metric for physical insulated Litz strands.

Length sensitivity and the analytical reference answer different questions. The former examines variation of the finite-length kernel over the chosen interval; the latter checks resistance against the comparable scale of long straight-wire internal behavior. Agreement does not eliminate a boundary or basis limitation. In particular, a small integration change supports the present integration implementation but supplies no additional evidence for real end regions, transverse currents in curved strands, or redistribution at terminals. The result is therefore described as bounded acceptance within the longitudinal model.

<a id="03.compute.heading"></a>
### CPU/GPU Equivalence and Resource Boundaries

CPU/GPU comparisons hold the longitudinal model and discretization fixed. At 5024 degrees of freedom, relative differences are 7.48149×10⁻¹⁶ for the L matrix and 7.78082×10⁻¹⁴ for complex current, below the 10⁻¹⁰ target; the 1264 comparison also passes. This supports equivalence of the implemented CPU/GPU algorithms for the compared matrix and port solution. It adds no physical content to the model, and timings from different sizes or integration settings cannot establish a speedup.

Historical 9856-degree-of-freedom results recover only part of the available current and related data. Missing complete matrices, common voltage, or full fields prevent an upgrade to full validation. The 20108 and larger cases retain their archived resource boundaries and exits. Resource curves use attributable process-tree samples only; short peaks may be missed and records mixed with unrelated PIDs are excluded. Computational capability and physical failure are interpreted separately: unavailable resources are not acceptance, and completed execution is not physical validation.

The 640-strand bundle has Rac=15.793003197 mΩ per axial metre, bundle loss 6.317201279 W per axial metre, return loss 2.196205516 W per axial metre, and actual copper area 5.018478 mm². The shared axial terminal field is 0.411856245+j(4.064969103) V/m. The normalized RMS complex-current deviation is 1.854214; the phasor sum recovers the total 20 A RMS transport current.

<a id="E03"></a>
$$
\delta=(\pi f\mu\sigma)^{-1/2},\quad\kappa=(1+j)/\delta,\quad J_z(r)=\frac{I_t\kappa I_0(\kappa r)}{2\pi a I_1(\kappa a)},\quad z_{\mathrm{int}}=\frac{\kappa I_0(\kappa a)}{2\pi a\sigma I_1(\kappa a)}.\tag{6}
$$

<a id="fig-q1_profile"></a>
![Fig. 3](../../../composites/en/q1_profile.png)

<p align="center">Fig. 3. Round-wire radial current magnitude and phase.</p>

The copper conductor has diameter 2 mm and carries 20 A RMS at 200 kHz. (a) RMS magnitude; (b) continuously displayed phase.

<a id="fig-q1_cross_section"></a>
![Fig. 4](../../../panels/en/q1_cross_section.png)

<p align="center">Fig. 4. Analytical round-wire cross-sectional magnitude.</p>

The copper conductor has diameter 2 mm and carries 20 A RMS at 200 kHz. The color scale represents axial RMS current density.

<a id="fig-q1_fem_error"></a>
![Fig. 5](../../../panels/en/q1_fem_error.png)

<p align="center">Fig. 5. Round-wire two-dimensional calibration errors.</p>

The copper conductor has diameter 2 mm and carries 20 A RMS at 200 kHz. Three grids and independent power integrals concern the same internal-field problem.

<a id="fig-coax640_currents"></a>
![Fig. 6](../../../composites/en/coax640_currents.png)

<p align="center">Fig. 6. 640-strand common-terminal complex current sharing.</p>

(a) Magnitude; (b) phase, ordered by physical strand identity.

<a id="fig-coax640_fields"></a>
![Fig. 7](../../../composites/en/coax640_fields.png)

<p align="center">Fig. 7. 640-strand two-dimensional cross-sectional current density.</p>

(a) RMS magnitude; (b) phase, with material markers identifying strands.

<a id="fig-coax640_mesh"></a>
![Fig. 8](../../../panels/en/coax640_mesh.png)

<p align="center">Fig. 8. 640-strand mesh and boundary sensitivities.</p>

Mesh, return, and exterior tests each vary one factor.

<a id="fig-peec_cross_section"></a>
![Fig. 9](../../../panels/en/peec_cross_section.png)

<p align="center">Fig. 9. Longitudinal PEEC cross-sectional current.</p>

Complex currents in square volume filaments reconstruct the RMS magnitude.

<a id="fig-peec_length"></a>
![Fig. 10](../../../panels/en/peec_length.png)

<p align="center">Fig. 10. Longitudinal PEEC length sensitivity.</p>

Resistance per axial length is compared at archived lengths for the same cross-section.

<a id="fig-peec_sensitivity"></a>
![Fig. 11](../../../panels/en/peec_sensitivity.png)

<p align="center">Fig. 11. Longitudinal PEEC integration sensitivity.</p>

Mutual order and self accuracy are compared in separate single-factor tests.

<a id="fig-gpu_equivalence"></a>
![Fig. 12](../../../panels/en/gpu_equivalence.png)

<p align="center">Fig. 12. CPU/GPU same-model numerical comparison.</p>

Relative matrix and complex-current differences use identical discretization and integration.

<a id="fig-resource_memory"></a>
![Fig. 13](../../../panels/en/resource_memory.png)

<p align="center">Fig. 13. Attributable process-tree resource curves.</p>

Curves use archived time and memory samples.

<a id="chapter-04"></a>
## 04 Discussion

<a id="04.discussion.heading"></a>
### Discussion: Model Uncertainty and Relation to Literature

The results show that equal sharing and low loss are not a single issue determined only by strand size. The common-terminal model permits self-consistent changes in both current magnitude and phase, whereas current geometry displays supply paths and arc-length costs. A realistic comparison must carry these terminal constraints into an electromagnetic model with adequate longitudinal coupling and use consistent actual copper area, return, and length definitions. A proposed improvement must also exceed relevant numerical uncertainty; a small solver residual cannot cancel unresolved model error.

The relationship to [1, 2] concerns transposition representation and scope rather than replication of all published experiments. The connection to [3] is an interpretable reduced circuit, but its winding-specific experimental error is not imported as this project’s accuracy. Common voltage and total-current constraints in [5] provide a methodological link; its frequencies, dimensions, and quasi-two-dimensional assumptions do not directly validate the present 200 kHz large bundle. Homogenization studies [6, 7] also emphasize consistent allocation of macroscopic fields and microscopic local losses to avoid double counting. Averaging does not automatically establish uniform strand currents.

No thermal model or experimental measurement is available here to test winding tolerances, terminal contacts, insulation thickness, or temperature rise. RT0 imposed-field refinement and longitudinal PEEC agreement with analytical resistance provide localized evidence. Unsuccessful three-dimensional A–φ validation and native Ansys interfaces remain practical research boundaries. A subsequent priority is an affordable small-strand three-dimensional cross-check with real ends, return, and transverse degrees of freedom, followed by full-copper-area multilevel baselines and candidate structures, and ultimately controlled measurement.

<a id="04.recommendations.heading"></a>
### Recommendations

Further research should follow the remaining model gaps: establish boundary, gauge, and terminal-field consistency on an affordable three-dimensional calibration body; introduce realistic terminals and transverse freedom for a small strand count; and then compare full-copper multilevel and cross-layer structures. Experiments should measure impedance at common frequency, temperature, return, and axial length, with terminal resistance and geometric tolerances recorded. Proposed improvements should be compared with both numerical and measurement uncertainty.

<a id="chapter-05"></a>
## 05 Conclusions

First, the hierarchical framework records shared physical content separately from each model’s omissions, allowing analytical, two-dimensional, longitudinal, and three-dimensional imposed-field results to be used within comparable scopes. Second, the common-terminal augmented system provides a complex-current sharing criterion for the specified linear model, avoiding validation by prescribed equal currents. Third, the executed length and integration sensitivities of finite-length longitudinal PEEC meet the bounded campaign targets, and the final resistance agrees with its equal-area analytical reference. This conclusion remains limited by the longitudinal basis.

The 640-strand two-dimensional field, fixed imposed-field RT0 cuboid, and same-model CPU/GPU comparisons provide frozen evidence that can be redrawn. Three-dimensional electromagnetic ranking of realistic transposed bundles, thermal modeling, and experimental validation remain open. Failure routes retain triggers, original results, and the capabilities required to continue.

<a id="chapter-S1"></a>
## S1 Theory and Discretization

<a id="S1.round_derivation.heading"></a>
### Round Derivation

The axial current in a round wire satisfies (1/r)d(r dJz/dr)/dr=κ²Jz. Regularity at the axis selects I₀(κr). The identity ∫₀ᵃ rI₀(κr)dr=aI₁(κa)/κ together with the total-current constraint determines the normalization. The surface axial electric field divided by total current gives the internal impedance; its real part is checked by an independent Joule integral. Thus the derivation connects analytical shape, normalization, and power.

<a id="S1.sharing_derivation.heading"></a>
### Sharing Derivation

Sufficiency of the sharing criterion follows from uniqueness of the port solution. If the projection condition holds, every component of (It/N)Z1+e is equal, so a common voltage exists for which the equal-current vector satisfies both the port equations and the total-current constraint. Necessity follows by substitution of an existing equal-current solution. Numerical sharing is assessed using normalized complex-current deviation, with magnitude and phase reported to retain the information in phasor addition.

<a id="S1.dtm_derivation.heading"></a>
### Dtm Derivation

Let Ps map fixed physical strand identities to spatial positions in section s. The local current is Ps i and the voltage in identity coordinates is PsᵀZsPs i. Summation over series segments Δzs yields the total impedance. Position permutation and current identity therefore have separate records; K, 2K, and 4K segmentation checks concern the same paths and physical strands. Period, gap, and arc-length checks constrain geometric feasibility and copper usage separately.

<a id="S1.peec_derivation.heading"></a>
### Peec Derivation

Within each volume filament, current is represented by the constant axial density iα/Aα. Projection of the volume-integral vector potential onto the testing filament and integration along length produces the symmetric partial-inductance matrix. The self kernel is integrable but singular at coincidence and uses a dedicated accuracy setting; mutual terms use an independent order. Combining finite-segment ohmic resistance with jωL forms Z, after which the common-terminal augmented system determines filament currents and terminal voltage.

<a id="S1.triangle_derivation.heading"></a>
### Triangle Derivation

On a linear triangle, J=ΣₐNaJa. Current integration uses A/3 for each shape function. Joule integration uses the mass matrix and Joule expression in [(8)](paper_en.md#E09). Material markers assign each cell to a strand, the return, or air. Coordinates are converted to metres before area evaluation, and the integrated power is independently compared with the archived scalar.

<a id="E06"></a>
$$
Z_{\mathrm{tot}}=\sum_{s=1}^{K}\Delta z_s P_s^T Z_s P_s.\tag{7}
$$

<a id="E09"></a>
$$
M_T=\frac{A_T}{12}\begin{bmatrix}2&1&1\\1&2&1\\1&1&2\end{bmatrix},\qquad P_T=\mathbf J_T^H M_T\mathbf J_T/\sigma.\tag{8}
$$

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

<a id="chapter-S3"></a>
## S3 Sources and Reproduction

<a id="S3.report_repro.heading"></a>
### Reproduction, Failure Boundaries, and Frozen Data

Each route retains model, parameter, source-code, and run identities. Original WXF files, checkpoints, Ansys projects, logs, and failure files are not overwritten by conversions. JSON/CSV companions retain real and imaginary parts, units, and strand identity. Ambiguous historical unit annotations are interpreted through source-model definitions and additional notes without rewriting original files. Per-figure mappings record data sources, expressions, independent PDF/SVG/PNG hashes, and composition layout. Valid field integrals and complete spatial-field exports remain separate records; partial recovery is not expanded into an invented complete field.

A minimal failure reproduction includes triggering inputs, the actual error, targeted corrections attempted, stop conditions, and the resources or license needed to continue. Repeated solving of identical code and inputs after a known interface error does not create additional scientific evidence. New inventories point to existing sources and logs without deleting historical abnormal exits or backfilling successful postprocessing as successful original solving. This preserves usable research boundaries for subsequent investigators.

Publication runs limit CPU threads, task memory, and reserved system memory and perform cache reading and postprocessing only. Notebooks save static text, equations, and graphics. Native Graphics3D permits front-end rotation, but opening a manuscript does not run FEM, PEEC, or GPU solving. Missing attachments identify the specific file. Restoration in a path containing spaces, hash consistency, and lightweight reading are part of handover acceptance. Successful layout or export does not change physical acceptance.

<a id="S3.workflow.heading"></a>
### Workflow

Reproduction has separate entry points for research computation and publication building. The research entry reads original inputs and solver settings and performs the corresponding validation. The publication entry reads frozen data, verified independent panels, and Markdown prose to produce chapters, merged texts, and multiple formats. Each stage records input and output hashes and reuses a completed stage only when dependencies and products agree. Independent panels retain vector curves and fonts; composition manifests record panel identities and layout parameters.

来源清单 / Source manifest: source_provenance.json; quantities.json; asset_sources.json.

冻结来源与完整性 / Frozen sources and integrity

| Source | SHA256 |
| --- | --- |
| docs/总控/当前运行索引.json | 3324976d4af8f58e60820a88ae978246443f78fbdd0cfa1050e86809110ae60d |
| outputs/prewrite_closure_state.json | 80a66afa79c321a89f730b102af0e70125f6e1655372717d6b59f470c6520e71 |
<a id="references"></a>
## References

[1] Silvano Cruciani, Tommaso Campi, Francesca Maradei, Mauro Feliziani. Numerical Modeling of Litz Wires Based on Discrete Transpositions of Strands and 2-D Finite Element Analysis. IEEE TPEL 38(5):6710–6719, 2023. https://doi.org/10.1109/TPEL.2023.3240338

[2] Xinsheng Zhang, Fei Xiao, Ruitian Wang, Shunjun Chen, Xuexin Fan, Xin Li. AC Impedance Modeling of Composite Litz Wire With Nonideal Transposition Based on Improved Discrete Transposition Model. IEEE TPEL 41(7):11003–11019, 2026. https://doi.org/10.1109/TPEL.2026.3661080

[3] Yueyin Wang, Wu Chen, Zhan Shen. Modeling of Litz Wire Winding AC Resistance Based on Improved Segmented Equivalent Circuit. IEEE TPEL 39(1):1135–1149, 2024. https://doi.org/10.1109/TPEL.2023.3321327

[4] Andreas Roßkopf, Eberhard Bär, Christopher Joffe, Clemens Bonse. Calculation of Power Losses in Litz Wire Systems by Coupling FEM and PEEC Method. IEEE TPEL 31(9):6442–6449, 2016. https://doi.org/10.1109/TPEL.2015.2499793

[5] Tamás Bakondi, Sándor Bilicz, Szabolcs Gyimóthy. Finite element modeling of eddy currents in a multiconductor system with quasi-2D symmetry. COMPEL 44(5):730–742, 2025. https://doi.org/10.1108/COMPEL-01-2025-0031

[6] David C. Meeker. An Improved Continuum Skin and Proximity Effect Model for Hexagonally Packed Wires. JCAM 236(18):4635–4644, 2012. https://doi.org/10.1016/j.cam.2012.04.009

[7] Korawich Niyomsatian, Johan Gyselinck, Ruth V. Sabariego. Closed-form complex permeability expression for proximity-effect homogenisation of litz-wire windings. IET SMT 14(3):287–291, 2020. https://doi.org/10.1049/iet-smt.2019.0377
