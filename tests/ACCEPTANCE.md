# Scientific and delivery acceptance

Execution status and physical acceptance are recorded separately. Each conclusion names its model, excitation, discretization and source run. Frozen route records retain both passing and unsuccessful cases.

| Check | Tolerance |
| --- | --- |
| Analytical reference values | Relative error ≤ 10⁻⁶ |
| Analytical complex-current and Joule-power integrals | Relative error ≤ 10⁻⁸ |
| Total complex current, common voltage, continuity, true linear residual | Relative error ≤ 10⁻⁸ |
| Independent power balance | Relative difference ≤ 0.1% |
| Rac, mesh, segmentation, boundary and length sensitivity | Relative change ≤ 1% |
| CPU/GPU same-matrix and complex-current comparison | Relative difference ≤ 10⁻¹⁰ |
| RT0 quadrature sensitivity | Relative difference ≤ 0.1% |
| A–φ current-density calibration | Relative error ≤ 1% |
| A–φ scalar-potential calibration | Error ≤ 10⁻⁸ |
| A–φ gauge residual | Residual ≤ 10⁻³ |

## Physical conventions

SI, exp(+jωt), RMS. Copper conductivity 58 MS/m, relative permeability 1, 200 kHz, 20 A RMS and 20 °C define the primary case. A 2 mm solid wire is the Q1 calibration and has Jdc ≈ 6.366 A/mm². Comparisons use actual equal copper area and axial length, with arc length and copper volume explicitly reported. Insulated strands share terminal voltage and total complex current; current per strand is an output of the constrained solve.

## Analytical calibration

Twelve checks cover skin depth, DC and AC resistance, internal reactance, resistance ratio, RMS power, independent complex-current and power integrals, positive low-frequency limit, passivity and phasor sign, RMS normalization and the Q1 current-density condition. Python and Wolfram implementations are independent. High-precision residuals describe numerical quadrature within the analytical model.

## Numerical routes

Two-dimensional calibration and the 640-strand common-terminal model have retained mesh, return and exterior-domain evidence. Larger coarse models supply scale-execution evidence. Longitudinal PEEC reports separate length and integration sensitivities and CPU/GPU comparisons within its retained longitudinal physics.

The imposed-field RT0 cuboid uses zero net transport, 200 kHz and 1 mT RMS. Its final consecutive spatial loss changes are 0.655090% and 0.362916%, with retained quadrature, constraint and power checks. Older dense-matrix memory refusals are separate records. This result concerns external-field loss and operator validation.

Three-dimensional A–φ diagnostics retain their actual potential, current and gauge acceptance. Ansys evidence distinguishes successful bounded scalar tests from interface failures and incomplete three-level sensitivities. Realistic transposition ranking, thermal predictions and experiments retain their stated research scope. Performance differences must exceed numerical uncertainty to support a ranking.

## Tool and archive validation

Unique run IDs, fresh-kernel execution, process ownership, resource guards and actual exit codes are checked. Dataset tests cover resumed transfer, corruption, archive membership, part reconstruction and full file hashes. Paths resolve relative to the project and are exercised in a directory containing spaces. Missing inputs identify the required dataset and command.

## Scholarly editions

Paired paragraphs, numbers, units, formulas, figure identities, references and chapter extraction agree across formats. All PDF outputs compile and render, with resolved references and embedded fonts. All formal Notebooks undergo frontend open/save/read and rendering; native three-dimensional figures undergo viewpoint roundtrip checks. Provenance binds source and output identities, including numerical checks for metadata derivatives.
