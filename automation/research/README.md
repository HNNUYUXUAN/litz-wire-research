# Research discovery and acquisition

The four research skills connect literature and software discovery to the existing modeling workflows. They use the available host search, GitHub and Chrome tools, with Tencent Yuanbao preferred for broad web discovery. Provider credentials remain local.

`upstreams.lock.json` distinguishes reviewed candidates from modules undergoing local validation. The academic-search MIT modules are pinned before use; retain its LICENSE and original file identities in any redistributed snapshot. Its OA helper handles open access. Institutional WebVPN acquisition uses the host browser workflow in `paper-acquire`.

Source records are a JSON array. Each record has `id`, `title`, canonical `url`, `retrieved_at`, `provider`, `kind`, `access_status`, `identity_status` and `redistribution`. Downloads add relative `local_path`, `sha256` and `media_type`. Adopted software adds `commit`, `license`, `copyright`, `original_files`, `modifications` and `use`. Full-text publication additionally requires `rights_evidence` and verified identity.

Validate with `python -m litz_research.research_records records.json --root .local-library`. Keep local papers and browser session details outside public artifacts. Identity verification requires reading the document; byte validation is a separate check.

Run representative DOI, broad-topic, Chinese/English, duplicate/conflicting metadata, service-failure and institutional-session cases before claiming operational coverage. Compare tool calls, elapsed time, observable tokens and human interventions under equal task/tool conditions. Missing measurements remain null.

## Pinned helper commands

```bash
node automation/research/vendor/academic-search/scripts/academic-records.mjs validate --input records.json --output validation.json
node automation/research/vendor/academic-search/scripts/academic-records.mjs dedupe --input records.json --output normalized.json
node automation/research/vendor/academic-search/scripts/oa-pdf-download.mjs --input papers.json --manifest acquisition.json --out-dir .local-library --download
node --test automation/research/vendor/academic-search/scripts/*.test.mjs
python -m litz_research.research_citations normalized.json --root . --output selected.bib
```

Citation export selects reviewed entries from `references/library.bib` by DOI, preserving established citation keys. Adopt new records there after verifying their metadata. The adjacent provenance JSON retains provider field sources and normalization conflicts. The vendor's `field_sources` uses `source_url`, `checked_at` and `evidence_type`; the local acquisition validator uses public `url` and a human-readable `locator`. These are separate input contracts; retain the vendor record alongside the local acquisition record.

The snapshot contains its MIT license, original tests and fixtures, plus a per-file SHA256 provenance manifest. Tests were also run under the Conda research runtime (Node 24.22.1).
