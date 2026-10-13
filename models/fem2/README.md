# Two-dimensional diffusion FEM

Miao Yuxuan · Huainan Normal University

## Model and assumptions

∇⊥²Ez−jωμσEz=0; Jz=σEz

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Change mesh_h; run at least three meshes before making a convergence claim.

## Run the tutorial

```powershell
litz-research run fem2 --case tutorial --parameters models/fem2/examples/tutorial.json --run-id fem2_example_01
```

[Interactive Notebook](notebooks/fem2_en.nb)

## Result and acceptance

Read `results.json`, the checks, complex real/imaginary values and `results.wxf`. Execution status and physical acceptance describe different observations. A single tutorial mesh does not establish convergence.

## Research continuation

Start from the tutorial configuration. Vary one supported parameter at a time, save new run identities, check conservation and discretization sensitivity, then compare frozen evidence. Complete campaigns remain available through the stage runner.

## Sources

[FEMDOC](../../references/README.md), [P04](../../references/README.md)

## Derivation and interpretation

The circular cross section solves ∇⊥²Ez−jωμσEz=0. A constant boundary field is normalized to the total complex current; the circle polygon, interpolation order and mesh size determine numerical error.
The weak form integrates ∇v·∇Ez+jωμσvEz over the domain, subject to the stated boundary value. Integrate the resulting current and Joule density independently and compare Rac with the Bessel solution.
This tutorial uses one mesh. Repeat at three or more decreasing h/a values and inspect boundary/polygon resolution before claiming accuracy; integral conservation alone does not bound field error.

## Historical evidence

data/evidence/v1.0.0-rc.1/; litz-research data fetch fem2
