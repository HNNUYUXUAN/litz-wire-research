# Open-source preparation record

[English](open-source-readiness.md) · [简体中文](open-source-readiness.zh-CN.md)

Prepared on 20 October 2026. The source candidate is maintained in `HNNUYUXUAN/litz-wire-research`. Publication artifacts retain the run identity `publication_review_20261015_03`.

## Maintenance completed

The README now routes readers by task. A generated catalog exposes seven modeling routes, five workflows, six automation cases and six complete manuscripts, with source paths and raw-byte hashes. The [pattern record](../provenance/maintenance/repository-patterns.json) identifies the exact revisions reviewed in general-physics-lab, thermal-pde-audit, phy-sim-llm and cluetide-review.

Current publication indexes and download names are generated from the same delivery records. The original rc.1 index is archived byte for byte. Contributor and development guides are available in both languages. A Windows/Ubuntu and Python 3.11/3.12 CI matrix checks portable source contracts, reading links, discovery and future publication updates.

## Recorded checks

| Check | Recorded result |
| --- | --- |
| Fresh installation | Separate Windows Python 3.12 environment and checkout containing spaces; dependency check passed |
| Portable source and maintenance tests | 43 tests passed locally |
| Bibliography and discovery | 60 references verified; 15 CLI model entries discovered |
| Reader paths | Tracked Markdown relative-link check passed; external URL and heading-anchor checks are outside this checker |
| Release assets | 66 data parts, 27 publication artifacts and one license companion match the API names, sizes and SHA256 values |
| Frozen identities | Original publication ZIP hashes and archived rc.1 index retained |
| License companion | 1,315 original ZIP members indexed; deterministic companion build and member verification passed |

Evidence: [source tests](../provenance/maintenance/source-checkout-20261020.json), [maintenance tests](../provenance/maintenance/maintenance-tests-20261020.json), [environment](../provenance/maintenance/fresh-environment-20261020.json), [reader paths](../provenance/maintenance/reader-links-20261020.json), [asset metadata](../provenance/maintenance/release-assets-20261020.json), [retained identities](../provenance/maintenance/preserved-identities-20261020.json), [package licenses](../LICENSES/publication-companion/README.md).

The targeted [disclosure check](../provenance/maintenance/source-disclosure-20261020.json) found no configured credential/private-key signatures in the inspected UTF-8 source and history. Its record specifies the commits, file counts and exclusions; binary contents and external evidence archives were outside that text scan.

The hosted matrix was queued when preparation was recorded. Check the result for the exact source commit in [GitHub Actions](https://github.com/HNNUYUXUAN/litz-wire-research/actions/workflows/ci.yml); queued jobs are not counted as passed checks here.

## Publication transition

The repository is Private; rc.1 and rc.2 remain Draft. The dataset catalog still uses authenticated access. Public distribution requires the visibility/release transitions, public download metadata and anonymous download verification in the [release procedure](release-preparation.md). Attachment metadata verification does not establish anonymous accessibility.

This maintenance run performed no physical solves or publication rebuilds. Existing numerical acceptance and unresolved research questions remain attached to their original evidence.
