# Release preparation

[简体中文](release-preparation.zh-CN.md) · [Development](development.md)

Source maintenance, scientific builds and public distribution have separate identities. A preparation pass updates the repository's interfaces, documentation and release metadata, then records the checks for that source revision. New physical studies and manuscript rebuilds use their own run IDs and validation records.

## Identify the source and frozen publications

Record the exact source commit with `git rev-parse HEAD`. Keep its validation receipt alongside the release manifest. The maintained publication set is driven by [the LaTeX manifest](../manuscript/latex-publication.json): six bilingual LaTeX masters and six generated Markdown manuscripts, with a reading PDF for each master. [Current compilation and reading receipts](../provenance/current-publication/reading-receipt.json) select the build. Historical Notebook and multiple-layout attachments retain their original identities in the archival delivery records.

The publication ZIP contains the source snapshot and artifacts of that frozen build. Later changes to repository documentation, CI or download handling are represented by the current source commit. Cite both identities when using the current software with that publication package. Rebuilding a package requires a new artifact identity, hashes and applicable compilation/frontend checks.

## Verify the prepared checkout

Run these checks from a clean checkout with the `automation` extra installed:

```text
python -B tools/CheckSourceCheckout.py --output outputs/ci/source-checkout.json
python tools/BuildPublicationIndex.py --check
python tools/BuildAgentCatalog.py --check
python tools/CheckReaderLinks.py
litz-research references verify
```

Review each configured CI matrix result and retain failures or unavailable environments explicitly. The source checker exercises portable fixtures and metadata; native solver and publication receipts remain associated with the runs that produced them.

Check reader links against the tracked file set, rather than files present only on a developer's machine. Links to complete Markdown manuscripts and lightweight figures must resolve within the checkout. PDF, Notebook and ZIP links must resolve to the selected release assets. Regenerate indexes from the same download metadata and verify the result.

Validate all three works in both languages against `manuscript/latex-publication.json` and `provenance/current-publication/`. Check reading PDF and standalone source-package names and hashes against the selected build. Preserve historical publication indexes and original run identities. Validate dataset dependencies, object identities, file mappings, part order and hashes in `data/catalog.json`; a dataset may set `repository` to its archived GitHub owner/name, otherwise the top-level repository applies. Its public URL must exactly match that repository, source version and filename.

## Verify release assets

For every asset advertised by the publication index or dataset catalog, check its target repository, release tag, asset name, size and SHA256. Read back remote bytes or use a server-provided SHA256 that is explicitly bound to that asset; record the verification method. Preserve the original `review_20261015_` publication attachment names and hashes. Check individual PDFs and Notebooks, the publication and LaTeX packages, their checksum file, and dataset archive parts required by rc.1 and rc.2.

Inspect the repository, source packages and distributed archives for credentials, commercial-license credentials, personal machine paths and third-party notices. Apply the project's [license boundaries](../LICENSES/README.md) to original software, scholarly material and upstream components. Scientific applications and fonts are installed separately under their own terms.

## Publish a release and verify public access

For each release:

1. Confirm the source commit, release target commits, artifact inventories, license companion and checksums. Keep existing frozen artifact identities unchanged.
2. Make the repository Public, publish the maintained source release, and publish every Release required by the data catalog. The maintained source is `v1.0.0-rc.3`; the current catalog uses `v1.0.0-rc.1` for historical evidence and `v1.0.0-rc.2` for automation and publication assets. Preserve the existing rc.1 and rc.2 tag targets. A public repository alone does not make Draft release attachments anonymously downloadable.
3. Set the public catalog to `private: false`. Keep each part's API `url` for asset-ID verification and provide its verified browser download URL as `public_url`. Confirm that the CLI uses public URLs without reading credentials; older catalogs may fall back to anonymous API retrieval.
4. Verify the hosted CI matrix for the exact source commit. From a signed-out session and a fresh cache, walk the README-to-publication path and restore a small dataset through the CLI. Read back the advertised assets anonymously and verify the downloaded byte counts and SHA256 values; retain the scope and timestamp of each receipt.
5. Record the public URLs, repository visibility, Release states, source commit, CI results and anonymous download receipts. Keep release notes consistent with the maintained source and frozen manuscript identities.

The [distribution record](open-source-readiness.md) links the observations for the released revision. Historical snapshots retain the repository and Release states observed when they were captured. Source CI, scientific acceptance and public-download verification each have their own evidence.

## Attachment metadata audit tool

Save the GitHub repository and release API responses using the [snapshot format](release-snapshot.schema.json), then run:

```text
python tools/CheckReleaseReadiness.py --snapshot outputs/public-release-snapshot.json --output outputs/release-check.json
```

The tool compares registered file identities with server SHA256 values in the snapshot and performs no download. A passing result means the attachment metadata matches; repository visibility, release publication, catalog access mode and anonymous readback have separate statuses. The saved snapshot replays this audit; obtain a fresh one for publication.

Distribute the license companion with publication ZIPs; see the [license and member index](../LICENSES/publication-companion/README.md) and [supplemental asset hashes](../provenance/maintenance/supplemental-assets.json). See the [distribution record](open-source-readiness.md).
