# LaTeX construction

Paired Markdown and the shared manifest in `manuscript/` supply the scholarly manuscripts. XeLaTeX uses SimSun for Chinese, Times New Roman for Latin text and numbers, and TeX mathematics packages. IEEEtran retains its upstream LPPL license.

Install `.[documents,figures]` and run `litz-research doctor`. Restore the required evidence and prepare the figure inputs as described in [Editions](../docs/editions.md), then use:

```powershell
litz-research build --run-id paper_example_01 --edition paper --language en --form merged --layout all --stage documents
litz-research build --run-id paper_example_01 --edition paper --language en --form merged --layout all --stage pdf
```

`--edition` accepts `report`, `paper` and `automation`; `--layout` accepts `single`, `ieee-journal`, `ieee-conference` and `all`. The legacy `ieee` selector aliases the journal layout.

Set `LITZ_XELATEX` and `LITZ_LATEXMK` when the executables are outside PATH. Install fonts through a licensed operating-system or font distribution. [Independent templates](templates/README.md) illustrate prose, equations, tables and references in each layout. Complete manuscripts obtain numbering from their shared document structure.

Compiler logs, tool versions, source hashes and actual exit codes are stored under the run in `outputs/`. PDF checks use pypdf and pypdfium2.

[简体中文](README.zh-CN.md)
