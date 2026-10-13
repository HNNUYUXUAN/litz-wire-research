# Cite the software, data and automation method

`references/library.bib` is the sole manually maintained bibliography. `references/sources.json` adds actual role, implementation location, version/commit, license and use evidence under the same stable key. Compatibility BibTeX and CSL files are generated exports. Run `litz-research references build` and `references verify` after edits.

Display numbers follow first citation in each complete edition. Chinese and English use the same `citation_maps.json`; chapters inherit their parent numbers. The canonical reference parser supplies Markdown, Notebook and LaTeX. Frozen historical editions retain their source identity; current representative builds verify the new chain.

Software example: Miao, Yuxuan. *Litz Wire Research: agent-driven reproducible modeling and simulation*. Version 1.0.0-rc.2, candidate software, 2026. https://github.com/HNNUYUXUAN/litz-wire-research/tree/v1.0.0-rc.2. Include the exact commit returned by `git rev-parse v1.0.0-rc.2` and access date.

Data example: cite the same repository/version, dataset `automation-rc2` or the immutable `v1.0.0-rc.1` route dataset, actual source run ID, `results.json` SHA256 and catalog/manifest identity. Method-document example: cite this version/commit, `docs/automation-architecture.md`, and the corresponding case in `automation/examples/verification.json`. No DOI has been assigned.

CITATION.cff describes original software. Original prose, figures and data use CC BY 4.0. Upstream software keeps its own terms. Read-only repository review, runtime dependency, adapted code and comparison evidence are separate source-use states. AI use and author responsibility are documented in ACKNOWLEDGMENTS.
