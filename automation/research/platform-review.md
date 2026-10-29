# Platform discovery and primary-source review

Reviewed on 2026-10-28. Tencent Yuanbao supplied discovery leads; repository content and original documentation were checked separately. This review records candidates, not additional installed backends.

| Discovery route | Primary source and fixed identity | Verified scope and decision |
| --- | --- | --- |
| GitHub | [academic-search](https://github.com/ustc-ai4science/academic-search/tree/b9b692ed1334c858eb42d1f2710ccfcae1a43eb8) | MIT snapshot adopted for record normalization and OA acquisition; original files, license and hashes retained locally in the vendor directory. |
| skills.sh | [LangChain arxiv-search](https://github.com/langchain-ai/deepagents/tree/7e4e55a70447edc1219358940181856e39153736/libs/code/examples/skills/arxiv-search) | Original skill and Python helper inspected. MIT, copyright LangChain, Inc.; requires `arxiv`. The helper returns title/summary text; its CLI calls the function without printing the returned value at this revision. Evaluated as a candidate; project integration uses the existing retrieval workflow. |
| SkillHub | [K-Dense citation-management](https://github.com/K-Dense-AI/scientific-agent-skills/tree/5f2bc0341354fd5590aef76a533ada1e1e5b4e62/skills/citation-management) | Original skill declares version 2.3, Python 3.9+ and requests, with scholarly optional for Google Scholar. [MIT license](https://github.com/K-Dense-AI/scientific-agent-skills/blob/5f2bc0341354fd5590aef76a533ada1e1e5b4e62/LICENSE.md), copyright 2025 K-Dense Inc., read at the fixed revision. Citation validation remains a reviewed supplementary candidate. |
| Gitee | [MindSpore MindScience](https://gitee.com/mindspore/mindscience/tree/2311346cf057742c35b0e64a58e343d85e245802) | Repository metadata and LICENSE fetched using the existing local API helper. Apache-2.0 license blob `261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64`; a scientific-computing candidate, with no local solver integration claimed. |
| FEMM forum | [Series–parallel conductor discussion](https://groups.io/g/femm/message/7204), 2021-10-21 | Search result supplied a lead about Litz winding assumptions. Direct forum retrieval failed in the web tool; no forum text is redistributed or treated as validated scientific evidence. The relevant material and circuit definitions were checked against the author’s manual. |

The [SkillHub source page](https://skills-hub.ai/sources/scientific-skills) points to the K-Dense repository under its earlier `claude-scientific-skills` name. Counts and mirror descriptions are discovery metadata; the fixed original files above define the assessed capability.

The [FEMM 4.2 manual](https://www.femm.info/doku/lib/exe/fetch.php?media=upload:documentation:manual.pdf), David Meeker, 2018-01-30, pp. 31–32, defines bulk winding parameters and impedance-based parallel circuit constraints. This supports checking the model’s current/voltage assumptions; it does not validate arbitrary finite-length transposition geometry. Software access, code license, paper access and redistribution rights are recorded separately.

Local source responses and license texts are retained in `outputs/research_online_20261028_01`. Public provenance contains canonical URLs and fixed identities. The evaluated skill source files are not incorporated into the distributed implementation.
