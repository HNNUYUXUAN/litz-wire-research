# Model workflows and a first reproducible result

The first example computes the internal impedance of one isolated straight round copper wire. It uses Python and `mpmath`; the research checkout supplies its physical inputs. Run it before selecting a solver route.

## Install and run the analytical example

From the repository root:

```sh
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -e .
litz-research doctor
litz-research run analytic --run-id analytical_example_01 --dry-run
litz-research run analytic --run-id analytical_example_01
```

`--dry-run` reports the intended output directory, source inputs, workload, launch conditions and dataset commands. It leaves the output directory uncreated. Every execution uses a distinct `--run-id`; repeating an existing identity produces a diagnostic and exit code 1.

Read the result and its scope:

```sh
python -c "import json; from pathlib import Path; r=json.loads(Path('outputs/analytical_example_01/results.json').read_text(encoding='utf-8')); print(r['source_model']); print(r['physical_acceptance_status']); print(r['values']); print(r['diagnostics'])"
```

For the supplied 2 mm diameter, 200 kHz, 20 A RMS copper case, the expected internal AC resistance is approximately **20.0162 mΩ/m** and the Joule loss is **8.00648 W/m**. `results.json` records twelve checks, physical parameters, source hashes and integration errors. `radial_current_density.csv` stores radius in metres and complex current density as real and imaginary parts in A/m². The current and Joule-power integrals independently check the RMS phasor convention. The recorded average current density is approximately 6.3662 A/mm²; the 2 mm case serves as a calibration case with that explicit condition.

This example evaluates internal impedance per axial metre. Port reactance, return-path losses and finite-end redistribution belong to their corresponding field models.

## Discover routes before executing them

```sh
litz-research models
litz-research models peec
litz-research models rt0 --json
litz-research run peec --dry-run
```

`models` is the shared inventory for installed commands and expert scripts. An entry states its execution interface, workload, inputs, output, evidence datasets and scientific scope. The interface describes how to invoke the code; it is separate from physical acceptance.

| Model ID | Entry and workload | Inputs for a new execution | Archived evidence |
| --- | --- | --- | --- |
| `analytic` | Python Bessel calibration; light | `configs/reference_parameters.json`, `reference_values.json` | `analytic` |
| `wolfram-analytic` | Wolfram Bessel calibration and twelve tests; light | Source checkout, `tests/Q1Analytical.wlt` | `analytic` |
| `circuits` | Three common-terminal lumped-circuit examples; light | `src/stages/circuits.wl` | `common-terminal` |
| `geometry` | Sampled centrelines and additive DTM examples; light | `src/stages/geometry.wl` | `geometry` |
| `copper` | Equal-copper analytical/reduced predictions; light | `src/stages/copper.wl` | `geometry` |
| `fem2` | Round-wire 2D mesh campaign; field solve | Source checkout | `fem2` |
| `coax` | 2D common-terminal calibration plus coarse 640/1280/2560-strand scale attempts; large campaign | Source checkout | `common-terminal` |
| `coax640` | 640-strand mesh, return and outer-domain campaign; large field solve | Source checkout | `common-terminal` |
| `peec` | Longitudinal finite-length discretization; field solve | Source checkout | `peec` |
| `voxel` | Dense voxel/face-flux examples; field solve | Source checkout | `rt0` |
| `gpu` | GPU arithmetic, matrix-vector and synthetic solver comparisons | Wolfram GPU runtime and compatible device | `gpu` |
| `rt0` | Expert matrix-free imposed-field campaign | Source checkout, explicit case selection | `rt0` |
| `aphi` | Expert postprocessing of preserved A–φ fields | `aphi` dataset | `aphi` |
| `ansys` | Expert Q1 resource preflight, followed by gated Maxwell workflows | Q1 preflight uses the source checkout; 2D workflows use `ansys` and `research-records` | `ansys`, `research-records` |

The Python analytical entry is portable. The retained scientific process supervisor uses Windows PowerShell and a licensed Wolfram kernel. Ansys field execution uses Maxwell/PyAEDT. Archived evidence can be read independently of those solver installations.

```sh
litz-research data fetch peec
litz-research data verify peec
```

Evidence downloads preserve original relative paths and run identities beneath `data/evidence/v1.0.0-rc.1/`. A new model run writes to its own identity. For a complete cross-route regression suite, also fetch `research-records`; individual route archives serve their recorded runs and file mappings.

## Interpret environment diagnostics

```sh
litz-research doctor
litz-research doctor --kernel
```

`doctor` returns JSON. Its exit code 0 means the inspection completed; inspect each capability and diagnostic to decide which workflow is usable.

| Field | Observation | Next step |
| --- | --- | --- |
| `tools` | Configured executable resolution | Set `LITZ_<TOOL>` or `tools.<tool>` in `litz.config.json` when missing. |
| `versions` | Actual version command and exit code | Read `diagnostic_lines` if initialization fails. |
| `python_imports.mpmath` | Import in the active Python environment | The analytical route is ready when this probe passes. |
| `wolfram_kernel` | With `--kernel`: local kernel start, arithmetic and version | Run the analytical Wolfram checks next. Frontend rendering has its own document acceptance. |
| `python_imports.pyaedt` | Actual PyAEDT import | Install `python -m pip install -e ".[ansys]"` for this environment when needed. |
| `ansys_installation` | Desktop executable discovery, including Student installations | Field runs establish interface and license availability. |
| `gpu_driver` | Device name, driver and memory query through `nvidia-smi` | The GPU route separately validates Wolfram runtime and numerical agreement. |
| `fonts` | SimSun/Times New Roman font files on Windows | A document compile and rendered inspection establish embedded fonts and readability. |
| `actual_resources` | Available RAM and system reserve on Windows | Schedule a model within its preflight estimate and the recorded resource budget. |

