# Bilingual scholarly editions — execution record

Approved scope: local review workspace; local commits; remote publication is a separate operation.

## Deliverables

- Three works: complete research report (`report`), agent/MCP methods (`automation`), Litz physical research (`paper`).
- Each work: Chinese and English complete Markdown and native Wolfram Notebook; single-column, IEEE journal and IEEE conference LaTeX/PDF (18 PDFs total).
- Bilingual reader documentation, source-based acknowledgments, 21 scientific figure families redrawn from retained inputs, six bilingual overview illustrations selected from at least 18 candidates.
- Portable LaTeX package, checksums, bilingual reading index, PDF and Notebook visual verification.

## Execution constraints

Scientific inputs remain frozen. Plotting, sampling and document compilation receive new run identities. No additional physical solver campaign is included. Preserve the approved sample `publication_20261013_paper_sample_09` and independently modified review indexes.

Use at most eight logical processors and 24 GiB task memory; retain 8 GiB system free memory. Scope includes required local dependency setup, repair, rendering, packaging and commits without intermediate approval gates.

## Progress

1. Environment and source inventory: independent Python environment installed; source resolution uses versioned evidence; Wolfram frontend exports and three PDF layouts exercised.
2. Publication interfaces and source resolution: three editions and three layouts implemented; per-work citation identity retained; standalone layout renderer added.
3. Bilingual documents and source attribution: localized source registry and generated acknowledgments/notices complete; documentation translation and factual rewrite in progress.
4. Three paired manuscripts and chapter evidence records: six-chapter automation paper authored in both languages; physical paper aligned to sample 09 and retranslated; shared report prose aligned and rc.2 records integrated. Thirty chapters and 270 paired blocks passed the scientific-token and citation audit; claim-evidence-map.json records the paragraphs and sources.
5. Scientific figures and visual selection: all 62 bilingual independent panels redrawn and checked (21 figure families); eight field/curve panels reframed and verified; overview/sketch image pairs and 24 vector candidates generated. Eight selected SVG diagrams rendered in Chrome; two English labels shortened after inspection.
6. Six Notebooks / eighteen PDFs / portable templates: first complete build rendered six native Notebooks and compiled eighteen PDFs; final corrected build is publication_review_20261015_03. Six reusable templates generated; standalone compilation in a spaced directory passed for the preceding source bundle.
7. Verification, local packaging and commit: pending.

## Resume information

Baseline: `15df5069e4f370c130ac0306bc65f441a64b7ad5`, branch `workshop-codex/open-source-review`.
Existing untracked review files: `REVIEW.zh-CN.md`, `publications/NOTEBOOKS.zh-CN.md`; preserve them.
Evidence roots: `data/evidence/v1.0.0-rc.1`, `data/evidence/v1.0.0-rc.2`.
Canonical manuscript generator: `tools/publication/PublicationManuscripts.py`; scientific asset builder: `tools/publication/BuildPublicationEdition.py`.
Shared evidence resolver: `litz_research.common.resolve_read_path`.
Python: `.venv/Scripts/python.exe`; system tools include WolframScript, XeLaTeX and latexmk.

## Scientific distinctions

The rc.2 native Maxwell case is a two-dimensional MCP construction/solve with port and power checks. Historical three-dimensional interface diagnostics and A–φ potential/gauge failures retain their own identities. A single mesh comparison is not a convergence uncertainty estimate. Automation conclusions describe the recorded cases and exposed tool events.

## Current build identities

- `publication_redraw_20261015_01`: completed field reconstruction and 62 exports; zero panel check failures.
- `publication_reframe_20261015_01`: source-binding guard detected an editor update to the Python supervisor during native rendering; retained as an unsuccessful build attempt.
- `publication_reframe_20261015_02`: eight panels completed, primitive identity and color checks passed; selected for manuscript overrides.
- `publication_pipeline_smoke_20261015_01`: English automation paper, three layouts compiled and PDF verification passed. Long reference URLs now use breakable URL typography. Verification uses its frozen input manifest after the main manuscript manifest evolved.
- `publication_review_20261015_01`: full six-document build launched; final PDF/Notebook acceptance still pending.

PDF skill operation marker completed once for 18 PDFs. Image prompts and selected paths are recorded alongside this log. All generated images were visually inspected in tool output; selected files are copied into `publications/assets/overview/`.


## Editorial verification and final run

- publication_review_20261015_01: all 18 PDFs compiled without overfull boxes, missing characters or unresolved references. All six Notebooks completed actual frontend save/reopen, complete cell rendering and Graphics3D viewpoint roundtrip. Page inspection found five Chinese descriptions in English sources; corrected with a new translation guard. Its early verification attempt ran before Notebook completion and correctly rejected the partial Notebook count.
- publication_review_20261015_02: stopped owned build processes after identifying an unsupported citation placeholder in newly added report method references. Process identities and the stop reason are retained in editorial_stop.json. Standalone compilation of this intermediate source package passed 24 documents, but it is superseded for content.
- publication_reframe_20261015_03: two coax640 mesh panels use readable 150k/250k/400k axis labels; primitives and plot ranges remain identical.
- publication_review_20261015_03: final corrected content. Single-column captions use centered titles and left-aligned explanatory text; IEEE layouts retain native class captions. LaTeX was refreshed independently while the unchanged Notebook document tree rendered; the PDF stage records its current renderer source binding.
- Eleven targeted publication tests passed, including the untranslated-paragraph guard, scientific quantity values, paired blocks and IEEE class/legacy alias handling. Source audit reports 30 chapters, 270 paired blocks and zero mismatches.
- Maintained-document relative links passed. Superseded generated chapter previews were removed; the original historical scholarly dataset remains intact. The reading generator emits six complete works only.

Final verification: all 240 PDF pages and 84 Notebook chunks visually inspected; six actual frontend save/reopen and viewpoint checks passed. The final standalone package compiled all 24 manuscript/template sources in a directory containing spaces. Eleven unittest checks, 60 bibliography entries, 270 paired blocks and maintained links passed. The initial pytest invocation found no pytest installation; the project uses unittest and its native test entry passed. Delivery manifests bind all final artifacts and packages. Local commit completes this scope; no remote push.
