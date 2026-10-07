# Datasets / 数据集

Select a route with `litz-research data fetch <dataset>`. Dependencies are restored automatically. Use `data verify <dataset>` to check the resulting files. Academic viewing uses `academic-editions`; rebuilding the editions uses `publication-inputs`. Cross-route validation fixtures are in `research-records`.

使用 `litz-research data fetch <dataset>` 获取路线及依赖；完整测试所需的跨路线输入位于 `research-records`。`research-shared` 保存去重后的共享对象，由所属路线映射到实际文件路径。各数据集保留原始运行的执行状态、模型范围和物理验收状态。

| Dataset | Files | Compressed MiB | Contents |
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

The catalogue in `data/catalog.json` is authoritative for ordered parts, dependencies, file identities and checksums. Compressed sizes count objects owned by each dataset; shared dependencies add their own download size. All parts are at most 128 MiB.

Route records distinguish external-field loss, conductor transport quantities, geometrical observations, and three-dimensional diagnostic results. Use the corresponding model definitions and acceptance records when comparing quantities.
