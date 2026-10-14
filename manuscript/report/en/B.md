<!-- id: B.triangle_derivation.heading -->
## Current and power integration on linear triangles

<!-- id: B.triangle_derivation.p1 -->
Complex current density in a linear triangle is interpolated as J=ΣₐNaJa. The area integral of each shape function is AT/3, giving the element's complex current directly. Joule loss uses the consistent mass matrix in {{eqref:E09}}. Material tags associate each element with a strand, return, or air, and areas are calculated after converting coordinates to metres. Material-wise current and loss sums are independently checked against the original field–circuit scalars.

<!-- id: B.report_rt0.heading -->
## RT0 Face Flux and Lightweight Field Recovery

<!-- id: B.report_rt0.p1 -->
Original RT0 face fluxes are stored by direction and integer grid identity. For each cell axis, opposing fluxes q− and q+ give the center component (q−+q+)/(2h²) and local resistive power [|q−|²+|q+|²+Re(q−*q+)]/(3σh). Summing all three axes and all cells recovers total loss. Faces omitted at insulating sides have structural zero flux in the original discretization; this zero is not an independently solved boundary-flux validation.

<!-- id: B.report_rt0.p2 -->
Publication postprocessing independently reconstructs complex center J for all 27648 cells and compares it with the original cell_fields.csv, while exact overlap integration checks archived loss. A section uses the actual discrete layer near the center and states its z coordinate rather than assuming that all samples lie exactly at 1 mm. The W/cm³ scale is obtained by multiplying SI loss density by 10⁻⁶. Vector sample identities and their common length scale are inspectable in the figure request and mapping data without an additional solver.

<!-- id: B.equation.E09 -->
{{equation:E09}}
