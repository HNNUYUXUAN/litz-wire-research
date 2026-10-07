# Litz Wire Research

Layered models, numerical verification, and bilingual academic documents for Litz-wire research.

**Miao Yuxuan · Huainan Normal University**

[简体中文](README.zh-CN.md) · [Academic editions](docs/editions.md) · [Datasets](docs/datasets.md) · [Development](docs/development.md) · [Scientific conventions](docs/建模约定与解析基准.md) · [Acceptance criteria](tests/ACCEPTANCE.md)

## Start

Use Python 3.11 or later in a virtual environment. Run these commands from the repository root:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[documents,figures]"
litz-research doctor
litz-research run analytic --run-id analytical_example_01
litz-research data list
```

The Python example independently evaluates the round-wire Bessel solution, integrates complex current and Joule power, and checks twelve acceptance conditions. Each run writes parameters, results, diagnostics, and a radial profile to `outputs/<run-id>/`.

## Research scope

The modules cover round-wire analysis, two-dimensional FEM, common-terminal field–circuit coupling, strand geometry, finite-length longitudinal PEEC, imposed-field RT0, three-dimensional A–φ diagnostics, and Ansys and CPU/GPU comparisons. Results retain separate execution and physical acceptance states. The report discusses the scope and uncertainty of each model, including unresolved three-dimensional calibration and realistic transposition performance.

All calculations use SI units, RMS phasors and `exp(+jωt)`. The main copper case uses 200 kHz, 20 A RMS, conductivity 58 MS/m, relative permeability 1, and 20 °C. Strands are insulated along their paths and connected through common terminal voltages. The RT0 example has an independently imposed field and reports external-field loss.

## Datasets and scholarly editions

Version attachments contain the original scientific evidence, publication inputs, and complete academic files. `data/catalog.json` identifies each dataset and its SHA256-verified parts. Private candidate downloads use the existing `gh` authentication session.

```sh
litz-research data fetch publication-inputs
litz-research data verify publication-inputs
litz-research build --run-id publication_example_01 --stage all
```

Canonical bilingual Markdown is under `manuscript/`. The build produces complete reports and papers, chapter excerpts, native Wolfram Notebooks, LaTeX, and single-column and IEEE-style PDFs. Wolfram and XeLaTeX are required for the corresponding build stages. Run `litz-research doctor` for environment requirements; configure executable locations through `LITZ_WOLFRAMSCRIPT`, `LITZ_XELATEX`, `LITZ_BIBTEX`, and `LITZ_LATEXMK`, or `litz.config.json`.

Cached datasets support offline restoration with `data fetch <dataset> --offline --cache <directory>`. A missing attachment is reported with its dataset identity and download command. Data reading and document builds use archived evidence; model execution is selected explicitly through `run`.

## Development and citation

This version is a research tool snapshot intended for independent extension. Consult [development](docs/development.md) for module interfaces, tests, resource limits, and solver requirements. Scientific records and source mappings are documented in [provenance](provenance/README.md). Citation metadata is provided in [CITATION.cff](CITATION.cff).

Original software is licensed under MIT. Original text, figures, and data use CC BY 4.0. Notebook code cells follow MIT and their text and figures follow CC BY 4.0. Third-party material retains its own license; see [LICENSES](LICENSES/README.md) and the per-file provenance records.
