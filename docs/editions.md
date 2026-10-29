# Scholarly editions and builds

[简体中文](editions.zh-CN.md)

The [publication index](../publications/README.md) provides six English and Chinese LaTeX masters and generated Markdown readings. The research report uses one column; the automation and physics papers use IEEE journal. The [source manifest](../manuscript/latex-publication.json) records identities, section order, layout and evidence relationships.

## Build and inspect

Rebuild the project [Conda environment](../automation/environments/README.md) with Pandoc 3.13 and document dependencies. XeLaTeX, SimSun and Times New Roman are external installations. The source tree includes the required figures, bibliography and retained numerical inputs.

```bash
.conda/project/python.exe -m litz_research.cli build --run-id scholarly_local_01
.conda/project/python.exe tools/RenderLatexReview.py --run-id scholarly_local_01
.conda/project/python.exe tools/SelectPublicationBuild.py --run-id scholarly_local_01
.conda/project/python.exe tools/BuildAgentCatalog.py
```

The default build converts all six sources, compiles PDFs, verifies identities and packages LaTeX, figures, data and Markdown. Individual stages are `preflight`, `documents`, `pdf`, `verify` and `package`. `--edition` and `--language` restrict conversion; compilation and delivery require all six masters. Use a new run ID after editing source. Selecting a build updates reading navigation and preserves its page-review status.

Review all rendered pages and record the PDF hashes and review findings. Automated compilation checks detect missing glyphs, overfull boxes and unresolved references; they supplement visual review. PDFs remain local preview and acceptance artifacts.

## Source and reading consistency

Edit titles, abstracts, keywords, paragraphs and captions in LaTeX. Stable paragraph IDs, equation labels, figure identities and bibliography keys connect sources to their readings. Numerical substitutions are recomputed from the retained evidence before conversion. Unsupported commands, unresolved references and roundtrip text or math loss fail the build. Generated UTF-8 files use LF line endings for the same byte identity across operating systems.

[Manuscript instructions](../manuscript/README.md) describe the conversion contract. [Citation guidance](citation-guide.md) explains the shared bibliography. [Historical releases](../publications/HISTORY.md) retain published attachment identities and applicable licenses.
