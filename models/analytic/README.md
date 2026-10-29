# Round-wire analytical calibration

Miao Yuxuan · Huainan Normal University

## Model and assumptions

∇²Ez−jωμσEz=0; Zint=κ I0(κa)/(2πaσ I1(κa))

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Change frequency/current; compare independent current and Joule integrals.

## Save inputs and execute

Run from the project root. Copy and edit the parameter file and choose a new run ID. The CLI validates parameter fields; save source and inputs before formal execution.

[Parameter file](examples/tutorial.json)

```bash
litz-research models wolfram-analytic
litz-research run wolfram-analytic --case tutorial --parameters models/analytic/examples/tutorial.json --run-id analytic_example_01 --dry-run
litz-research run wolfram-analytic --case tutorial --parameters models/analytic/examples/tutorial.json --run-id analytic_example_01
```

Use the installed `litz-research` command, or replace it with `.conda/project/python.exe -m litz_research.cli`.

## Asynchronous jobs and recovery

```bash
litz-research jobs submit wolfram-analytic --case tutorial --parameters models/analytic/examples/tutorial.json --run-id analytic_example_01
litz-research jobs status analytic_example_01
```

The synchronous and asynchronous examples are two ways to execute the same task. Choose one and assign a unique run ID. Cancel with `litz-research jobs cancel analytic_example_01`. Before resuming, verify input and source identities; use `jobs resume --help` to assign a linked new run ID.

## Results and acceptance

Inspect `execution_status`, `physical_acceptance_status`, `checks`, `scope` and parameters in `outputs/analytic_example_01/results.json`. Complex values retain real and imaginary parts; routes with native results also save `results.wxf`. One tutorial mesh does not establish convergence.

Tasks use at most eight logical processors and 24 GiB memory, retaining 8 GiB system reserve. Only task-created processes with matching creation identities are managed.

## Derivation and interpretation

For a homogeneous, long cylindrical conductor, symmetry leaves Ez(r) and Jz=σEz. Combining Ampère and Faraday laws with exp(+jωt) gives (1/r)d(r dEz/dr)/dr=jωμσEz. The regular solution is C I0(κr), κ²=jωμσ.
Normalize C using 2π∫Jz r dr=It. The terminal voltage gradient gives Zint=κ I0(κa)/(2πaσ I1(κa)). Independently integrate ∫|J|²/σ dA and compare with |It|² Re Zint. RMS phasors introduce no extra factor 1/2.
As κa→0, I0→1 and I1→κa/2, giving Rdc=1/(σπa²). The model excludes end effects and return-path external inductance. Q1 uses a=1 mm and remains a calibration case.

## Continue the research

Change one supported parameter at a time, save a new run identity, and check conservation, discretization, boundary and length sensitivity. Preserve comparable returns, actual arc lengths, copper volume and the traditional multilevel Litz baseline.

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## Historical evidence and sources

data/evidence/v1.0.0-rc.1/; litz-research data fetch analytic

[BESSEL](../../references/README.md)
