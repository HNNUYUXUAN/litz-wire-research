# Vector RT0 volume PEEC

Miao Yuxuan · Huainan Normal University

## Model and assumptions

(R+jωL)i+e=Cᵀv; Ci=b

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Choose field or transport excitation. The field case has 1 mT RMS imposed Bz and zero net transport.

## Run the tutorial

```powershell
litz-research run rt0 --case tutorial --parameters models/rt0/examples/tutorial.json --run-id rt0_example_01
```

[Interactive Notebook](notebooks/rt0_en.nb)

## Result and acceptance

Read `results.json`, the checks, complex real/imaginary values and `results.wxf`. Execution status and physical acceptance describe different observations. A single tutorial mesh does not establish convergence.

## Research continuation

Start from the tutorial configuration. Vary one supported parameter at a time, save new run identities, check conservation and discretization sensitivity, then compare frozen evidence. Complete campaigns remain available through the stage runner.

## Sources

[P03](../../references/README.md), [RUEHLI1974](../../references/README.md), [RT1977](../../references/README.md), [GMRES1986](../../references/README.md)

## Derivation and interpretation

Lowest-order Raviart–Thomas face-flux degrees of freedom represent a vector current field with cellwise divergence. Adjacent cells share oriented face fluxes; the incidence matrix C enforces discrete current continuity.
The mixed PEEC system is (R+jωL)i+e=Cᵀv with Ci=b. In the imposed-field tutorial Bz=1 mT RMS and net transport is zero; calculate dissipated power from the reconstructed current and resistive quadratic form.
Check the true linear residual, continuity, quadrature and spatial sensitivity. Imposed-field loss is a diagnostic observable; dividing it by a separate transport current squared would not define intrinsic conductor resistance.

## Historical evidence

data/evidence/v1.0.0-rc.1/; litz-research data fetch rt0
