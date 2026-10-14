# Windows and Wolfram Notebook execution

[简体中文](Windows与Notebook实施路线.md)

The project combines Python orchestration, Wolfram scientific modules and optional solver adapters. Start with `litz-research doctor` to inspect actual tools, fonts and resources; installation groups are described in [Development](development.md).

`litz-research run analytic` runs independent Python Bessel calibration. `run wolfram-analytic` starts a clean Wolfram kernel for the corresponding twelve checks. FEM, common-terminal coupling, geometry, PEEC and RT0 use their route runners and retain parameters, source snapshots, logs and acceptance under individual run identifiers.

The recorded Windows baseline uses Wolfram 15.0. Kernel computation and Notebook frontend operation are checked separately. Process supervisors track creation identities, eight logical processors, 24 GiB task memory and an 8 GiB free-memory reserve. Ansys follows its actual version and license limits; GPU runtime and same-matrix comparisons are retained with their runs.

## Manuscript construction

```powershell
litz-research data fetch publication-inputs
python tools/PreparePublicationInputs.py
litz-research build --run-id publication_local_01 --form merged --stage all
```

Paired Markdown and the common manifest in `manuscript/` define the content. The build produces document structure, panel compositions, native Notebooks, LaTeX and PDFs. Notebooks contain prose, equations, figures and interactive Graphics3D; numerical calculations use separate research entry points.

Notebook checks open, save, reread and render the actual frontend document. Viewpoint roundtrips verify preserved geometry. XeLaTeX and latexmk compile the PDFs; the canonical bibliography supplies their references. Checks cover embedded fonts, resolved links, clipping and every rendered page. SimSun and Times New Roman are supplied by the local font environment.

## Data recovery

Use `data list`, `data fetch` and `data verify` to select, restore and check datasets. Parts, objects and restored files have SHA256 identities. Offline restoration uses `--offline --cache <directory>`. Paths derive from the project root; migration checks include directories containing spaces.
