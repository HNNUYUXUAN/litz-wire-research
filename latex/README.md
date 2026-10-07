# LaTeX builds

The academic editions use the shared Markdown sources in `manuscript/` and the publication manifest. XeLaTeX renders SimSun for Chinese and Times New Roman for Western text and numbers. Mathematical typesetting uses the installed TeX math packages. IEEEtran is distributed under its upstream LPPL terms.

Install the document dependencies and check the toolchain from the project root:

```sh
python -m pip install -e ".[documents,figures]"
litz-research doctor
litz-research data fetch publication-inputs
litz-research build --run-id paper_example_01 --edition paper --language en --form merged --layout all --stage documents
litz-research build --run-id paper_example_01 --edition paper --language en --form merged --layout all --stage pdf
```

Set `LITZ_XELATEX`, `LITZ_BIBTEX`, and `LITZ_LATEXMK` when executables are outside PATH. Install SimSun and Times New Roman through a licensed operating-system or font distribution. The template smoke files provide a small standalone example; the complete manuscripts and their numbering come from the unified build.

Compiled files, logs, dependency versions, source hashes, and actual exit codes are saved under the selected run directory in `outputs/`. PDF checks use pypdf and pypdfium2 from the document dependency group.
