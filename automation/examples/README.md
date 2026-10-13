# Replay the actual research workflow

The six [execution records](verification.json) bind visible MCP events, saved code, inputs, solver files and scientific acceptance. Public event copies normalize machine paths and preserve all JSON numeric values. The complete attachment is restored by `litz-research data fetch automation-rc2`.

## Wolfram model, tests and Notebook

```powershell
python automation/examples/wolfram-calibration/build_sequence.py --run-id wolfram_study_01 --output build/wolfram-sequence.json
litz-research automation probe wolfram --run-id wolfram_protocol_01 --sequence build/wolfram-sequence.json
```

Create `build/` first. The live sequence discovers seven tools, invokes Context and Evaluator, executes the shared saved task runner, runs the independent WLT report, writes a native Notebook and reads it back. Open `outputs/wolfram_study_01/calibration.nb`; the bilingual route Notebooks provide the portable interactive tutorial.

## Native Maxwell through Ansys MCP

Configure the separate Ansys Python executable with `automation configure`. In one terminal, launch the owned Student session:

```powershell
& <Ansys-Python> adapters/ansys/OwnedAEDTSession.py --output outputs/aedt_owner_01 --timeout 1800
```

In a second terminal, read the emitted session receipt and run:

```powershell
python automation/examples/ansys-native/build_sequence.py --session outputs/aedt_owner_01/aedt_session.json --run-id maxwell_case_01 --output build/maxwell-sequence.json
litz-research automation probe ansys --run-id maxwell_protocol_01 --sequence build/maxwell-sequence.json
New-Item outputs/aedt_owner_01/stop_session -ItemType File
```

The runner explicitly owns the Student gRPC session. MCP checks the installation, connects, executes CPython/PyAEDT model code and reads model information. Two voltage bases determine the common source/return voltage for the final 20 A RMS solve. Inspect the saved project, actual depth/units/frequency, currents, mesh and power. Tool success and physical acceptance have separate records.

## Compare solvers, extend and diagnose

Run the matching Wolfram seven-strand case with `minimum_segments=42`, then `tools/CompareSevenStrand.py --wolfram-run <run> --ansys-run <run> --run-id <new-run>`. The recorded comparison observes current and resistance differences while retaining the one-pass Maxwell mesh limitation.

Use `litz-research run analytic --case frequency-sweep --run-id frequency_study_01`. The [actual extension diff](frequency-extension/code.patch) adds seven frequencies, independent current/power integrals, the DC limit and original-case regression.

The [diagnosis record](diagnosis/execution.json) preserves the real `1000mm` conversion failure returned as text by the upstream tool, the [repair diff](diagnosis/code.patch) and a successful new run. The [A–phi record](aphi-diagnostics/execution.json) reproduces field derivatives and retains the failed potential/gauge gates.

Use a new identity on every invocation. After a timeout, query the saved task or session before starting another solve. The task templates document the visible research request; records contain tool events and artifacts, without model-internal reasoning.
