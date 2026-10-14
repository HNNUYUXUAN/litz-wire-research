# Development

[简体中文](development.zh-CN.md)

## Code and scientific inputs

`models/` owns the seven physical routes; `adapters/` connects Wolfram, Ansys and GPU execution; `automation/` supplies workflows, skills and MCP/client setup. `shared/` provides common numerical and path utilities. `python/litz_research/` supplies the CLI, task management, data restoration and independent analytical implementation. `src/` retains compatibility entry points. Scholarly builders live in `tools/publication/`.

New cases use explicit parameter files and unique run IDs. Record source hashes, units, phasor conventions, material and boundary conditions, actual exit status, execution status and physical acceptance. Complex values retain real and imaginary components. [Acceptance targets](../tests/ACCEPTANCE.md) define the checks appropriate to each model.

## Runtime

Python 3.11+ supports the base analytical and data interfaces. The Ansys MCP environment requires Python 3.12+ and its separate pinned dependency set. Document construction uses licensed Wolfram for native Notebooks, XeLaTeX and latexmk for PDFs, and locally installed SimSun and Times New Roman.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[documents,figures,automation,audit]"
.venv/Scripts/litz-research.exe doctor
```

Executable lookup follows `LITZ_<TOOL>`, then `tools.<tool>` in local `litz.config.json`, then PATH. For example, set `LITZ_WOLFRAMSCRIPT`, `LITZ_XELATEX` or `LITZ_LATEXMK` for an explicitly selected installation. The resource policy is eight logical processors, 24 GiB task memory and an 8 GiB system free-memory reserve; solver licenses can impose smaller limits.

## Verification and manuscript work

Use focused tests for changes to physical equations, port constraints, power integration, data identity or process ownership. Python tests are discovered with `python -m unittest discover -s tests`; optional scientific dependencies and retained datasets are documented by the affected tests and route guides. New solver runs use their own IDs.

Paired Markdown chapters and `manuscript/publication.json` define three complete works. Equations, quantities, figure identities and per-work citation maps are shared across formats. The [publication guide](editions.md) explains builds, templates and portable packages. Bilingual reader prose is maintained in Markdown; index builders read it and generate inventories rather than replacing it with hard-coded drafts.

`data/catalog.json` specifies archive parts, content objects, dependencies and original relative paths. The restorer verifies part, object and file hashes before reuse. Offline restoration uses the same checks. Source records distinguish original files, metadata derivatives and new run artifacts.
