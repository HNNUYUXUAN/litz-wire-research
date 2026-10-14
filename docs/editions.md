# Scholarly editions and builds

[简体中文](editions.zh-CN.md)

The [publication index](../publications/README.md) provides complete Chinese and English versions of the research report, automation-method paper and Litz physical-modeling paper. Each has Markdown, a native Wolfram Notebook, and LaTeX/PDF in general single-column, IEEE journal and IEEE conference layouts. The layouts share full content and impose no conference page cap.

## Build a complete work

Install the document dependencies and restore the input data described in [Datasets](datasets.md). For a new source checkout, prepare the scientific figure inputs before composing current editions. A supplied portable manuscript package includes the selected panels and can compile LaTeX directly.

```powershell
python -m pip install -e ".[documents,figures,automation]"
python tools/PreparePublicationInputs.py
litz-research build --run-id scholarly_local_01 --edition all --language all --form merged --layout all --stage documents
litz-research build --run-id scholarly_local_01 --stage pdf
litz-research build --run-id scholarly_local_01 --stage notebooks
litz-research build --run-id scholarly_local_01 --stage verify
litz-research build --run-id scholarly_local_01 --stage package
```

Edition selectors are `report`, `paper`, `automation` and `all`; layout selectors are `single`, `ieee-journal`, `ieee-conference` and `all`. The legacy `ieee` selector means IEEE journal. A new manifest requires a new run identity. Build outputs, compilation logs, Notebook receipts and verification details are saved beneath the selected `outputs/` directory.

## Reading and reuse

PDFs are compiled from their LaTeX sources. Standalone templates demonstrate class-specific author blocks, abstracts, figures, equations and references. Native Notebooks support inspection of saved three-dimensional graphics. Research calculations have separate [model entry points](tool-workflows.md).

The [editorial guide](editorial-style.md) describes the sample-09 conventions and IEEE adaptations. [Citation guidance](citation-guide.md) explains the shared bibliography. Historical editions retain their dataset identities and are linked separately from current manuscripts.
