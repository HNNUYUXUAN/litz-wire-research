# Ansys MCP and Maxwell workflow

Miao Yuxuan · Huainan Normal University

## Model and assumptions

Common terminal voltage and total RMS current

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Run resource preflight; execute the native seven-strand MCP example when Maxwell is available.

## Save inputs and execute

Run from the project root. Copy and edit the parameter file and choose a new run ID. The CLI validates parameter fields; save source and inputs before formal execution.

[Parameter file](examples/tutorial.json)

```bash
litz-research models ansys
litz-research run ansys --case preflight --parameters adapters/ansys/examples/tutorial.json --run-id ansys_example_01 --dry-run
litz-research run ansys --case preflight --parameters adapters/ansys/examples/tutorial.json --run-id ansys_example_01
```

Use the installed `litz-research` command, or replace it with `.conda/project/python.exe -m litz_research.cli`.

## Asynchronous jobs and recovery

```bash
litz-research jobs submit ansys --case preflight --parameters adapters/ansys/examples/tutorial.json --run-id ansys_example_01
litz-research jobs status ansys_example_01
```

The synchronous and asynchronous examples are two ways to execute the same task. Choose one and assign a unique run ID. Cancel with `litz-research jobs cancel ansys_example_01`. Before resuming, verify input and source identities; use `jobs resume --help` to assign a linked new run ID.

## Results and acceptance

Inspect `execution_status`, `physical_acceptance_status`, `checks`, `scope` and parameters in `outputs/ansys_example_01/results.json`. Complex values retain real and imaginary parts; routes with native results also save `results.wxf`. One tutorial mesh does not establish convergence.

Tasks use at most eight logical processors and 24 GiB memory, retaining 8 GiB system reserve. Only task-created processes with matching creation identities are managed.

## Derivation and interpretation

This Notebook performs the resource preflight. The complete MCP case starts an owned Student gRPC Desktop, connects the upstream server, constructs seven voltage windings and a controlled return, and solves two linear bases plus a constrained final case.
AEDT voltage inputs are peak values; the adapter converts RMS inputs by √2 and reconstructs RMS complex currents and power. Maxwell CPython/PyAEDT execution differs from the embedded AEDT RunScript environment.
Inspect actual units, axial model depth, frequency, project contents, mesh statistics, complex strand currents and input/loss balance. A one-pass Student mesh supports only the explicitly reported comparison scope.

## Continue the research

Change one supported parameter at a time, save a new run identity, and check conservation, discretization, boundary and length sensitivity. Preserve comparable returns, actual arc lengths, copper volume and the traditional multilevel Litz baseline.

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## Historical evidence and sources

data/evidence/v1.0.0-rc.1/; litz-research data fetch ansys

[PYAEDTMCP](../../references/README.md), [PYAEDT](../../references/README.md)