The resource policy is eight logical processors, 24 GiB task memory and an 8 GiB system reserve. `run` constrains the process and passes the memory policy to its supervisor. Availability probes exercise versions, imports and simple arithmetic. A successful probe has the scope shown in its record.

## Expert workflows

Run these commands from the research checkout using its active Python environment. Read each workflow's configuration and output before scheduling a field solve.

### Matrix-free RT0 resource preflight

The model is a 1 × 1 × 2 mm cuboid at 200 kHz with a 1 mT RMS imposed field and zero net transport current. Its observable is external-field loss. Case names encode subdivision and quadrature order; for example, `rt0_n16_q14` contains 8192 cells. The configuration is `configs/prewrite_closure.json`.

The following PowerShell block evaluates resource estimates and restores the caller's preflight environment value:

```powershell
$previousPreflight = $env:LITZ_CLOSURE_PREFLIGHT_ONLY
$env:LITZ_CLOSURE_PREFLIGHT_ONLY = '1'
try {
    powershell -NoProfile -File src/RunNotebookStage.ps1 -Stage closure_rt0 -RunId rt0_preflight_01
} finally {
    $env:LITZ_CLOSURE_PREFLIGHT_ONLY = $previousPreflight
}
```

Inspect `outputs/rt0_preflight_01/cases/rt0_n16_q14/resource_preflight.json`. A planned solve selects `LITZ_CLOSURE_CASE_ID`, sets `LITZ_CLOSURE_MAX_WORKING_BYTES=25769803776` and `LITZ_CLOSURE_MIN_SYSTEM_FREE_BYTES=8589934592`, and uses a new run ID through `RunNotebookStage.ps1 -Stage closure_rt0`. Preflight mode must be cleared for that separate execution. Spatial and quadrature conclusions require the full comparison campaign recorded by the stage, including true residual and power checks.

### Preserved A–φ field diagnostics

```sh
litz-research data fetch aphi
litz-research data verify aphi
powershell -NoProfile -File src/RunNotebookStage.ps1 -Stage closure_fem3_diagnostics -RunId aphi_diagnostics_01
```

This stage reads the cylinder fields in `rerun_20261005_fem3_cylinder_report` and the manufactured-solution fields in `3d_20261005_fem3_mms_distinct`. It exports sampled derivatives and `diagnostic_summary.json`. The existing cylinder φ and gauge failures remain explicit. Loading and reconstructing fields requires Wolfram and sufficient memory; set the same task/system memory variables as for RT0 when invoking this expert supervisor directly. The underlying solver stages `fem3_mms` and `fem3_cylinder` are documented in their source files for further research.

### Maxwell resource preflight and evidence dependencies

```sh
python src/RunClosureAnsys.py --task preflight --case q1 --budget low --run-id ansys_preflight_01
```

The displayed command uses the Q1 configuration to estimate the mesh/resource campaign. It records `execution_status="preflight_only"` and `solver_started=false`. `--budget low` selects a 24 GiB task budget, 8 GiB system reserve and four solver cores. Actual field tasks require the Ansys extra and a licensed Maxwell installation.

```sh
litz-research data fetch ansys
litz-research data fetch research-records
python src/RunClosureAnsys.py --help
```

The 2D tasks read the seven-strand reference in `full_20261005_handoff/field_case_005/port_and_loss.json`, its geometry manifest, the retained native interface probe and the first 2D mesh record. The scripts use these identities to keep geometry and interface decisions reproducible. Inspect `closure_2d_config` and the command help before extending that workflow. Native Q1 progression uses the explicit `native_probe`, `native_coarse` and prerequisite-gated `native_suite` tasks. Student element limits and recorded interface failures remain part of each task's acceptance conditions.

## Read a scientific result

Start with `results.json`, then the model assumptions and test report. Interpret `source_model`, `execution_status` and `physical_acceptance_status` together. A process exit code is a software execution outcome; the physical state records the checks and scope that were established. A manufactured solution, an imposed-field cuboid and a common-terminal transport model answer different validation questions.

Use the dataset catalogue to locate and hash-check original files. Preserve real/imaginary current components and SI units through analysis; calculate amplitude and phase as derived quantities. A new result retains its parameter and source identities alongside its checks.

## Verification scope for this tool revision

On 2026-10-13, a separate source copy in a path containing spaces was installed into a fresh Python 3.12.10 virtual environment with `pip install -e .`. The installed command completed help, route discovery, analytical dry-run and execution, twelve analytical checks, and duplicate run-ID diagnostics. A local Wolfram 15.0 kernel completed the bounded arithmetic probe. The base Python environment correctly reported the optional PyAEDT import requirement. The Q1 Ansys resource preflight completed with `solver_started=false`.

Nine focused tests cover catalogue/source identity, expert-interface discovery, missing-source diagnostics, run-ID ownership, actual probe failures/timeouts, Student installation discovery, UTF-8 command output, diagnostic field compatibility and the first analytical CLI run in a path containing spaces. Their command is:

```sh
python -m unittest discover -s tests -p test_tool_experience.py -v
```

These checks establish the stated command and reading experience. Large FEM, RT0, A–φ solver and GPU results retain their existing scientific evidence and acceptance records.
