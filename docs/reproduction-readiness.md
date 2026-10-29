# Reproduction readiness

[简体中文](reproduction-readiness.zh-CN.md) · [Automation](../automation/README.md)

Use `.conda/project` for CLI tasks and `.conda/ansys` for the pinned Ansys MCP runtime. Local executable paths and explicit server environments belong in the ignored `litz.config.json`. Record environment readiness, protocol success, solver execution and physical acceptance separately.

## Prepare and check configuration

```bash
python tools/CondaEnvironments.py rebuild project --prefix .conda/project
python tools/CondaEnvironments.py rebuild ansys --prefix .conda/ansys
.conda/project/python.exe -m litz_research automation configure --output build/client-config --ansys-python .conda/ansys/python.exe
```

Use the [pinned Ansys installation](../automation/mcp/ansys/README.md), reusing a healthy environment when available. Merge generated `mcp.json` entries from `mcpServers` into local `mcp_servers`, and merge the matching TOML into the desktop client while preserving unrelated settings. Configure `tools.python`, `ansys_python`, `ansysedt`, `wolfram_kernel`, `wolframscript` and `powershell` locally. Do not commit machine paths.

Explicit Ansys startup settings include UTF-8 Python pipes, Windows `APPDATA`, a verified `ANSYSEMSV_ROOTxxx` or `ANSYSEM_ROOTxxx`, and the matching edition. Preserve the licensed user's Wolfram directories. Both servers receive `LITZ_PROJECT`; compatibility adapters use `LITZ_PYTHON`. The generator copies relevant settings only. `pip check` alone does not establish import compatibility or agreement with the lock files. See [environment rebuilding](../automation/environments/README.md) for locks, existing-prefix verification and the Miniconda executable option.

## Before a new study

The following commands use Git Bash and fresh run IDs:

```bash
stamp=$(date +%Y%m%d_%H%M%S)
py=.conda/project/python.exe
"$py" -m litz_research automation readiness --run-id "ready_${stamp}" --client-config "$USERPROFILE/.codex/config.toml"
```

Require exit code zero, `readiness_status=passed_preflight` and no `failed_checks`. The saved report checks imports, dependency locks, upstream source identity, explicit server configuration, desktop parity, portable source tests, route inputs and the memory reserve. Add `--verify-data` after restoring data or migrating storage to verify dataset content hashes.

After runtime or configuration changes, verify fresh MCP processes without inherited application variables:

```bash
"$py" -m litz_research automation probe ansys --run-id "ansys_probe_${stamp}" --clean-environment
"$py" -m litz_research automation probe wolfram --run-id "wolfram_probe_${stamp}" --clean-environment
```

These probes retain basic system variables and supply application settings from the saved configuration. Missing AEDT installations and failed/empty Wolfram test reports fail the probe even when the tool transport returns success. Inspect actual tool events and stderr. A process terminated after a durable completion receipt can have a nonzero OS exit code; inspect `completion_receipt_observed` and `cleanup_reason` too. Existing MCP processes need a client reload to receive changed environment settings.

## Validate small cases before campaigns

```bash
"$py" -m litz_research run analytic --case tutorial --run-id "analytic_${stamp}"
"$py" -m litz_research jobs submit peec --case tutorial --run-id "peec_${stamp}"
"$py" -m litz_research jobs status "peec_${stamp}"
"$py" -m litz_research jobs submit ansys --case maxwell-seven --run-id "maxwell_${stamp}"
"$py" -m litz_research jobs status "maxwell_${stamp}"
```

Use `jobs submit/status/cancel/resume` for long runs. `running` with `worker_status=finishing` means solver results exist but worker/session cleanup is still underway. Wait for final status before restarting. Formal runs preserve input and source identities, dependency locks, resource observations and result records.

The [text research entries](research-entry-migration.json) map each route to its parameters and CLI. Publication compilation and visual review follow the [current manuscript workflow](../manuscript/README.md).

## Scientific scope

Readiness does not certify a physical model. A one-pass seven-strand Maxwell run checks its port/power scope; ranking still requires numerical uncertainty and mesh, boundary and length studies. The A–φ diagnostic reproduces retained potential/gauge failures. Keep these failures visible.

Use SI, exp(+jωt), RMS and copper at 20 °C. Q1's 2 mm diameter is a calibration; final Q2 nominal copper area must be at least 5 mm², with traditional multilevel Litz as the strong baseline. See the selected route README and [acceptance criteria](../tests/ACCEPTANCE.md).
