# Scholarly presentation

[简体中文](editorial-style.zh-CN.md)

The retained specimen `publication_20261013_paper_sample_09` establishes the project's approach to scientific exposition, equations, figures and captions. Its original Notebook and verification record retain their own hashes and run identity. Current editions use this approach across a comprehensive report, an automation-method paper and a physical-modeling paper.

Chinese prose uses SimSun; Latin text uses Times New Roman. Independent figures are designed at 88.9 mm, with a 252 × 198 pt canvas for the calibrated field and curve panels. Composite figures preserve each panel's identity and place panel letters above the panels. Figure titles identify the observable; explanatory captions state model conditions, sampling and interpretation.

The general single-column PDF uses A4 paper and the established reading layout. IEEE journal and conference PDFs use the respective IEEEtran class options and class-defined page geometry, headings, author blocks and captions. Figure widths adapt to the available column or page width. All PDFs are compiled from LaTeX; the three layouts share the same scientific content and citation map.

Native Wolfram Notebooks retain typeset equations, tables and Graphics3D. Frontend acceptance includes opening, saving, reopening, rendering all cells, and checking a changed viewpoint against the original geometry. Scientific plots are reconstructed from recorded data or saved fields; conceptual illustrations accompany the repository overview with their generation records.

The build binds source files, quantities, panel exports and output hashes. A new build identity is required when the input manifest changes. The [publication guide](editions.md) gives build and reading entry points.
