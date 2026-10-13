# Development

## Module layout

`python/litz_research/` contains installation, CLI orchestration, configuration, the independent Python Bessel calibration, and dataset transfer. `src/` contains the Wolfram models, stage runners, Ansys adapters, and publication builders. `configs/` defines physical inputs. `tests/` contains Wolfram and Python regression checks. `manuscript/publication.json` binds paired paragraphs, equations, figures and frozen observables.

Extend a model through an explicit input record and a uniquely named run directory. Archive `source_model`, `run_id`, `execution_status`, `physical_acceptance_status`, units, phasor convention, material parameters, source hashes, elapsed time, and actual exit status. A completed solver call and a passed physical validation have distinct meanings. Preserve complex values as real and imaginary parts; amplitude and phase are derived quantities.

## Environments

Python 3.11+ supports reading datasets and the analytical example. Install editable extras for document and figure handling. Wolfram 15.0 on Windows is the recorded scientific baseline; a licensed kernel runs the scientific modules and the frontend renders `.nb` documents and native three-dimensional graphics. XeLaTeX, BibTeX and latexmk compile the academic editions. Font matching uses locally installed SimSun and Times New Roman. Fonts are installed separately under their own licenses.

The retained PowerShell solver supervisor binds processes to their creation identities, records a process tree, checks available memory and preserves exit codes. The current configuration limits work to eight logical processors and 24 GiB with an 8 GiB system reserve. Model-specific predictions can impose a smaller budget. Ansys adapters require Maxwell and a compatible PyAEDT installation; Student-specific element and four-core limits remain part of each run's acceptance conditions. GPU routes require the recorded Wolfram CUDALink environment and same-model CPU comparisons.

Executable configuration has two layers: `LITZ_<TOOL>` environment variables, followed by `tools.<tool>` in local `litz.config.json`, then PATH. Example:

```json
{"tools": {"wolframscript": "wolframscript", "xelatex": "xelatex", "bibtex": "bibtex", "latexmk": "latexmk"}}
```

## Validation

```sh
python -m unittest discover -s tests -p test_research_cli.py
litz-research run analytic --run-id analytical_validation_01
litz-research run wolfram-analytic --run-id wolfram_validation_01
litz-research data verify
```

Scientific tolerances are defined in `tests/ACCEPTANCE.md`. Extend tests when a change affects physical conventions, data identities, constrained currents, independent power balance, operator action, or resource ownership. Small numerical changes require focused regression; conclusions based on large retained computations are linked to the preserved evidence.

## Dataset schema

`data/catalog.json` contains named datasets, dependencies, ordered archive parts, object SHA256 and byte counts, and logical file paths. Parts concatenate to a gzip-compressed tar stream. Tar members are `objects/<sha256>` and contain only regular files. Shared objects are assigned to one dataset and referenced by dependency. `data fetch` checks part hashes, archive coverage and object hashes before restoring logical paths. Existing local files are verified before reuse. Offline mode uses the same cache and checks.

Each source record in `provenance/` binds original and candidate SHA256, origin, rights, processing and scientific review. Metadata derivatives retain a mapping to their original identities. Credentials stay with the local authentication provider. Dataset attachment URLs are populated from the private draft Release; download authorization is limited to the GitHub API host.

## Publications

Edit paired Markdown paragraphs and shared definitions first, then use `litz-research build`. Chapter files are extracted from the merged document structure. The build tracks hashes for source dependencies, independent figure panels, composed panels, compiled PDFs and saved Notebooks. Changes to scientific data require a distinct source identity and documented acceptance. Stage recovery reuses verified artifacts belonging to the same run and input manifest.
