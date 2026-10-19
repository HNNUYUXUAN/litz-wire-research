# Development

[简体中文](development.zh-CN.md) · [Contributing](../CONTRIBUTING.md)

## Source layout

`models/` owns the seven physical routes; `adapters/` connects Wolfram, Ansys and GPU execution; `automation/` supplies workflows, skills and MCP/client setup. `shared/` provides common numerical and path utilities. `python/litz_research/` implements the CLI, task management, evidence restoration and independent analytical model. `src/` retains compatibility entry points. Scholarly builders live in `tools/publication/`.

Use explicit parameter files and unique run IDs for new cases. Save source hashes, units, phasor conventions, materials, boundaries, elapsed time, actual exit status, execution status and physical acceptance. Complex quantities retain real and imaginary components. [Acceptance targets](../tests/ACCEPTANCE.md) define model-specific checks.

## Install the source interfaces

The source interfaces require Python 3.11 or later. CI is configured for Python 3.11 and 3.12 on Windows and Ubuntu; its job results report the combinations actually verified. Keep the checkout alongside the installed CLI: model sources, configuration and manifests are read from this repository.

Windows PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[automation]"
.venv/Scripts/python.exe -B tools/CheckSourceCheckout.py
```

Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[automation]'
.venv/bin/python -B tools/CheckSourceCheckout.py
```

In the following commands, `python` and `litz-research` refer to this environment. Use its executable paths directly or activate the environment in your shell.

## Select the validation scope

| Scope | Inputs and runtime | Verification |
| --- | --- | --- |
| Source checkout | Python and the `automation` extra | `python -B tools/CheckSourceCheckout.py` |
| Retained evidence | Selected datasets restored from the catalog | `litz-research data verify <dataset>` and the relevant evidence checks |
| Native model | Required Wolfram, Ansys or GPU runtime, license and case inputs | Route-specific execution, conservation and sensitivity checks |
| Publications | Frozen figure inputs, document dependencies, native Notebook frontend and LaTeX environment | Content, citation, compilation, frontend and rendered-page checks |

The source checker uses an explicit portable test list and temporary fixtures. It checks restoration integrity, parameter and process ownership rules, model discovery, references and current-publication metadata. It blocks subprocess and network starts and physical-solver calls. Save a machine-readable receipt with:

```text
python -B tools/CheckSourceCheckout.py --output outputs/ci/source-checkout.json
```

Additional tests live in `tests/`. Select tests for the implementation being changed after providing their documented optional dependencies and datasets. Full discovery includes native and frozen-data consumers; it is a broader operation than the source-only check. A source check establishes interface and metadata consistency; scientific conclusions depend on the applicable model validation.

## Configure native tools

The Ansys MCP server uses Python 3.12 or later in a separate environment, with the pinned dependencies and installation steps in [Ansys MCP](../automation/mcp/ansys/README.md). [Wolfram MCP](../automation/mcp/wolfram/README.md) records its upstream and probes. Model tutorials and campaigns are indexed in [Tool workflows](tool-workflows.md).

Executable lookup follows `LITZ_<TOOL>`, then `tools.<tool>` in local `litz.config.json`, then PATH. For example, use `LITZ_WOLFRAMSCRIPT`, `LITZ_XELATEX` or `LITZ_LATEXMK` to select an installation. Probe the actual environment with `litz-research doctor`; add `--kernel` when a bounded Wolfram version/arithmetic probe is appropriate.

Native research runs follow the budget of eight logical processors, 24 GiB task memory and an 8 GiB system free-memory reserve. License limits may be smaller. Manage only task-owned processes, keep interrupted-run records, and resume from verified source/input identities or create a linked new run.

## Maintain evidence and publications

`data/catalog.json` defines archive parts, content objects, dependencies and original paths. Restoration checks part, object and final-file hashes; offline restoration uses the same identities. Historical evidence remains under its versioned `data/evidence/` root. New runs go into `outputs/`. See [Datasets](datasets.md).

Paired Markdown chapters and `manuscript/publication.json` define three complete works. Equations, quantities, figure identities and per-work citation maps are shared across formats. Update `references/library.bib` and `references/sources.json` before rebuilding citation exports. [Editions](editions.md) describes dependencies and complete builds: Wolfram creates native Notebooks, while XeLaTeX and latexmk compile PDFs using locally installed SimSun and Times New Roman.

Maintain bilingual reader prose and the generators that produce its indexes. `docs/current-edition.json` identifies the current six manuscripts and their downloadable assets; historical publication records retain their original run identity. The publication ZIP for `publication_review_20261015_03` is a frozen build. Subsequent source maintenance has its own Git commit and checks, as explained in [Release preparation](release-preparation.md).
