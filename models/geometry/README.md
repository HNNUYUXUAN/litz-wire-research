# Geometry and transposition

Miao Yuxuan · Huainan Normal University

## Model and assumptions

ℓi=∫√(1+x′²+y′²) dz; Rdc=(ΣσAi/ℓi)⁻¹

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Change topology, pitch or length; inspect gaps, arc lengths and copper volume. Geometry is a model input.

## Run the tutorial

```powershell
litz-research run geometry --case tutorial --parameters models/geometry/examples/tutorial.json --run-id geometry_example_01
```

[Interactive Notebook](notebooks/geometry_en.nb)

## Result and acceptance

Read `results.json`, the checks, complex real/imaginary values and `results.wxf`. Execution status and physical acceptance describe different observations. A single tutorial mesh does not establish convergence.

## Research continuation

Start from the tutorial configuration. Vary one supported parameter at a time, save new run identities, check conservation and discretization sensitivity, then compare frozen evidence. Complete campaigns remain available through the stage runner.

## Sources

[P01](../../references/README.md), [N01](../../references/README.md)

## Derivation and interpretation

A topology maps a persistent strand identity to a centerline (xi(z),yi(z),z). The tutorial samples the path, evaluates surface gaps and integrates each arc length ℓi=∫√(1+x′i²+y′i²)dz.
For axially cut length L, copper volume is ΣAiℓi and common-terminal Rdc=(ΣσAi/ℓi)⁻¹. Equal nominal copper area does not remove arc-length growth or change terminal constraints.
Geometry supplies the subsequent field model. Performance ranking requires an independent electromagnetic solve, controlled return/end effects and numerical uncertainty, using traditional multilevel Litz as a strong baseline.

## Historical evidence

data/evidence/v1.0.0-rc.1/; litz-research data fetch geometry
