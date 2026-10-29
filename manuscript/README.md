# Litz bilingual LaTeX masters

The six `main.tex` files and their `sections/` directories own manuscript prose, titles, abstracts, keywords and captions. The report uses a single column; the automation and physics papers use IEEE journal. `latex-publication.json` records document identity, order, layout and evidence relationships.

| Work | Chinese master | English master |
| --- | --- | --- |
| Complete report | [main.tex](report/zh-CN/main.tex) | [main.tex](report/en/main.tex) |
| Automation methods | [main.tex](automation/zh-CN/main.tex) | [main.tex](automation/en/main.tex) |
| Physics paper | [main.tex](paper/zh-CN/main.tex) | [main.tex](paper/en/main.tex) |

Use the project Conda environment and Pandoc 3.13. XeLaTeX, SimSun and Times New Roman are external installations.

```bash
.conda/project/python.exe -m litz_research.cli build --run-id publication_YYYYMMDD_01
```

The default pipeline generates the six Markdown reading editions under `publications/reading`, compiles the six masters in the run directory, verifies file identities and packages source. Individual stages are `preflight`, `documents`, `pdf`, `verify` and `package`. Reuse a run ID only to continue a stage with unchanged inputs; use a new ID after editing source. PDFs are temporary compilation and review artifacts. Figure PDFs and PNGs are required source assets.

Paragraph IDs use `% block-id:` and matching `\hypertarget`. Keep bilingual identities aligned. Citations use keys from `references/library.bib`. Equations and figures retain labels. `\metric{key}` consumes `metrics.json`; its values are recomputed from retained numerical inputs and its display strings are checked before generation of `generated/metrics.tex`. Bibliography TeX is generated from the shared BibTeX library.

The Pandoc adapter rejects unresolved references and unsupported raw LaTeX content. A Markdown roundtrip checks prose and mathematics; paragraph identities and bilingual citation order are checked separately. A conversion failure requires a tested adapter change. Review every compiled page before accepting the edition:

```bash
.conda/project/python.exe tools/RenderLatexReview.py --run-id publication_YYYYMMDD_01
```

`migration-receipt.json` retains the original chapter hashes, block IDs and figure identities. The source migration imported sixty chapters and added four bilingual integration sections. Original Markdown chapters and the previous manifest remain available during the final cleanup audit; edits belong in the LaTeX masters.

IEEEtran retains its LPPL notice. Figures, bibliography and numerical evidence retain their applicable source and license records. The original physical limitations, including A–φ gauge failures and Maxwell convergence gaps, remain part of the manuscripts.
