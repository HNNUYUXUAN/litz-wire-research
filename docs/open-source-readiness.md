# Public distribution record

[English](open-source-readiness.md) · [简体中文](open-source-readiness.zh-CN.md)

Record date: 20 October 2026. The source is maintained in [HNNUYUXUAN/litz-wire-research](https://github.com/HNNUYUXUAN/litz-wire-research). Publication artifacts retain the run identity `publication_review_20261015_03`.

## Maintained source and publications

The README routes readers by task. A generated catalog exposes seven modeling routes, five workflows, six automation cases and six complete manuscripts, with source paths and raw-byte hashes. The [pattern record](../provenance/maintenance/repository-patterns.json) identifies the exact revisions reviewed in general-physics-lab, thermal-pde-audit, phy-sim-llm and cluetide-review.

Current publication indexes and download names are generated from the same delivery records. The original rc.1 index is archived byte for byte. Contributor and development guides are available in both languages. A Windows/Ubuntu and Python 3.11/3.12 CI matrix checks portable source contracts, reading links, discovery and future publication updates.

The publication ZIP preserves the source and artifacts of its original build. Subsequent repository maintenance has its own source commit and test records. Downloaded PDFs, Notebooks and ZIPs retain their original hashes; the accompanying [license package](../LICENSES/publication-companion/README.md) records license scope and notices for the frozen archive members.

## Preparation evidence

The following checks were recorded during source preparation on 20 October 2026. They describe that preparation revision; the released revision and public access observations are recorded separately below.

| Check | Recorded result |
| --- | --- |
| Fresh installation | Separate Windows Python 3.12 environment and checkout containing spaces; dependency check passed |
| Portable source and maintenance tests | 43 tests passed locally |
| Bibliography and discovery | 60 references verified; 15 CLI model entries discovered |
| Reader paths | Tracked Markdown relative-link check passed; external URL and heading-anchor checks are outside this checker |
| Release attachment metadata | 66 data parts, 27 publication artifacts and one license companion match the API names, sizes and SHA256 values |
| Frozen identities | Original publication ZIP hashes and archived rc.1 index retained |
| License companion | 1,315 original ZIP members indexed; deterministic companion build and member verification passed |

Evidence: [source tests](../provenance/maintenance/source-checkout-20261020.json), [maintenance tests](../provenance/maintenance/maintenance-tests-20261020.json), [environment](../provenance/maintenance/fresh-environment-20261020.json), [reader paths](../provenance/maintenance/reader-links-20261020.json), [asset metadata](../provenance/maintenance/release-assets-20261020.json), [retained identities](../provenance/maintenance/preserved-identities-20261020.json).

The targeted [disclosure check](../provenance/maintenance/source-disclosure-20261020.json) records the inspected source/history range, configured credential/private-key signatures, file counts and exclusions. Binary contents and external evidence archives have separate inspection boundaries described in that record.

## Released revision and public access

The maintained source release is `v1.0.0-rc.3`; frozen evidence and manuscripts remain attached to rc.1 and rc.2. Source revision checked for release: [`01aa0bc3dc12a548301a148f8fc99e12a241e075`](https://github.com/HNNUYUXUAN/litz-wire-research/commit/01aa0bc3dc12a548301a148f8fc99e12a241e075). Observation time: `2026-10-19T17:20:14.443577+00:00`.

| Check | Observed result |
| --- | --- |
| Hosted Windows/Ubuntu × Python 3.11/3.12 matrix | All four jobs passed |
| Repository visibility | Public |
| `v1.0.0-rc.1` historical evidence release | Published |
| `v1.0.0-rc.2` automation and publication release | Published |
| `v1.0.0-rc.3` maintained source release | Published |
| Source and maintenance tests for the released revision | 59 tests passed in each of the four matrix jobs |
| Public catalog and credential-free CLI restoration | Passed: a fresh environment restored 874 analytic files without credentials; 679 object hashes matched |
| Anonymous attachment readback and hash verification | Full download acceptance of all 127 assets is in progress; all 972 files in the source ZIP passed verification |

Evidence: [hosted CI run](https://github.com/HNNUYUXUAN/litz-wire-research/actions/runs/39289553044), [release state and metadata](../provenance/public-release/repository-releases.json), [anonymous downloads and restoration](../provenance/public-release/README.md). Each receipt states its source revision, timestamp and inspection scope.

The public catalog retains asset-ID API URLs and supplies verified browser download URLs. The CLI uses public download mode without reading GitHub credentials. The [dataset guide](datasets.md) explains selective restoration and offline reuse; the [release procedure](release-preparation.md) describes how to repeat source, attachment and anonymous-access checks for later releases. Historical snapshots retain the visibility and Release states observed at their own capture times.

This maintenance run performed no physical solves or publication rebuilds. Existing numerical acceptance and unresolved research questions remain attached to their original evidence.
