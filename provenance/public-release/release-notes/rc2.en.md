# Litz Wire Research v1.0.0-rc.2 — automation and frozen publications

This release preserves the automation research and manuscript artifacts. Its existing tag remains at [`15df5069e4f370c130ac0306bc65f441a64b7ad5`](https://github.com/HNNUYUXUAN/litz-wire-research/commit/15df5069e4f370c130ac0306bc65f441a64b7ad5). Artifact run identities and manifests identify the later manuscript attachments independently of that tag.

The [automation examples](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/automation/examples/README.md) cover six recorded cases: Wolfram modeling and Notebook creation, native Maxwell modeling and solving, Wolfram–Maxwell comparison, model extension, error diagnosis and repair, and interpretation of an unsuccessful physical check. Connection, tool execution, solver completion and scientific acceptance are recorded separately. The `automation-rc2` dataset restores their saved evidence through the current CLI.

## Current manuscript attachments

The selected publication set is `publication_review_20261015_03`, with 27 artifacts retaining the `review_20261015_` filename prefix:

- Eighteen PDFs: three works × two languages × three layouts (single-column journal, IEEE journal and IEEE conference).
- Six native Wolfram Notebooks: complete report, automation methods paper and physics paper, each in English and Simplified Chinese.
- Three ZIPs: the publication package, independently compilable LaTeX sources and visual candidates.

[Publications](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/publications/README.md) links the six complete Markdown manuscripts and individual attachments. The release also supplies `review_20261015_SHA256SUMS.txt`. Download `litz_publication_licenses_20261020.zip` alongside the frozen publication ZIPs; it supplies license texts, third-party notices and the member-level license index. Earlier source archives, references and example manuscripts remain under their original names.

The publication ZIP contains its build-time source snapshot. Use [rc.3](https://github.com/HNNUYUXUAN/litz-wire-research/releases/tag/v1.0.0-rc.3) for the maintained source, public downloader and current source CI. The catalog restores historical scientific evidence from [rc.1](https://github.com/HNNUYUXUAN/litz-wire-research/releases/tag/v1.0.0-rc.1). Public access and hash-verification observations are linked from the [distribution record](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/docs/open-source-readiness.md).

## Scientific scope and reuse

Seven modeling routes retain their assumptions, units, boundary conditions and recorded acceptance status. The frozen imposed-field RT0 cuboid evidence records final spatial loss changes of 0.655090% and 0.362916%, meeting its 1% refinement target. This concerns external-field absorption with zero net transport. The saved A–φ cylinder scalar-potential and gauge checks remain unsuccessful. Two-dimensional Maxwell automation and its bounded comparison retain their own evidence, separately from the historical native three-dimensional Ansys interface diagnostics. Realistic transposition ranking and experimental validation remain research directions. These are the preserved scientific records; this publication transition performs no solver or manuscript rebuild.

Original software uses MIT; original prose, figures and data use CC BY 4.0. Upstream components retain their own terms. Wolfram and Ansys are external licensed applications. See [licenses](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/LICENSES/README.md), [acknowledgments](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/ACKNOWLEDGMENTS.md) and [citation guidance](https://github.com/HNNUYUXUAN/litz-wire-research/blob/main/docs/citation-guide.md).
