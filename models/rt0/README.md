# Vector RT0 volume PEEC

Miao Yuxuan · Huainan Normal University

## Model and assumptions

(R+jωL)i+e=Cᵀv; Ci=b

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Choose field or transport excitation. The field case has 1 mT RMS imposed Bz and zero net transport.

## Save inputs and execute

Run from the project root. Copy and edit the parameter file and choose a new run ID. The CLI validates parameter fields; save source and inputs before formal execution.

[Parameter file](examples/tutorial.json)

```bash
litz-research models rt0
litz-research run rt0 --case tutorial --parameters models/rt0/examples/tutorial.json --run-id rt0_example_01 --dry-run
litz-research run rt0 --case tutorial --parameters models/rt0/examples/tutorial.json --run-id rt0_example_01
```

Use the installed `litz-research` command, or replace it with `.conda/project/python.exe -m litz_research.cli`.

## Asynchronous jobs and recovery

```bash
litz-research jobs submit rt0 --case tutorial --parameters models/rt0/examples/tutorial.json --run-id rt0_example_01
litz-research jobs status rt0_example_01
```

The synchronous and asynchronous examples are two ways to execute the same task. Choose one and assign a unique run ID. Cancel with `litz-research jobs cancel rt0_example_01`. Before resuming, verify input and source identities; use `jobs resume --help` to assign a linked new run ID.

## Results and acceptance

Inspect `execution_status`, `physical_acceptance_status`, `checks`, `scope` and parameters in `outputs/rt0_example_01/results.json`. Complex values retain real and imaginary parts; routes with native results also save `results.wxf`. One tutorial mesh does not establish convergence.

Tasks use at most eight logical processors and 24 GiB memory, retaining 8 GiB system reserve. Only task-created processes with matching creation identities are managed.

## Derivation and interpretation

Lowest-order Raviart–Thomas face-flux degrees of freedom represent a vector current field with cellwise divergence. Adjacent cells share oriented face fluxes; the incidence matrix C enforces discrete current continuity.
The mixed PEEC system is (R+jωL)i+e=Cᵀv with Ci=b. In the imposed-field tutorial Bz=1 mT RMS and net transport is zero; calculate dissipated power from the reconstructed current and resistive quadratic form.
Check the true linear residual, continuity, quadrature and spatial sensitivity. Imposed-field loss is a diagnostic observable; dividing it by a separate transport current squared would not define intrinsic conductor resistance.

## Continue the research

Change one supported parameter at a time, save a new run identity, and check conservation, discretization, boundary and length sensitivity. Preserve comparable returns, actual arc lengths, copper volume and the traditional multilevel Litz baseline.

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## Historical evidence and sources

data/evidence/v1.0.0-rc.1/; litz-research data fetch rt0

[P03](../../references/README.md), [RUEHLI1974](../../references/README.md), [RT1977](../../references/README.md), [GMRES1986](../../references/README.md)
