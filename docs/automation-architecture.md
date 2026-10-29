# Agent-driven modeling architecture

The reusable contribution is a closed research loop: question and scientific contract → agent workflow → MCP tools → saved source and bounded execution → independent acceptance → diagnosis or scholarly output. Litz provides numerical examples and explicit unresolved boundaries.

`automation/` contains workflows, installable research skills, harness configuration and real tool sequences. `adapters/` owns runtime connection and execution. `models/` contains scientific implementations; `shared/` contains numerical/path/display helpers. The shared Python task interface joins CLI and native Notebooks, and is invoked by the Wolfram MCP example. Ansys case maxwell-seven uses the same task submission/status/cancel/restart contract, owns its Student session, and invokes the native adapter through MCP and CPython/PyAEDT.

## Task and evidence contract

| Artifact | Observation |
| --- | --- |
| request.json / parameters.json | Explicit case, supported inputs, units and resource policy |
| run_manifest.json / source_snapshot | Saved source bytes and hashes before formal execution |
| environment.json / resource_samples.json | Actual runtime, CPU affinity, owned-process RAM and system reserve |
| mcp_events.jsonl / protocol_report.json | Initialization, discovery, arguments, results and semantic API errors |
| results.json / results.wxf | Structured scientific values and native numerical/graphics objects |
| checks / test report | Tolerance, actual value, scope and pass/fail state |
| parent ticket / code.patch | Verified restart linkage or actual before/after source change |

The runner constrains its owned tree to eight logical processors, monitors 24 GiB task RAM and an 8 GiB system reserve, and bounds execution time. Ansys additionally owns an explicit Student PID/session and requests four solver cores. Full campaigns should run serially. Process cleanup is bound to creation identity, never executable-name selection.

## Long tasks and recovery

`jobs submit` returns a run ID. `jobs status` reads the saved task; `jobs cancel` requests cancellation. Tutorial recovery verifies the saved request and source snapshot, then restarts saved inputs under a linked new ID. Changed current source is explicitly listed. Full numerical campaigns retain their own documented checkpoints; tutorial restart does not pretend to recover unsupported solver state.

Connection, tool execution, solver execution and physical acceptance are separate. An API can return an error string with isError=false; the probe checks both. Budget exhaustion, interruption, solver failure and failed conservation retain their actual states. A frontend save receipt marks completed Notebook work before the supervisor releases lingering owned helpers, and records their actual process exit code.

## Scientific and source gates

SI, exp(+jωt), RMS and the fixed copper/temperature conditions apply throughout. Common-terminal voltage and total current determine complex strand currents. Geometry, external-field loss and transport resistance have distinct interpretations. A–phi sampling changes reuse original fields; gauge failures remain failures. Rankings require gains exceeding relevant numerical uncertainty.

[Method-to-evidence map](method-evidence-map.md), [actual cases](../automation/examples/verification.json), [reference library](../references/README.md) and [Chinese explanation](automation-architecture.zh-CN.md) provide the research continuation path. Codex with the standard MCP client bridge is verified end to end; other clients retain explicit untested status until their own records exist.
