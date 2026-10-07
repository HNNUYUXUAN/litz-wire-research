# Hierarchical Verification, Common-Terminal Current Sharing, and Finite-Length Longitudinal PEEC for Litz-Wire Modeling · 04 Discussion

Miao Yuxuan · Huainan Normal University

[Merged manuscript](paper_en.md#chapter-04)

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
<a id="references"></a>
## References

[1] Silvano Cruciani, Tommaso Campi, Francesca Maradei, Mauro Feliziani. Numerical Modeling of Litz Wires Based on Discrete Transpositions of Strands and 2-D Finite Element Analysis. IEEE TPEL 38(5):6710–6719, 2023. https://doi.org/10.1109/TPEL.2023.3240338

[2] Xinsheng Zhang, Fei Xiao, Ruitian Wang, Shunjun Chen, Xuexin Fan, Xin Li. AC Impedance Modeling of Composite Litz Wire With Nonideal Transposition Based on Improved Discrete Transposition Model. IEEE TPEL 41(7):11003–11019, 2026. https://doi.org/10.1109/TPEL.2026.3661080

[3] Yueyin Wang, Wu Chen, Zhan Shen. Modeling of Litz Wire Winding AC Resistance Based on Improved Segmented Equivalent Circuit. IEEE TPEL 39(1):1135–1149, 2024. https://doi.org/10.1109/TPEL.2023.3321327

[5] Tamás Bakondi, Sándor Bilicz, Szabolcs Gyimóthy. Finite element modeling of eddy currents in a multiconductor system with quasi-2D symmetry. COMPEL 44(5):730–742, 2025. https://doi.org/10.1108/COMPEL-01-2025-0031

[6] David C. Meeker. An Improved Continuum Skin and Proximity Effect Model for Hexagonally Packed Wires. JCAM 236(18):4635–4644, 2012. https://doi.org/10.1016/j.cam.2012.04.009

[7] Korawich Niyomsatian, Johan Gyselinck, Ruth V. Sabariego. Closed-form complex permeability expression for proximity-effect homogenisation of litz-wire windings. IET SMT 14(3):287–291, 2020. https://doi.org/10.1049/iet-smt.2019.0377
