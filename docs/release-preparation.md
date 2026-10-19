# Release preparation

[简体中文](release-preparation.zh-CN.md) · [Development](development.md)

Source maintenance, scientific builds and public distribution have separate identities. A preparation pass updates the repository's interfaces, documentation and release metadata, then records the checks for that source revision. New physical studies and manuscript rebuilds use their own run IDs and validation records.

## Identify the source and frozen publications

Record the exact source commit with `git rev-parse HEAD`. Keep its validation receipt alongside the release manifest. The current manuscript set is identified by `publication_review_20261015_03`: six complete bilingual manuscripts, six native Notebooks and eighteen PDFs. [Delivery hashes](../provenance/editorial/delivery-manifest.json) and [uploaded asset records](../provenance/editorial/online-assets.json) identify its files.

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

`docs/current-edition.json` must describe all three works in both languages, with three PDF layouts per document and a Notebook record. Check asset names and SHA256 identities against the delivery manifest. Preserve the historical rc.1 index and its original run identity. Validate dataset dependencies, object identities, file mappings, part order and hashes in `data/catalog.json` against the source records; restoring a selected dataset must reproduce those identities.

## Verify release assets

For every asset advertised by the publication index or dataset catalog, check its target repository, release tag, asset name, size and SHA256. Read back remote bytes or use a server-provided SHA256 that is explicitly bound to that asset; record the verification method. Preserve the original `review_20261015_` publication attachment names and hashes. Check individual PDFs and Notebooks, the publication and LaTeX packages, their checksum file, and dataset archive parts required by rc.1 and rc.2.

Inspect the repository, source packages and distributed archives for credentials, commercial-license credentials, personal machine paths and third-party notices. Apply the project's [license boundaries](../LICENSES/README.md) to original software, scholarly material and upstream components. Scientific applications and fonts are installed separately under their own terms.

## Transition to public distribution

The preparation baseline is a **Private** repository with **Draft** releases for `v1.0.0-rc.1` and `v1.0.0-rc.2`. `data/catalog.json` has `private: true`, and its attachment URLs use the protected GitHub release-asset API. Private restoration currently uses authenticated access. These states must be checked again at the final transition.

After the maintainer explicitly authorizes public release:

1. Confirm the reviewed source commit, release target commits, asset inventories and checksums.
2. Change the repository to Public and publish both required release records. A public repository alone does not make Draft release attachments anonymously downloadable.
3. Update catalog/download metadata for public access. Anonymous retrieval must work without GitHub credentials; any private-access fallback must retain bounded credential scope and strip authorization on cross-host redirects.
4. From a signed-out session and a fresh cache, test the README-to-publication download path, download representative PDF/Notebook/package assets, and restore a small dataset through the CLI. Verify their hashes after download. Check access to the remaining advertised assets and required archive parts.
5. Record the public URLs, visibility and release states, source commit and anonymous verification results. Keep the release notes consistent with the verified source and frozen manuscript identities.

Until those transition checks finish, the preparation records describe a candidate for public distribution. Source CI, scientific acceptance and anonymous download verification each retain their actual status.

## Attachment metadata audit tool

Save the GitHub repository and release API responses using the [snapshot format](release-snapshot.schema.json), then run:

```text
python tools/CheckReleaseReadiness.py --snapshot provenance/maintenance/release-snapshot-20261020.json --output outputs/release-check.json
```

The tool compares registered file identities with server SHA256 values in the snapshot and performs no download. A passing result means the attachment metadata matches; repository visibility, release publication, catalog access mode and anonymous readback have separate statuses. The saved snapshot replays this audit; obtain a fresh one for publication.
