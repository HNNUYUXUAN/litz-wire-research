# Ansys MCP and Maxwell workflow

Miao Yuxuan · Huainan Normal University

## Model and assumptions

Common terminal voltage and total RMS current

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Run resource preflight; execute the native seven-strand MCP example when Maxwell is available.

## Run the tutorial

```powershell
litz-research run ansys --case preflight --parameters adapters/ansys/examples/tutorial.json --run-id ansys_example_01
```

[Interactive Notebook](notebooks/ansys_en.nb)

## Result and acceptance

Read `results.json`, the checks, complex real/imaginary values and `results.wxf`. Execution status and physical acceptance describe different observations. A single tutorial mesh does not establish convergence.

## Research continuation

Start from the tutorial configuration. Vary one supported parameter at a time, save new run identities, check conservation and discretization sensitivity, then compare frozen evidence. Complete campaigns remain available through the stage runner.

## Sources

[PYAEDTMCP](../../references/README.md), [PYAEDT](../../references/README.md)

## Derivation and interpretation

This Notebook performs the resource preflight. The complete MCP case starts an owned Student gRPC Desktop, connects the upstream server, constructs seven voltage windings and a controlled return, and solves two linear bases plus a constrained final case.
AEDT voltage inputs are peak values; the adapter converts RMS inputs by √2 and reconstructs RMS complex currents and power. Maxwell CPython/PyAEDT execution differs from the embedded AEDT RunScript environment.
Inspect actual units, axial model depth, frequency, project contents, mesh statistics, complex strand currents and input/loss balance. A one-pass Student mesh supports only the explicitly reported comparison scope.

## Historical evidence

data/evidence/v1.0.0-rc.1/; litz-research data fetch ansys

## Shared asynchronous native case

```powershell
litz-research jobs submit ansys --case maxwell-seven --run-id maxwell_job_01
litz-research jobs status maxwell_job_01
litz-research jobs cancel maxwell_job_01
litz-research jobs resume maxwell_job_01 --new-run-id maxwell_job_02
```

The runner owns the Student session, records MCP discovery/calls and native results, and closes the owned process tree on cancellation. Restart verifies saved inputs/source and uses a new run. The Notebook preflight is the lightweight default.
