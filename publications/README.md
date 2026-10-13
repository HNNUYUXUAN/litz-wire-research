# Research publications

The complete bilingual reports and papers below retain their frozen scientific source identity. Lightweight previews are available directly in Git. The approved Chinese paper specimen records the editorial and plotting convention for the next scholarly edition.

| Edition | Read | Download PDF |
| --- | --- | --- |
| paper / zh-CN | [Markdown](paper/zh-CN/README.md) | [paper_zh-CN_single.pdf](https://github.com/HNNUYUXUAN/litz-wire-research/releases) |
| paper / en | [Markdown](paper/en/README.md) | [paper_en_single.pdf](https://github.com/HNNUYUXUAN/litz-wire-research/releases) |
| report / zh-CN | [Markdown](report/zh-CN/README.md) | [report_zh-CN_single.pdf](https://github.com/HNNUYUXUAN/litz-wire-research/releases) |
| report / en | [Markdown](report/en/README.md) | [report_en_single.pdf](https://github.com/HNNUYUXUAN/litz-wire-research/releases) |

The candidate Release is private and draft; use authenticated GitHub access. Full Notebooks, figures and historical evidence are restored with `litz-research data fetch academic-editions`. The mount is `data/evidence/v1.0.0-rc.1/`; original relative paths are preserved.

[Approved specimen](../docs/revision-sample-review.zh-CN.md) · [Editorial convention](../manuscript/style.json) · [Citation guide](../docs/citation-guide.md)

Download a single PDF from the authenticated draft / 从授权草稿获取单份 PDF：

```powershell
gh release download v1.0.0-rc.2 --repo HNNUYUXUAN/litz-wire-research --pattern paper_zh-CN_single.pdf --dir build/reading
```

Use the exact filename from the table for the other editions. The approved specimen is `approved_paper_zh-CN.pdf`; the current citation-chain compile is `paper_zh-CN_rc2_reference.pdf`.
