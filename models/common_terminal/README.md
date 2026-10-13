# Common-terminal current sharing

Miao Yuxuan · Huainan Normal University

## Model and assumptions

Zi+e=V1; 1ᵀi=It

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Change strand count or return geometry; inspect complex strand currents and input/loss balance.

## Run the tutorial

```powershell
litz-research run coax --case tutorial --parameters models/common_terminal/examples/tutorial.json --run-id common_terminal_example_01
```

[Interactive Notebook](notebooks/common_terminal_en.nb)

## Result and acceptance

Read `results.json`, the checks, complex real/imaginary values and `results.wxf`. Execution status and physical acceptance describe different observations. A single tutorial mesh does not establish convergence.

## Research continuation

Start from the tutorial configuration. Vary one supported parameter at a time, save new run identities, check conservation and discretization sensitivity, then compare frozen evidence. Complete campaigns remain available through the stage runner.

## Sources

[P01](../../references/README.md), [P02](../../references/README.md)

## Derivation and interpretation

Insulated strands are connected in parallel only at the ends. The 2D Az weak form couples each conductive region to its unknown axial electric potential gradient. A controlled conducting coaxial return closes the transport problem.
Linearity yields a coupled block system for Az and the source/return voltage gradients. Impose ΣIi=20 A RMS and Ireturn=−20 A; every strand shares the source voltage gradient, while each complex Ii follows from integrating its solved current density.
Compute bundle and return Joule losses separately and compare their sum with input real power. Rac,bundle=Pbundle/|It|² is valid for this pure transport case. Seven strands demonstrate the method and do not meet Q2 copper area.

## Historical evidence

data/evidence/v1.0.0-rc.1/; litz-research data fetch common-terminal
