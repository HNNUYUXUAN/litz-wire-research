# Candidate review

Version `v1.0.0-rc.1` is the private candidate for the Litz Wire Research snapshot. The repository has an independent history, with scientific evidence derived from source baseline `7f98a4092654125597bb843f7ee0e6a586041c7a`.

## Review paths

- Read [the English entry](../README.md) or [the Chinese entry](../README.zh-CN.md).
- Select a [complete paper, report, or chapter](editions.md).
- Inspect [scientific acceptance](../tests/ACCEPTANCE.md), [per-file provenance](../provenance/candidate_files.json), and [license categories](../LICENSES/README.md).
- Install the command-line tool and run the analytical example. Select datasets with `litz-research data list` and `data fetch <dataset>`.

The candidate contains 13 datasets, 31,950 restored file identities and 8,953 unique content objects. Sixty-five compressed parts total 7,605,595,016 bytes; each part is at most 128 MiB. Original scientific bytes and metadata derivatives have separate source and release hashes.

## Acceptance evidence

Local records in [provenance/validation](../provenance/validation/) cover independent Python and Wolfram analytical regressions, installation in a fresh virtual environment, dataset restoration, document builds, and migration through a directory containing spaces. All 104 PDFs were compiled and their 411 pages rendered. All 52 Notebooks were opened, saved, read back, and rendered; native 3D view changes were saved and recovered. Visual comparison with the accepted source edition identified 16 PDF pages and 18 Notebook render chunks requiring individual review, all completed.

The publication preserves model assumptions and scientific acceptance states. Consult the discussion and diagnostic appendices when evaluating A–φ, Ansys, RT0, finite-length PEEC, and transposition claims.

## Public-version review

Review the scientific scope, attribution, dual licensing of Notebook cells, bibliography links, download experience, and the scholarly editions. Public visibility and the final archival state are the next release-stage decisions. The private candidate and its draft release provide the complete materials for that review.
