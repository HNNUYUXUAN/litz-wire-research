---
name: paper-acquire
description: Obtain and verify a requested academic paper through open sources or an authorized institutional browser session, retaining acquisition provenance.
---

Resolve DOI, title, authors and edition before downloading. Prefer publisher-authorized open access, arXiv and institutional repositories. Use the academic-search OA helper documented in [the workflow reference](references/workflow.md) for supported open URLs.

For institutional access, use the host Chrome tools with the user's authorized existing WebVPN session and locally configured portal. Inspect the current page before acting. Keep authentication inside the browser; do not export cookies or session URLs into source records. On authentication expiry, record access_status=session_expired with failure_reason and preserve progress. A login page is not a downloaded paper.

Save full text under the ignored .local-library directory. Verify PDF signature, title/DOI and edition, then record SHA256, canonical public URL, provider, retrieval time and local relative path. Separate access_status, identity_status and redistribution. File signature and matching hash alone do not prove paper identity.

Validate records with python -m litz_research.research_records RECORDS --root EVIDENCE_ROOT. Public artifacts contain metadata and permitted excerpts; distributing full text requires documented redistribution rights. Report exact missing steps when access or identity verification is incomplete.
