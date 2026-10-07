# Litz-Wire Modeling and Numerical Verification: Comprehensive Research Report · 04 Multistrand Common-Terminal Circuits and Sharing Criterion

Miao Yuxuan · Huainan Normal University

[Merged manuscript](report_en.md#chapter-04)

<a id="chapter-04"></a>
## 04 Multistrand Common-Terminal Circuits and Sharing Criterion

<a id="04.common.heading"></a>
### Common-Terminal Field–Circuit Model and Complex Current Sharing

Parallel terminals do not require strand currents to be prescribed as equal. Let Z denote the coupled impedance matrix of a specified linear model, e the independently induced term, and i the complex strand-current vector. Common terminal voltage and total current form the augmented system [(4)](report_en.md#E04). The implementation solves this system rather than relying on an explicit matrix inverse. Both magnitude and phase are determined by the coupled field–circuit problem. Comparing only current magnitudes overlooks the relationship between individual phasors and their complex sum.

Assuming a unique solution of the augmented system, substitution of i=(It/N)1 into the terminal equation shows that equal current sharing holds exactly when [(It/N)Z1+e] lies in the span of 1. Projection by Q gives [(5)](report_en.md#E05). Without an independent imposed field, the condition reduces to equality of impedance row sums. With an imposed field, the induced term can preserve or break it. This algebraic criterion applies to the specified Z, e, and terminal model; it is not a theorem of equal sharing for arbitrary continuously transposed three-dimensional geometry.

The two-dimensional common-terminal FEM solves the shared axial electric field together with Az degrees of freedom. The preserved u and terminal field are measured in V/m, with Jz=σ(v−u); the return uses its own terminal field, and air is not assigned conductor current. Figures reconstruct Jz from original nodes and material triangles and retain the original coordinate scaling in the integrals. Independent linear-triangle mass integration is compared with complex strand currents, bundle and return losses, and copper area, making the color map auditable. The preserved u itself is not current density.

<a id="04.sharing_derivation.heading"></a>
### Sharing Derivation

Sufficiency of the sharing criterion follows from uniqueness of the port solution. If the projection condition holds, every component of (It/N)Z1+e is equal, so a common voltage exists for which the equal-current vector satisfies both the port equations and the total-current constraint. Necessity follows by substitution of an existing equal-current solution. Numerical sharing is assessed using normalized complex-current deviation, with magnitude and phase reported to retain the information in phasor addition.

<a id="04.coax_results.heading"></a>
### The 640-Strand Two-Dimensional Result and Its Boundaries

The frozen three-grid, return, and exterior checks for the 640-strand straight bundle contain 23 passing checks. The final AC-resistance mesh change is 0.011902%, the return-distance change is 0.000495%, and the exterior-boundary change is 0.000270%, all below the route-specific 1% target. These results show stability of the specified two-dimensional common-terminal model under the perturbations examined; they do not establish convergence of finite end regions in an actual manufactured bundle. Bundle resistance and return loss are reported separately so that heating in the return is not mistaken for an intrinsic conductor improvement.

Individual magnitude and phase reveal current sharing under the common voltage. A line at It/N is only a reference, not a prescribed constraint. Consistency between current integration and the common-terminal condition is a prerequisite for interpreting sharing. In a two-dimensional straight bundle, reducing strand diameter does not imply longitudinal exchange of strand positions. The principal role of this model is to verify multistrand field–circuit coupling with controlled boundaries and provide cross-sectional evidence for later transposition modeling. Final structural ranking still requires a model or experiment that retains longitudinal coupling, actual terminals, and relevant numerical uncertainty.

<a id="04.interpretation.heading"></a>
### Interpretation

The 640-strand section distinguishes the skin-effect scale of an individual fine strand from collective current redistribution in the bundle. Inner and outer strands experience different magnetic coupling; under a common terminal field, this difference appears in current magnitude and phase. DC area supplies a reference for copper utilization, the bundle Joule integral gives transport loss, and the separate return integral describes energy allocation across the complete field–circuit system.

The 640-strand bundle has Rac=15.793003197 mΩ per axial metre, bundle loss 6.317201279 W per axial metre, return loss 2.196205516 W per axial metre, and actual copper area 5.018478 mm². The shared axial terminal field is 0.411856245+j(4.064969103) V/m. The normalized RMS complex-current deviation is 1.854214; the phasor sum recovers the total 20 A RMS transport current.

<a id="E04"></a>
$$
\begin{bmatrix} Z&-\mathbf1\\ \mathbf1^T&0\end{bmatrix}\begin{bmatrix}\mathbf i\\V\end{bmatrix}=\begin{bmatrix}-\mathbf e\\I_t\end{bmatrix}.\tag{4}
$$

<a id="E05"></a>
$$
Q=I_N-\mathbf1\mathbf1^T/N,\qquad Q\left[(I_t/N)Z\mathbf1+\mathbf e\right]=\mathbf0.\tag{5}
$$

<a id="fig-common_terminal"></a>
![Fig. 5](../../../panels/en/common_terminal.png)

<p align="center">Fig. 5. Multistrand common terminals and return.</p>

Strands are insulated along their paths and connected in parallel at both ends; their phasor currents follow from the common voltage and total-current constraints. The coupling matrix Z and excitation term e contain the impedance and field contributions retained by the model. The controlled return carries the opposite total current and has its own terminal field. Known inputs and unknown currents and voltage are identified.

<a id="fig-coax640_currents"></a>
![Fig. 6](../../../composites/en/coax640_currents.png)

<p align="center">Fig. 6. 640-strand common-terminal complex current sharing.</p>

(a) Magnitude; (b) phase, ordered by physical strand identity. A dashed line marks the comparison reference It/N. Magnitude and phase use identical physical strand numbering.

<a id="fig-coax640_fields"></a>
![Fig. 7](../../../composites/en/coax640_fields.png)

<p align="center">Fig. 7. 640-strand two-dimensional cross-sectional current density.</p>

(a) RMS magnitude; (b) phase, with material markers identifying strands. Current is reconstructed as Jz=σ(v−u) from original nodal and terminal fields. Independent power uses linear-triangle mass integration, while visualization samples cell centers.

<a id="fig-coax640_mesh"></a>
![Fig. 8](../../../panels/en/coax640_mesh.png)

<p align="center">Fig. 8. 640-strand mesh and boundary sensitivities.</p>

Mesh, return, and exterior tests each vary one factor. Variation is normalized from resistance differences between the specified adjacent cases. Mesh, return distance, and exterior size use separate sequences.
<a id="references"></a>
## References
