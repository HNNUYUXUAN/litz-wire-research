<!-- id: A.report_derivation.heading -->
## Analytical Normalization, Circuit Constraints, and Element Integrals

<!-- id: A.report_derivation.p1 -->
Round-wire normalization first requires 2π∫₀ᵃ r Jz(r) dr=It. The identity d[r I₁(κr)]/dr=κr I₀(κr) then gives the normalization denominator. Dividing the boundary axial electric field Jz(a)/σ by It yields the internal impedance per unit length. The independent Joule integral is compared with |It|² Re(zint) under the RMS convention. High-precision quadrature error checks only the stated analytical formula; finite ends, external return inductance, temperature changes, and insulation are not included in that analytical accuracy.

<!-- id: A.report_derivation.p2 -->
Linear-triangle recovery uses the actual physical area aT. With nodal eₖ=v−uₖ, complex element current is σaTΣeₖ/3 and Joule power is σaT[Σ|eₖ|²+|Σeₖ|²]/12. The latter follows from the consistent mass matrix with diagonal coefficient two and off-diagonal coefficient one. Original coordinates are scaled by 0.001 m, so area carries the square of that scale; conversion to millimetres for display does not change integration. Material markers distinguish individual strands, return, and air, and the return uses its own v.

<!-- id: A.report_derivation.p3 -->
Necessity and sufficiency of the common-terminal criterion depend on the same linear system and uniqueness of its solution. Necessity follows by substituting equal currents into the voltage equation. Sufficiency follows because a vector removed by Q can be represented as V1 and then satisfies the augmented system together with total current. Conductor contacts, additional terminal impedances, nonlinear material, or a missing induced term change that system. Reuse of the criterion in a new model therefore begins by reconstructing Z, e, and the constraints, rather than copying an earlier conclusion.

<!-- id: A.sharing_derivation.heading -->
## Sharing Derivation

<!-- id: A.sharing_derivation.p1 -->
Sufficiency of the sharing criterion follows from uniqueness of the port solution. If the projection condition holds, every component of (It/N)Z1+e is equal, so a common voltage exists for which the equal-current vector satisfies both the port equations and the total-current constraint. Necessity follows by substitution of an existing equal-current solution. Numerical sharing is assessed using normalized complex-current deviation, with magnitude and phase reported to retain the information in phasor addition.
