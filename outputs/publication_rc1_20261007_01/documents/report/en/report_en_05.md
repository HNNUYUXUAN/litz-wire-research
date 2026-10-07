# Litz-Wire Modeling and Numerical Verification: Comprehensive Research Report · 05 Transposition Models, Real Geometry, and Equal-Copper Comparisons

Miao Yuxuan · Huainan Normal University

[Merged manuscript](report_en.md#chapter-05)

<a id="chapter-05"></a>
## 05 Transposition Models, Real Geometry, and Equal-Copper Comparisons

<a id="05.geometry.heading"></a>
### Geometry, Actual Arc Length, and Discrete Transposition

Archived straight, single-level, traditional multilevel, and cross-layer centerlines support checks of physical strand identity, period, gap, curvature, arc length, and copper volume. Axial sampling at 400, 800, and 1600 segments and 60 geometry checks support numerical consistency of these quantities; the historical wrapper exit and the unrecorded native kernel exit retain their original status. The 24-strand specimen with 0.100 mm copper diameter has only about 0.1885 mm² nominal copper area. It illustrates construction and is not a final bundle satisfying the 5 mm² requirement. Three-dimensional material, lighting, and rotatable views are reading aids.

The current DTM/iDTM demonstration uses additive discrete blocks [(6)](report_en.md#E06). Reordering the same weighted impedance blocks does not change their sum. Equal sharing in that implementation therefore does not prove the equivalence of distinct realistic transposition paths or the superiority of a cross-layer structure over traditional multilevel Litz. Comparison with [1, 2] should examine longitudinal transposition, noncommuting hierarchical operations, local-field assumptions, and terminals rather than borrowing the method name alone. Geometric fairness, model adequacy, and performance improvement are three questions requiring separate evidence.

<a id="05.dtm_derivation.heading"></a>
### Dtm Derivation

Let Ps map fixed physical strand identities to spatial positions in section s. The local current is Ps i and the voltage in identity coordinates is PsᵀZsPs i. Summation over series segments Δzs yields the total impedance. Position permutation and current identity therefore have separate records; K, 2K, and 4K segmentation checks concern the same paths and physical strands. Period, gap, and arc-length checks constrain geometric feasibility and copper usage separately.

<a id="05.report_geometry.heading"></a>
### Geometry Sampling and Equal-Copper Checks

Trajectory recovery preserves physical strand IDs instead of renaming strands by cross-sectional order. Period checks distinguish position closure from identity permutation; gap and curvature checks use physical units, and arc length is integrated from sampled paths and compared with doubled sampling. Copper volume and DC resistance use actual strand lengths; the axial length is not substituted for every helical branch. Local cropping and display subsampling are recorded under the publication run, while complete original centerlines remain available.

Equal-copper comparisons identify circular nominal area, discretized actual area, and the outer envelope occupied by insulation. At the same nominal area, longer arc length increases copper volume per axial metre and the resistive path length. Geometric complexity itself supplies no evidence of electromagnetic improvement. The 640-strand candidate trajectories and 7/24-strand construction demonstrations serve different scales, and public materials should retain that distinction.

<a id="E06"></a>
$$
Z_{\mathrm{tot}}=\sum_{s=1}^{K}\Delta z_s P_s^T Z_s P_s.\tag{6}
$$

<a id="fig-geometry_comparison"></a>
![Fig. 9](../../../composites/en/geometry_comparison.png)

<p align="center">Fig. 9. Three-dimensional strand centerline structures.</p>

Panels show straight, single-level, local multilevel, and cross-layer structures. The 24-strand structures use a copper diameter of 0.100 mm, and the multilevel panel shows a 3 mm detail. Blue markers preserve selected physical strand identities.
<a id="references"></a>
## References

[1] Silvano Cruciani, Tommaso Campi, Francesca Maradei, Mauro Feliziani. Numerical Modeling of Litz Wires Based on Discrete Transpositions of Strands and 2-D Finite Element Analysis. IEEE TPEL 38(5):6710–6719, 2023. https://doi.org/10.1109/TPEL.2023.3240338

[2] Xinsheng Zhang, Fei Xiao, Ruitian Wang, Shunjun Chen, Xuexin Fan, Xin Li. AC Impedance Modeling of Composite Litz Wire With Nonideal Transposition Based on Improved Discrete Transposition Model. IEEE TPEL 41(7):11003–11019, 2026. https://doi.org/10.1109/TPEL.2026.3661080
