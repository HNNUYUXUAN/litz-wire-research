# Hierarchical Verification, Common-Terminal Current Sharing, and Finite-Length Longitudinal PEEC for Litz-Wire Modeling · S1 Theory and Discretization

Miao Yuxuan · Huainan Normal University

[Merged manuscript](../README.md#chapter-S1)

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

On a linear triangle, J=ΣₐNaJa. Current integration uses A/3 for each shape function. Joule integration uses the mass matrix and Joule expression in [(8)](../README.md#E09). Material markers assign each cell to a strand, the return, or air. Coordinates are converted to metres before area evaluation, and the integrated power is independently compared with the archived scalar.

<a id="E06"></a>
$$
Z_{\mathrm{tot}}=\sum_{s=1}^{K}\Delta z_s P_s^T Z_s P_s.\tag{7}
$$

<a id="E09"></a>
$$
M_T=\frac{A_T}{12}\begin{bmatrix}2&1&1\\1&2&1\\1&1&2\end{bmatrix},\qquad P_T=\mathbf J_T^H M_T\mathbf J_T/\sigma.\tag{8}
$$
<a id="references"></a>
## References
