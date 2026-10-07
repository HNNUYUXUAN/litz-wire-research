# Litz-Wire Modeling and Numerical Verification: Comprehensive Research Report · 03 Round-Wire Analysis and Two-Dimensional Calibration

Miao Yuxuan · Huainan Normal University

[Merged manuscript](report_en.md#chapter-03)

<a id="chapter-03"></a>
## 03 Round-Wire Analysis and Two-Dimensional Calibration

<a id="03.round_derivation.heading"></a>
### Round Derivation

The axial current in a round wire satisfies (1/r)d(r dJz/dr)/dr=κ²Jz. Regularity at the axis selects I₀(κr). The identity ∫₀ᵃ rI₀(κr)dr=aI₁(κa)/κ together with the total-current constraint determines the normalization. The surface axial electric field divided by total current gives the internal impedance; its real part is checked by an independent Joule integral. Thus the derivation connects analytical shape, normalization, and power.

<a id="03.analytic.heading"></a>
### Round-Wire Analysis and Independent Two-Dimensional Calibration

The long straight round-wire internal solution uses modified Bessel functions [(3)](report_en.md#E03). At 200 kHz, the skin depth is 0.147771655 mm, producing pronounced surface concentration relative to the 1 mm radius. Frozen analytical values are 5.488101486 mΩ/m DC resistance, 20.016203628 mΩ/m AC resistance, a ratio of 3.647199980, and loss of 8.006481451 W/m. This internal impedance excludes the external inductance determined by the return path. Radial phase retains the original complex phasor and is displayed with a continuous nearest-neighbor 360° lift; unwrapping changes the display, not the underlying data.

Independent two-dimensional disk diffusion uses 353, 1389, and 5573 nodes and is normalized by total complex current. The finest relative AC-resistance error against the analytical reference is 1.79233×10⁻⁶, and the power-integral discrepancy is 3.06800×10⁻⁶. These results support discretization and normalization for the isolated internal-field problem. Its boundary conditions differ from a finite three-dimensional end region, so this error cannot be transferred directly to that problem. The analytical cross-sectional image is formed by linear interpolation of radial analytical magnitudes followed by an axisymmetric mapping.

<a id="E03"></a>
$$
\delta=(\pi f\mu\sigma)^{-1/2},\quad\kappa=(1+j)/\delta,\quad J_z(r)=\frac{I_t\kappa I_0(\kappa r)}{2\pi a I_1(\kappa a)},\quad z_{\mathrm{int}}=\frac{\kappa I_0(\kappa a)}{2\pi a\sigma I_1(\kappa a)}.\tag{3}
$$

<a id="fig-q1_profile"></a>
![Fig. 2](../../../composites/en/q1_profile.png)

<p align="center">Fig. 2. Round-wire radial current magnitude and phase.</p>

The copper conductor has diameter 2 mm and carries 20 A RMS at 200 kHz. (a) RMS magnitude; (b) continuously displayed phase. Phase is displayed with a continuous radial lift, while magnitude retains RMS normalization. Radial samples come from preserved Bessel analytical data.

<a id="fig-q1_cross_section"></a>
![Fig. 3](../../../panels/en/q1_cross_section.png)

<p align="center">Fig. 3. Analytical round-wire cross-sectional magnitude.</p>

The copper conductor has diameter 2 mm and carries 20 A RMS at 200 kHz. The color scale represents axial RMS current density. Radial samples are linearly interpolated and mapped axisymmetrically. Coordinates are displayed in millimetres and current density in A/mm².

<a id="fig-q1_fem_error"></a>
![Fig. 4](../../../panels/en/q1_fem_error.png)

<p align="center">Fig. 4. Round-wire two-dimensional calibration errors.</p>

The copper conductor has diameter 2 mm and carries 20 A RMS at 200 kHz. Three grids and independent power integrals concern the same internal-field problem. Resistance is referenced to the internal Bessel solution of the same round wire. Power is evaluated by independent integration over the material region.
<a id="references"></a>
## References
