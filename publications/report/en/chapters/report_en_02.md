# Litz-Wire Modeling and Numerical Verification: Comprehensive Research Report · 02 Physical Conventions and Model Hierarchy

Miao Yuxuan · Huainan Normal University

[Merged manuscript](../README.md#chapter-02)

<a id="chapter-02"></a>
## 02 Physical Conventions and Model Hierarchy

<a id="02.conventions.heading"></a>
### Operating Conditions, Quantities, and Fair Comparisons

Calculations use SI units, exp(jωt), and RMS phasors. Copper at 20 °C has conductivity 5.8×10⁷ S/m and relative permeability one. The main transport condition is 200 kHz and 20 A RMS with no independent imposed field. Strands are insulated along their paths and connected in parallel at the ends. Every per-metre quantity refers to axial length; actual strand arc lengths are reported separately. A finite-segment terminal voltage V and the axial electric field used by a two-dimensional model have different units, so their length normalization must remain explicit.

The original Q1 conductor with diameter 2 mm is retained as an analytical calibration. Its copper area is 3.141593 mm² and its DC current density is 6.366198 A/mm², exceeding the 4 A/mm² constraint; it therefore does not satisfy the final design condition. Q2 requires at least 5 mm² nominal copper area. The ideal circular area of 640 strands of diameter 0.100 mm is 5.026548 mm², whereas the original two-dimensional 64-sided approximation has an area of approximately 5.018478 mm². Equal-copper references should use the actual chosen area to avoid interpreting an area-discretization difference as a purely electromagnetic improvement.

For unequal strand lengths, DC resistance follows from the sum of parallel conductances [(1)](../README.md#E01). Copper volume, arc-length growth, absolute AC resistance, its ratio to DC resistance, loss, and complex strand currents are all reported rather than reducing the comparison to one ratio. RMS Joule loss uses [(2)](../README.md#E02) without the one-half factor associated with peak phasors. With an independent imposed field, absorbed power includes work done by that excitation. RT0 imposed-field loss cannot be divided unconditionally by 20² and named intrinsic transport resistance. Equal nominal copper area also does not imply equal copper volume per axial metre.

<a id="02.maxwell.heading"></a>
### Maxwell

In the magnetoquasistatic approximation, conduction dominates displacement current and charge continuity gives ∇·J=0. With exp(jωt), Faraday’s law is ∇×E=−jωB and Ohm’s law is J=σE. Materials, excitation, return, and boundary conditions define a boundary-value problem. Mapping its comparable observables to the next discretization establishes the verification sequence used here.

<a id="02.hierarchy.heading"></a>
### Model Hierarchy and Verification Methods

The hierarchy is organized by unknowns and comparable observables. The analytical round wire supplies internal impedance and radial current for a homogeneous long straight conductor; two-dimensional diffusion verifies the same internal-field problem. The multistrand two-dimensional common-terminal model additionally retains intrastand fields, complex current sharing, and an explicit return, while omitting longitudinal transposition and finite end regions. Longitudinal PEEC retains a finite-length partial-inductance kernel and common-terminal constraints but lacks complete transverse current loops. The three-component RT0 imposed-field example tests a three-dimensional operator, continuity, and field absorption; it remains distinct from transport in curved Litz geometry.

Verification combines solver residuals, constraints, independent power evaluation, and parameter sensitivities. The retained targets are 10⁻⁸ for true linear residuals and common-terminal or total-current constraints, 0.1% for independent power balance, and 1% for relevant mesh, segmentation, boundary, and length changes. Analytical references and analytical current/power integrals have their own stricter targets. RT0 keeps a true GMRES residual target of 10⁻¹¹ and an integration sensitivity target of 0.1%; CPU/GPU matrix and complex-current comparisons use 10⁻¹⁰. These are definitions of the checks performed in this study, not a claim that every physical problem has already attained the same accuracy.

Evidence can be cross-compared only under shared assumptions; a conclusion does not propagate automatically along a diagram arrow. A small linear residual indicates that the assembled system was solved accurately but does not exclude omitted physics or an incorrect boundary. Power balance constrains consistency between the discretization and postprocessing, yet a conservative but inappropriate model may also balance power. Agreement between two levels limits variation under a specified perturbation; it is not an unconditional error bound or a statistical confidence interval. Execution status, numerical-check status, and physical applicability are therefore archived separately.

<a id="E01"></a>
$$
R_{\mathrm{dc}}=\left(\sum_{k=1}^{N}\frac{\sigma A_k}{\ell_k}\right)^{-1},\qquad V_{\mathrm{Cu}}=\sum_{k=1}^{N}A_k\ell_k.\tag{1}
$$

<a id="E02"></a>
$$
P_{\mathrm{Cu}}=\int_{\Omega_{\mathrm{Cu}}}|\mathbf J|^2/\sigma\,\mathrm d\Omega,\quad R_{\mathrm{ac}}=P_{\mathrm{Cu}}/|I_t|^2,\quad r_{\mathrm{ac}}=R_{\mathrm{ac}}/L_z.\tag{2}
$$
<a id="references"></a>
## References
