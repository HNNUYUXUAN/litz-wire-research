# Preserved A–φ field diagnostics

Miao Yuxuan · Huainan Normal University

## Model and assumptions

J=−σ(jωA+∇φ); ∇·J=0

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Read actual saved fields and reproduce J, phi and gauge residuals. Original field parameters remain visible.

## Save inputs and execute

Run from the project root. Copy and edit the parameter file and choose a new run ID. The CLI validates parameter fields; save source and inputs before formal execution.

[Parameter file](examples/tutorial.json)

```bash
litz-research models aphi
litz-research run aphi --case diagnostic --parameters models/aphi/examples/tutorial.json --run-id aphi_example_01 --dry-run
litz-research run aphi --case diagnostic --parameters models/aphi/examples/tutorial.json --run-id aphi_example_01
```

Use the installed `litz-research` command, or replace it with `.conda/project/python.exe -m litz_research.cli`.

## Asynchronous jobs and recovery

```bash
litz-research jobs submit aphi --case diagnostic --parameters models/aphi/examples/tutorial.json --run-id aphi_example_01
litz-research jobs status aphi_example_01
```

The synchronous and asynchronous examples are two ways to execute the same task. Choose one and assign a unique run ID. Cancel with `litz-research jobs cancel aphi_example_01`. Before resuming, verify input and source identities; use `jobs resume --help` to assign a linked new run ID.

## Results and acceptance

Inspect `execution_status`, `physical_acceptance_status`, `checks`, `scope` and parameters in `outputs/aphi_example_01/results.json`. Complex values retain real and imaginary parts; routes with native results also save `results.wxf`. One tutorial mesh does not establish convergence.

Tasks use at most eight logical processors and 24 GiB memory, retaining 8 GiB system reserve. Only task-created processes with matching creation identities are managed.

## Derivation and interpretation

Under exp(+jωt), reconstruct J=−σ(jωA+∇φ) from the original saved A and φ fields. Compare current conservation and normalized potential/gauge residuals using the exact preserved inputs.
This entry changes only diagnostic sampling density. It recomputes derivatives on saved fields and tests reproducibility against the original diagnostic quantities; it performs no new field solve.
The saved scalar-potential/gauge checks remain failed. Preserve mesh, excitation, gauge and boundary assumptions. Continue only after identifying a consistent formulation and passing conservation, gauge and mesh studies.

## Continue the research

Change one supported parameter at a time, save a new run identity, and check conservation, discretization, boundary and length sensitivity. Preserve comparable returns, actual arc lengths, copper volume and the traditional multilevel Litz baseline.

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## Historical evidence and sources

data/evidence/v1.0.0-rc.1/; litz-research data fetch aphi

[FEMDOC](../../references/README.md), [GMRES1986](../../references/README.md)
