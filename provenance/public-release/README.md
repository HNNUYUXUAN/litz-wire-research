# Public release acceptance

[English](README.md) · [简体中文](README.zh-CN.md)

The repository and rc.1, rc.2 and rc.3 prereleases are public. Source tag rc.3 identifies `01aa0bc3dc12a548301a148f8fc99e12a241e075`; its [four-job CI](ci-source.json) passed 59 tests per job. [Repository and Release metadata](repository-releases.json) records publication state.

The [anonymous source download](verification/public-receipts/source-verification.json) matched all 972 committed files. The [installed CLI](verification/public-receipts/cli-restoration-verification.json) restored 874 analytic files in a fresh environment and cache, then verified 679 data objects. The [independent package audit](verification/public-receipts/installed-package-binding.json) bound all 13 installed Python files to the Git tree. See the [reproduction guide](verification/INTEGRATION.md) and [portable receipt identities](verification/public-receipts/portable-receipts-manifest.json).

The complete 127-asset download is in progress. Its full-body byte counts and hashes will be added when all downloads finish. The API metadata snapshot was read with repository authorization after an unauthenticated API request was rate limited; content downloads use separate credential-free HTTPS requests. This transition performs no physical solve or manuscript rebuild.
