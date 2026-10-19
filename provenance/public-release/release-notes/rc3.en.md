# Litz Wire Research v1.0.0-rc.3

This source-maintenance release provides the public downloader, reproducible source CI and bilingual reading routes for Litz Wire Research. Its source tag identifies the maintained code; historical datasets and the frozen manuscript set remain attached to rc.1 and rc.2.

## Read and reproduce

- [Start from the README](https://github.com/HNNUYUXUAN/litz-wire-research#readme) or the [automation guide](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/automation/README.md).
- Read the [complete report, automation methods paper and physics paper](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/publications/README.md), each in English and Simplified Chinese: six Markdown manuscripts, six native Wolfram Notebooks and eighteen PDFs in single-column journal, IEEE journal and IEEE conference layouts.
- Download the 27 selected publication artifacts—18 PDFs, six Notebooks and three ZIPs—from [rc.2](https://github.com/HNNUYUXUAN/litz-wire-research/releases/tag/v1.0.0-rc.2). Take `litz_publication_licenses_20261020.zip` with the publication packages; its member index identifies the applicable licenses and third-party notices.
- Restore selected research evidence using the [dataset guide](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/docs/datasets.md). Public downloads require no account or token. The catalog draws historical evidence from [rc.1](https://github.com/HNNUYUXUAN/litz-wire-research/releases/tag/v1.0.0-rc.1) and automation evidence from rc.2.

## Source maintenance

The maintained source adds task-based navigation, a machine-readable model/workflow/manuscript catalog, generated publication indexes, bilingual contributor and development guides, and Windows/Ubuntu × Python 3.11/3.12 source CI. The downloader retains GitHub asset IDs, uses verified public download URLs and verifies part and restored-file hashes.

Source revision checked for this release: [`01aa0bc3dc12a548301a148f8fc99e12a241e075`](https://github.com/HNNUYUXUAN/litz-wire-research/commit/01aa0bc3dc12a548301a148f8fc99e12a241e075). Source and maintenance tests: 59 tests passed in each of the four matrix jobs. Hosted CI: All four jobs passed ([run](https://github.com/HNNUYUXUAN/litz-wire-research/actions/runs/39289553044)). Anonymous download and restoration result: 127/127 Release assets downloaded in full without credentials; 8,578,518,566 bytes and all SHA256 values matched; the rc.3 source ZIP matched all 972 committed files; Fresh Python 3.12 installation restored all 874 analytic files; 679 unique dependency/data objects (660,867,640 bytes) passed hash verification; no credentials or authentication subprocesses. The [distribution record](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/docs/open-source-readiness.md) links the source, release-state and download evidence.

## Scientific and artifact identities

The manuscript set is frozen as `publication_review_20261015_03`; its assets retain the `review_20261015_` names and original SHA256 identities. The publication ZIP contains that build's source snapshot. Later CI, navigation and downloader maintenance is identified by the source commit above. The rc.3 tag identifies the maintained source. The existing rc.1 and rc.2 tags continue to identify their original commits; their data and publication attachments retain separate manifests.

The research uses SI units, `exp(+jωt)` and RMS phasors. The 2 mm round conductor is a calibration case; the final Q2 design requires at least 5 mm² nominal copper. Strand insulation and common-terminal voltage constrain the models without imposing equal strand currents. The imposed-field RT0 cuboid at 200 kHz and 1 mT RMS has zero net transport; its final spatial loss changes of 0.655090% and 0.362916% meet the recorded 1% refinement target. The saved three-dimensional A–φ cylinder still fails scalar-potential and gauge acceptance. Ranking real transposed structures requires matched terminal and return conditions, three-dimensional validation and controlled experiments. This maintenance release performs no new physical solve or manuscript rebuild.

Original software is MIT-licensed; original prose, figures and data use CC BY 4.0. Upstream components retain their own terms. Wolfram and Ansys remain external licensed applications. See [licenses](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/LICENSES/README.md), [acknowledgments](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/ACKNOWLEDGMENTS.md) and [citation guidance](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/docs/citation-guide.md).

The later public-download navigation and verification-tools commit `76323f6` passed 74 tests in each of four CI jobs ([run](https://github.com/HNNUYUXUAN/litz-wire-research/actions/runs/39293290975)).
