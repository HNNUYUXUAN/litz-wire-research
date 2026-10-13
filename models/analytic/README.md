# Round-wire analytical calibration

Miao Yuxuan · Huainan Normal University

## Model and assumptions

∇²Ez−jωμσEz=0; Zint=κ I0(κa)/(2πaσ I1(κa))

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Change frequency/current; compare independent current and Joule integrals.

## Run the tutorial

```powershell
litz-research run wolfram-analytic --case tutorial --parameters models/analytic/examples/tutorial.json --run-id analytic_example_01
```

[Interactive Notebook](notebooks/analytic_en.nb)

## Result and acceptance

Read `results.json`, the checks, complex real/imaginary values and `results.wxf`. Execution status and physical acceptance describe different observations. A single tutorial mesh does not establish convergence.

## Research continuation

Start from the tutorial configuration. Vary one supported parameter at a time, save new run identities, check conservation and discretization sensitivity, then compare frozen evidence. Complete campaigns remain available through the stage runner.

## Sources

[BESSEL](../../references/README.md)

## Derivation and interpretation

For a homogeneous, long cylindrical conductor, symmetry leaves Ez(r) and Jz=σEz. Combining Ampère and Faraday laws with exp(+jωt) gives (1/r)d(r dEz/dr)/dr=jωμσEz. The regular solution is C I0(κr), κ²=jωμσ.
Normalize C using 2π∫Jz r dr=It. The terminal voltage gradient gives Zint=κ I0(κa)/(2πaσ I1(κa)). Independently integrate ∫|J|²/σ dA and compare with |It|² Re Zint. RMS phasors introduce no extra factor 1/2.
As κa→0, I0→1 and I1→κa/2, giving Rdc=1/(σπa²). The model excludes end effects and return-path external inductance. Q1 uses a=1 mm and remains a calibration case.

## Historical evidence

data/evidence/v1.0.0-rc.1/; litz-research data fetch analytic
