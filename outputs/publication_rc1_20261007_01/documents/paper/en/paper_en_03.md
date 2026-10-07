# Hierarchical Verification, Common-Terminal Current Sharing, and Finite-Length Longitudinal PEEC for Litz-Wire Modeling · 03 Results

Miao Yuxuan · Huainan Normal University

[Merged manuscript](paper_en.md#chapter-03)

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
<a id="references"></a>
## References
