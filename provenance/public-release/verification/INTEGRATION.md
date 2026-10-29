# Public source and installed CLI acceptance

These are post-publication acceptance tools. They do not publish anything or
install dependencies. They and the receipts are maintained after the rc.3 source
tag; their presence in that tag is not asserted. Run network acceptance only after
the repository and required releases are public and the source tag is present.
The commands below start in the current repository root. A tagged-source archive
has no `.git` directory; the expected source manifest must therefore be read from
a local Git checkout containing the specified commit.

## 1. Download and verify the tagged source

Use the exact 40-character commit behind the published tag. `--commit` is required;
the verifier has no fixed source commit. The destination directory must not exist.

```powershell
$repo = (Resolve-Path '.').Path
$tools = Join-Path $repo 'provenance/public-release/verification'
$python = (Get-Command python).Source
$commit = '01aa0bc3dc12a548301a148f8fc99e12a241e075'
$acceptance = Join-Path $repo 'outputs/public source acceptance'
& $python "$tools/VerifyPublicSource.py" --root $repo --commit $commit --tag 'v1.0.0-rc.3' --directory $acceptance
```

The helper uses only local Git object reads to build its expected inventory. It
then downloads a fresh GitHub tag ZIP through a credential-free HTTPS opener,
compares every archive file against raw committed bytes, and extracts only after
the complete inventory and all hashes match. Symlinks, unexpected members,
traversal, Windows name hazards, collisions and an existing extraction directory
are rejected. The receipt is `source-verification.json`; source is extracted to
`source checkout/`.

## 2. Install the verified source in a fresh virtual environment

The caller performs this separate dependency installation. This is preparation,
not anonymous-download evidence. Keep the new environment outside the extraction
directory. Do not use system site packages or reuse an existing environment.

```powershell
$source = "$acceptance/source checkout"
$venv = "$acceptance/clean environment"
& $python -m venv $venv
& "$venv/Scripts/python.exe" -m pip --isolated install --disable-pip-version-check --no-cache-dir --index-url 'https://pypi.org/simple' --report "$acceptance/pip-install-report.json" $source
```

## 3. Run the actual installed CLI with fresh data and cache

```powershell
& "$venv/Scripts/python.exe" "$tools/VerifyAnonymousCLI.py" --source $source --directory "$acceptance/cli restoration acceptance"
```

The helper requires a virtual environment, rechecks all committed source bytes
from the source receipt, and projects the exact package `.py` inventory from that
receipt's committed Git file list. Both the current source package and installed
package must match that inventory and its hashes, including rejection of added
Python files. It invokes the real `litz_research.cli.main` with:

```text
--project <source checkout> data fetch analytic --cache <new empty object cache>
```

The CLI's parameter parsing, catalog selection, part download, object extraction,
dependency recursion and destination restoration execute normally. The HTTP
transport is explicitly instrumented to disable environment proxies, reject
credential headers, accept only trusted GitHub HTTPS redirects and record request
header names plus HTTP statuses. Signed query strings are omitted from records.
Subprocess execution is blocked during this command, including any `gh auth`
attempt. Existing destination files or a reused cache cannot satisfy acceptance.

The receipt `cli-restoration-verification.json` includes the commit, catalog and
installed-code identities, actual CLI result, every part hash, anonymous request
records, `data.verify` results for analytic and all recursive dependencies, and
independent post-run hashes of every dependency cache object. The research-shared
dataset supplies cache objects; it has no direct destination file records.
The expected file totals are derived from the committed catalog (currently 874
analytic file records); the script does not substitute a hardcoded count for
verification. It starts no physical solve.

## Offline tests

```powershell
Push-Location $tools
& "$venv/Scripts/python.exe" -m unittest -v test_public_source test_anonymous_cli test_portable_receipts
Pop-Location
```

Fourteen tests exercise exact raw ZIP bytes, missing/extra/traversal members, symlinks,
case collisions, overwrite rejection, proxy and credential handling, a real CLI
restoration using synthetic HTTP streams, corrupted response bytes, attempted
authentication subprocesses, dependency cycles, modified installed code, extra
source/installed Python files and portable receipt transformations. They make no
network requests.

## Portable receipt copies

Keep the original receipts at their original locations. This command requires a
new output directory and produces separate copies plus a transformation manifest:

```powershell
& "$venv/Scripts/python.exe" "$tools/SanitizePublicReceipts.py" --acceptance-root $acceptance --output "$acceptance/portable public receipts"
```

`${ACCEPTANCE_ROOT}` replaces the absolute acceptance directory and
`${PYTHON_BASE}` replaces the base Python installation path. JSON file-URI paths
are transformed by the same rule. All hashes, counts, statuses and public HTTPS
request URLs remain unchanged. The manifest records exact raw-byte SHA-256 values
for both original and portable files; embedded references to raw receipt hashes
continue to identify the originals. The reviewed portable copies are stored under
`public-receipts/` beside these scripts. A fresh reproduction must use another
output directory rather than overwrite the published receipts.
