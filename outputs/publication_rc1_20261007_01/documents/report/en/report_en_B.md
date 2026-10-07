# Litz-Wire Modeling and Numerical Verification: Comprehensive Research Report · B Discretization and Postprocessing

Miao Yuxuan · Huainan Normal University

[Merged manuscript](report_en.md#chapter-B)

<a id="chapter-B"></a>
## B Discretization and Postprocessing

<a id="B.triangle_derivation.heading"></a>
### Triangle Derivation

On a linear triangle, J=ΣₐNaJa. Current integration uses A/3 for each shape function. Joule integration uses the mass matrix and Joule expression in [(9)](report_en.md#E09). Material markers assign each cell to a strand, the return, or air. Coordinates are converted to metres before area evaluation, and the integrated power is independently compared with the archived scalar.

<a id="B.report_rt0.heading"></a>
### RT0 Face Flux and Lightweight Field Recovery

Original RT0 face fluxes are stored by direction and integer grid identity. For each cell axis, opposing fluxes q− and q+ give the center component (q−+q+)/(2h²) and local resistive power [|q−|²+|q+|²+Re(q−*q+)]/(3σh). Summing all three axes and all cells recovers total loss. Faces omitted at insulating sides have structural zero flux in the original discretization; this zero is not an independently solved boundary-flux validation.

Publication postprocessing independently reconstructs complex center J for all 27648 cells and compares it with the original cell_fields.csv, while exact overlap integration checks archived loss. A section uses the actual discrete layer near the center and states its z coordinate rather than assuming that all samples lie exactly at 1 mm. The W/cm³ scale is obtained by multiplying SI loss density by 10⁻⁶. Vector sample identities and their common length scale are inspectable in the figure request and mapping data without an additional solver.

<a id="E09"></a>
$$
M_T=\frac{A_T}{12}\begin{bmatrix}2&1&1\\1&2&1\\1&1&2\end{bmatrix},\qquad P_T=\mathbf J_T^H M_T\mathbf J_T/\sigma.\tag{9}
$$
<a id="references"></a>
## References
