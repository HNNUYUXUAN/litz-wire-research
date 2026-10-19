# Public release acceptance

[English](README.md) · [简体中文](README.zh-CN.md)

The repository and rc.1, rc.2 and rc.3 prereleases are public. The source release `v1.0.0-rc.3` identifies commit `01aa0bc3dc12a548301a148f8fc99e12a241e075`. These records capture the checks performed before and after publication on 20 October 2026 (Asia/Shanghai).

| Check | Result | Evidence |
| --- | --- | --- |
| Release source CI | Windows/Ubuntu × Python 3.11/3.12: four jobs passed, 59 tests each | [CI](ci-source.json) |
| Later public-navigation and verification-tools CI | Commit `76323f6`: the same four jobs passed, 74 tests each | [Maintenance CI](ci-maintenance.json) |
| Visibility and Release state | Public repository; all three prereleases published | [API metadata](repository-releases.json) |
| Release tag identities | rc.1 and rc.2 retain their original commits; rc.3 identifies the maintained source | [Remote refs](tag-identities.json) |
| Every rc.1/rc.2 attachment | 127 complete anonymous downloads, 8,578,518,566 bytes; all SHA256 values matched | [Download receipts](anonymous-assets.json) |
| Registered distribution assets | 66 evidence parts, 27 publication files and one license companion; all publication conditions satisfied | [Manifest audit](release-readiness.json) |
| Public rc.3 source archive | 972 files / 80,001,469 raw bytes match the exact Git commit | [Source receipt](verification/public-receipts/source-verification.json) |
| Installed CLI, fresh environment and cache | 874 analytic files restored; 679 unique objects / 660,867,640 bytes verified | [CLI receipt](verification/public-receipts/cli-restoration-verification.json) |

[Summary and receipt hashes](summary.json). The 127-asset check covers every uploaded attachment of rc.1 and rc.2, including historical files; its 94 registered assets are a subset. GitHub's automatically generated rc.3 source archive has a separate receipt. Download byte counts and restored-object byte counts describe different stages and should not be added together.

Saved release notes: [rc.1](release-notes/rc1.en.md), [rc.2](release-notes/rc2.en.md), [rc.3](release-notes/rc3.en.md). Each has a paired Chinese source in the same directory.

Attachment and source downloads used credential-free HTTPS, without cookies or environment proxy credentials. The installed CLI retained its actual parsing, download, extraction and restoration code; its HTTP transport was instrumented to reject credential headers and authentication subprocesses. Every advertised destination and cache was initially empty. The [reproduction guide](verification/INTEGRATION.md) documents that instrumentation and its scope.

Repository-authorized GitHub API metadata supplied asset identities after an unauthenticated API request hit its rate limit. Metadata retrieval and anonymous content downloads are distinct evidence. Download receipts contain full-body GET results and hashes; the manifest audit only checks supplied metadata and receipts. Local path tokens and the original/portable receipt hashes are documented in the [transformation manifest](verification/public-receipts/portable-receipts-manifest.json).

The source and CLI verification helpers were maintained after the rc.3 tag; the 14 offline tests for these helpers are separate from that tag's 59-test CI. The [independent package-binding audit](verification/public-receipts/installed-package-binding.json) also checks all 13 installed Python files against the immutable Git-tree inventory. Publication figures, PDFs, Notebooks, source ZIPs and scientific acceptance retain their frozen build/run identities. This release transition performed no new physical solve or manuscript build.

To replay the complete-attachment audit from the repository root, use a new output path:

```text
python tools/VerifyAnonymousReleaseAssets.py --snapshot provenance/public-release/repository-releases.json --output outputs/new-anonymous-downloads.json --all-assets --workers 4
python tools/CheckReleaseReadiness.py --snapshot outputs/new-anonymous-downloads.json --output outputs/new-release-audit.json
```

The stored metadata is a historical observation. Obtain a fresh repository/Release snapshot when checking a later distribution. Source and installed-CLI reproduction is documented in the [bilingual guide](verification/INTEGRATION.md).
