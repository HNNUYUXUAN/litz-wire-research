# Preserved A–φ field diagnostics

Miao Yuxuan · Huainan Normal University

## Model and assumptions

J=−σ(jωA+∇φ); ∇·J=0

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Read actual saved fields and reproduce J, phi and gauge residuals. Original field parameters remain visible.

## Run the tutorial

```powershell
litz-research run aphi --case diagnostic --parameters models/aphi/examples/tutorial.json --run-id aphi_example_01
```

[Interactive Notebook](notebooks/aphi_en.nb)

## Result and acceptance

Read `results.json`, the checks, complex real/imaginary values and `results.wxf`. Execution status and physical acceptance describe different observations. A single tutorial mesh does not establish convergence.

## Research continuation

Start from the tutorial configuration. Vary one supported parameter at a time, save new run identities, check conservation and discretization sensitivity, then compare frozen evidence. Complete campaigns remain available through the stage runner.

## Sources

[FEMDOC](../../references/README.md), [GMRES1986](../../references/README.md)

## Derivation and interpretation

Under exp(+jωt), reconstruct J=−σ(jωA+∇φ) from the original saved A and φ fields. Compare current conservation and normalized potential/gauge residuals using the exact preserved inputs.
This entry changes only diagnostic sampling density. It recomputes derivatives on saved fields and tests reproducibility against the original diagnostic quantities; it performs no new field solve.
The saved scalar-potential/gauge checks remain failed. Preserve mesh, excitation, gauge and boundary assumptions. Continue only after identifying a consistent formulation and passing conservation, gauge and mesh studies.

## Historical evidence

data/evidence/v1.0.0-rc.1/; litz-research data fetch aphi
