---
name: research-scout
description: Investigate a scientific question across literature, software, forums and reusable agent skills, with source-backed evidence and implementation options.
---

Establish the question, domain, comparison, date range and available budget from the request and project context. Read existing bibliography and research records before repeating searches.

Use Tencent Yuanbao for broad discovery when available; fall back to the host search tool when unavailable or insufficient. Use scholarly APIs for DOI and publication metadata. Inspect repositories with the connected GitHub tool and the user's configured Gitee API. Search SkillHub and skills.sh for discovery, then verify the original repository and license. Forum posts supply leads and operational experience; technical claims require primary evidence.

Use the pinned academic-search modules described in [the workflow reference](references/workflow.md) for record normalization and the project citation-export adapter for reviewed bibliography entries. Load only the domain and provider references needed. Preserve conflicting metadata; deduplicate by stable identifiers rather than title similarity alone.

Deliver a Markdown research brief, structured source records, a comparison of reusable implementations, and unresolved questions. Separate read evidence from hypotheses and proposed experiments. Record query/provider/time and source locators; reuse cached evidence only with an explicit retrieval date. Record observable elapsed time, calls and tokens; unavailable usage remains null.

For full text use paper-acquire; for adopting source use research-reuse; for executable follow-up use research-handoff. The installed host tools determine available capabilities. These skills currently have Litz-case integration scope; record each additional validation case explicitly.
