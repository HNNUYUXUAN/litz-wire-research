# Finite-length longitudinal PEEC

Miao Yuxuan · Huainan Normal University

## Model and assumptions

Z=R+jωL; Zi=V1; 1ᵀi=It

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Change length or cross divisions; compare complex port constraints and power. The basis is longitudinal.

## Run the tutorial

```powershell
litz-research run peec --case tutorial --parameters models/peec/examples/tutorial.json --run-id peec_example_01
```

[Interactive Notebook](notebooks/peec_en.nb)

## Result and acceptance

Read `results.json`, the checks, complex real/imaginary values and `results.wxf`. Execution status and physical acceptance describe different observations. A single tutorial mesh does not establish convergence.

## Research continuation

Start from the tutorial configuration. Vary one supported parameter at a time, save new run identities, check conservation and discretization sensitivity, then compare frozen evidence. Complete campaigns remain available through the stage runner.

## Sources

[P03](../../references/README.md), [RUEHLI1974](../../references/README.md)

## Derivation and interpretation

Discretize the cross section into longitudinal current basis elements. Galerkin projection of the magnetoquasistatic integral equation gives Z=R+jωL, where R follows from conductivity and basis overlap and L contains finite-length mutual and self interactions.
Solve Zi=V1 and 1ᵀi=It simultaneously. The terminal voltage and complex currents are unknowns. Real input power must equal the quadratic resistive loss iᴴRi.
Vary cross-section divisions, longitudinal length and quadrature independently. This longitudinal basis omits general transverse current and end-region charge; it must not be presented as a full vector 3D conductor solution.

## Historical evidence

data/evidence/v1.0.0-rc.1/; litz-research data fetch peec
