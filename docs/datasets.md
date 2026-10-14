# Research datasets

[简体中文](datasets.zh-CN.md)

Select the required route through the CLI. Dependencies are restored with it; verify file identities after restoration:

```powershell
litz-research data list
litz-research data fetch publication-inputs
litz-research data verify publication-inputs
```

| Dataset | File mappings | Compressed MiB | Contents |
| --- | ---: | ---: | --- |
| `academic-editions` | 665 | 337.48 | Bilingual reports, papers, chapters, Notebooks, PDFs, figures and document acceptance records |
| `analytic` | 874 | 1.38 | Round-wire Bessel calibration, radial profiles and analytical acceptance records |
| `ansys` | 1,980 | 4.28 | Maxwell inputs, projects, interface probes, mesh limits and validation records |
| `aphi` | 2,057 | 3200.49 | Three-dimensional A–phi fields, calibration diagnostics and solver boundary evidence |
| `common-terminal` | 1,401 | 693.62 | Common-terminal field–circuit models, complex strand currents and controlled return-path evidence |
| `fem2` | 470 | 6.28 | Two-dimensional finite-element calibration, meshes, fields and sensitivity checks |
| `geometry` | 1,155 | 94.24 | Strand identities, centreline geometry, arc lengths, copper volume and geometric checks |
| `gpu` | 4,746 | 301.36 | CPU/GPU matrix and complex-current comparisons with resource and exit-status records |
| `peec` | 3,289 | 989.54 | Finite-length longitudinal PEEC inputs, solutions, length and quadrature sensitivity |
| `publication-inputs` | 311 | 46.57 | Verified independent panels, figure data and observables used by publication builds |
| `research-records` | 11,389 | 929.57 | Cross-route run records, handoff inputs, validation summaries and retained source snapshots |
| `research-shared` | 0 | 125.87 | Content objects shared by route datasets; restored through their dependent file mappings |
| `rt0` | 3,613 | 522.57 | Imposed-field RT0 solutions, flux reconstruction, spatial convergence and operator checks |
| `automation-rc2` | 10,569 | 14.70 | Actual Codex/MCP automation cases, bounded task snapshots, Maxwell projects, route regressions and twenty native Notebook execution records |

## Identity and offline restoration

`data/catalog.json` defines part order, dependencies, object and file SHA256 identities. Compressed sizes count each dataset’s own parts; shared dependencies add to the first download. Parts are at most 128 MiB. Historical scientific records restore beneath `data/evidence/v1.0.0-rc.1/`, and automation records beneath `data/evidence/v1.0.0-rc.2/`, preserving original relative paths. New runs write to `outputs/`.

```powershell
litz-research data fetch publication-inputs --offline --cache "C:/Research Cache"
```

The restorer checks parts, archive membership, objects and final files; existing files are reused after hash verification. Corrupt objects produce explicit diagnostics. Imposed-field loss, transport resistance, geometric quantities and three-dimensional diagnostics retain their model definitions. Current local editions are indexed in [Publications](../publications/README.md); `academic-editions` locates historical editions.
