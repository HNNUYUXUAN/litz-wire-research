# Run a model and interpret its result

[简体中文](tool-workflows.zh-CN.md)

Start with the isolated round-wire analytical case. It needs Python and mpmath, and checks internal impedance, complex current and RMS power using independent integrals.

```powershell
litz-research models
litz-research doctor
litz-research run analytic --case tutorial --run-id analytic_example_01 --dry-run
litz-research run analytic --case tutorial --run-id analytic_example_01
```

Dry-run reports inputs, launch requirements and the intended directory. Execution writes to `outputs/analytic_example_01/`; reusing a run ID produces a diagnostic. Inspect `results.json`, including `source_model`, `execution_status`, `physical_acceptance_status`, values and checks. The 2 mm, 200 kHz, 20 A RMS case gives approximately 20.0162 mΩ/m and 8.00648 W/m. Its mean DC current density is 6.3662 A/mm², so it is an analytical calibration for Q1.

## Select the required scientific route

`litz-research models <model>` reports supported cases, workloads, sources and datasets. The [model map](method-evidence-map.md) connects analytical, FEM, common-terminal, geometry, PEEC, RT0 and A–φ implementations to their checks. Read the selected route guide before using a full campaign. Ansys and GPU adapters have separate runtime and license conditions.

## Long tasks

```powershell
litz-research jobs submit peec --case tutorial --run-id peec_job_01
litz-research jobs status peec_job_01
litz-research jobs cancel peec_job_01
litz-research jobs resume peec_job_01 --new-run-id peec_job_02
```

Query status after a client timeout. Cancellation targets owned processes. Tutorial resume verifies saved inputs and source and creates a linked restart; checkpoint recovery follows the individual route's capabilities. Read both execution and physical status before interpreting results.

## Diagnostics and continuation

`doctor` reports executable resolution, version commands, Python imports, fonts and resources. `doctor --kernel` also starts a bounded Wolfram arithmetic/version probe. A completed inspection means the report was produced; each capability has its own result. Connection, API, solver, resource and physical failures retain their actual evidence.

Choose an [automation workflow](../automation/README.md) to reproduce, extend, compare, diagnose or write results. Save changes before formal execution, retain original failures, and use a new run for revised inputs.
