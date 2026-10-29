# Finite-length longitudinal PEEC

Miao Yuxuan · Huainan Normal University

## Model and assumptions

Z=R+jωL; Zi=V1; 1ᵀi=It

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Change length or cross divisions; compare complex port constraints and power. The basis is longitudinal.

## Save inputs and execute

Run from the project root. Copy and edit the parameter file and choose a new run ID. The CLI validates parameter fields; save source and inputs before formal execution.

[Parameter file](examples/tutorial.json)

```bash
litz-research models peec
litz-research run peec --case tutorial --parameters models/peec/examples/tutorial.json --run-id peec_example_01 --dry-run
litz-research run peec --case tutorial --parameters models/peec/examples/tutorial.json --run-id peec_example_01
```

Use the installed `litz-research` command, or replace it with `.conda/project/python.exe -m litz_research.cli`.

## Asynchronous jobs and recovery

```bash
litz-research jobs submit peec --case tutorial --parameters models/peec/examples/tutorial.json --run-id peec_example_01
litz-research jobs status peec_example_01
```

The synchronous and asynchronous examples are two ways to execute the same task. Choose one and assign a unique run ID. Cancel with `litz-research jobs cancel peec_example_01`. Before resuming, verify input and source identities; use `jobs resume --help` to assign a linked new run ID.

## Results and acceptance

Inspect `execution_status`, `physical_acceptance_status`, `checks`, `scope` and parameters in `outputs/peec_example_01/results.json`. Complex values retain real and imaginary parts; routes with native results also save `results.wxf`. One tutorial mesh does not establish convergence.

Tasks use at most eight logical processors and 24 GiB memory, retaining 8 GiB system reserve. Only task-created processes with matching creation identities are managed.

## Derivation and interpretation

Discretize the cross section into longitudinal current basis elements. Galerkin projection of the magnetoquasistatic integral equation gives Z=R+jωL, where R follows from conductivity and basis overlap and L contains finite-length mutual and self interactions.
Solve Zi=V1 and 1ᵀi=It simultaneously. The terminal voltage and complex currents are unknowns. Real input power must equal the quadratic resistive loss iᴴRi.
Vary cross-section divisions, longitudinal length and quadrature independently. This longitudinal basis omits general transverse current and end-region charge; it must not be presented as a full vector 3D conductor solution.

## Continue the research

Change one supported parameter at a time, save a new run identity, and check conservation, discretization, boundary and length sensitivity. Preserve comparable returns, actual arc lengths, copper volume and the traditional multilevel Litz baseline.

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## Historical evidence and sources

data/evidence/v1.0.0-rc.1/; litz-research data fetch peec

[P03](../../references/README.md), [RUEHLI1974](../../references/README.md)
