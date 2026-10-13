# Reading and first run

[简体中文](reading-guide.zh-CN.md) · [Home](../README.md) · [Complete editions and chapters](editions.md)

## Choose a reading path

| Purpose | Action | Requirements |
| --- | --- | --- |
| Understand the research argument | Open the Chinese or English paper Markdown from the home page | Access to the GitHub repository |
| Read complete figures and page layouts | Restore `academic-editions` and open a single-column PDF | Python, GitHub CLI and a PDF reader |
| Inspect native three-dimensional graphics | Open the matching `.nb` from the same dataset | A Wolfram frontend that reads Notebooks |
| Reproduce the isolated round-wire solution | Run the analytical example below | Python 3.11+ and mpmath |
| Extend a model or rebuild a document | Select a route in the [developer guide](development.md) | The route's solver or document tools |

The GitHub Markdown contains text, equations and tables. Stable illustrated entries include lightweight figure previews; full figures are supplied as version attachments. Use the restored PDF for complete reading, or the Notebook for the same text with native graphics. Chapter excerpts retain the numbering of their complete edition.

## Read PDF and Notebook editions

The historical scholarly source is `v1.0.0-rc.1`, with attachments in its [private draft Release](https://github.com/HNNUYUXUAN/litz-wire-research/releases/tag/untagged-f71ee4e060c0e39537cb). Use a GitHub CLI identity with access to this repository and its draft releases. Check the signed-in account with `gh auth status`; use `gh auth login` to establish a session if needed.

In Windows PowerShell, run from the parent directory where you want the project:

```powershell
gh repo clone HNNUYUXUAN/litz-wire-research
cd litz-wire-research
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\litz-research.exe data fetch academic-editions
.\.venv\Scripts\litz-research.exe data verify academic-editions
```

For an existing checkout, run the installation and data commands from its root. The downloader reads the part manifest, reuses verified cache entries and restores relative paths. The academic dataset and its shared dependency download approximately **463.4 MiB**; the [dataset guide](datasets.md) lists the components. Verification should report `status: passed`. Download, extraction and verification times depend on the connection and disk.

Open the restored English single-column paper:

```powershell
Start-Process -FilePath '.\outputs\publication_rc1_20261007_01\documents\paper\en\paper_en_single.pdf'
```

Other complete editions are available at these paths relative to your checkout:

| Edition | Single-column PDF |
| --- | --- |
| English report | `outputs/publication_rc1_20261007_01/documents/report/en/report_en_single.pdf` |
| Chinese paper | `outputs/publication_rc1_20261007_01/documents/paper/zh-CN/paper_zh-CN_single.pdf` |
| Chinese report | `outputs/publication_rc1_20261007_01/documents/report/zh-CN/report_zh-CN_single.pdf` |

The two-column edition uses `_ieee.pdf` in the same directory. Open `notebooks/publication/publication_rc1_20261007_01/paper/en/paper_en.nb` through the Wolfram frontend's file dialog for the English paper Notebook. The [complete directory](editions.md) lists the remaining Notebooks and chapters. Their saved text, plots and three-dimensional graphics are ready to read.

Offline restoration uses a complete cache containing the parts and content objects. Replace the quoted path below with your cache directory:

```powershell
.\.venv\Scripts\litz-research.exe data fetch academic-editions --offline --cache 'D:\Research Cache\litz'
```

## Run the example

After the base installation above, run from the repository root:

```powershell
.\.venv\Scripts\litz-research.exe run analytic
```

Each execution receives a distinct run identifier. The returned `run_id` identifies `outputs/<run_id>/`. Its `results.json` contains conditions, quantities, errors and twelve checks; `radial_current_density.csv` contains the radius and real and imaginary current-density components. The CSV uses m for radius and A/m² for current density.

| Reference quantity | Expected value | Meaning |
| --- | ---: | --- |
| `Q1_Rac_mohm_per_m` | 20.01620363 | AC internal resistance per unit length, mΩ/m |
| `Q1_P_W_per_m` | 8.00648145 | Joule loss per unit length at 20 A RMS, W/m |
| `Q1_Jdc_A_per_mm2` | 6.36619772 | Mean DC current density in the 2 mm diameter wire, A/mm² |

The example represents an isolated straight round wire at 200 kHz, 20 °C and 58 MS/m conductivity. The twelve checks test analytical identities, integrals and physical conventions. The Q1 current-density check records that the specified 2 mm wire exceeds the 4 A/mm² condition. See [acceptance criteria](../tests/ACCEPTANCE.md) for the meaning of each acceptance status.

For Linux/macOS, install and run the base example with:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/litz-research run analytic
```

The Python analytical example and dataset restoration use cross-platform Python. The retained scientific process supervisors and manuscript frontend workflow use Windows; route-specific requirements are documented in the [developer guide](development.md).

## Troubleshooting

| Observation | Next step |
| --- | --- |
| Release access error | Run `gh auth status` and check the account's repository access |
| Missing PDF, figure or Notebook | Run `data fetch academic-editions`, then `data verify academic-editions` |
| Reported checksum error | Preserve the dataset identity and path, and inspect the cache and restoration records using the [developer guide](development.md) |
| Wolfram or LaTeX tool unavailable | PDF reading and the Python example are available independently; configure the corresponding build environment using `doctor` diagnostics |

Figure regeneration and document compilation are described in the [developer guide](development.md). Dataset identities, original sources and model states are described in [datasets](datasets.md) and [provenance](../provenance/README.md).
