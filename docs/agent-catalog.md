# Research discovery catalog

[English](agent-catalog.md) · [简体中文](agent-catalog.zh-CN.md)

Use [the machine catalog](agent-catalog.json) to find a physical route, research workflow, recorded automation case or complete manuscript. [llms.txt](../llms.txt) provides a short introduction; [llms-full.txt](../llms-full.txt) adds the registered entries and their reading paths.

From the repository root, search without installing Python packages or starting a solver:

```bash
python tools/BuildAgentCatalog.py --search "common_terminal"
python tools/BuildAgentCatalog.py --search "解析"
python tools/BuildAgentCatalog.py --show case/aphi-diagnostics
python tools/BuildAgentCatalog.py --show manuscript/automation/en
```

The standard-library tool requires Python 3.11+ and Git. Searches match all whitespace-separated terms, case-insensitively, against identifiers, titles, summaries, model interfaces, reference keys and saved status fields. A match returns complete JSON entries. No match returns an empty list and exit code 1. `--root PATH` selects another checkout, including a path containing spaces.

## Stable identities and source records

| Identity | Registration | Read next |
| --- | --- | --- |
| `route/<route>` | `configs/research_entries.json` | Bilingual text/CLI guide, saved parameters and implementation |
| `adapter/<route>` | `configs/research_entries.json` | Wolfram, ANSYS and GPU text/CLI entry points |
| `skill/<name>` | `automation/skills/*/SKILL.md` | Skill entry point and on-demand references |
| `workflow/<directory>` | Paired READMEs under `automation/workflows/` | Inputs, procedure and completion criteria |
| `case/<case>` | `automation/examples/verification.json` and each `task.json` | Visible tool events, execution record and actual code differences |
| `manuscript/<edition>/<language>` | `docs/current-edition.json`, `publications/manifest.json` and delivery records | LaTeX main, section sources, generated Markdown and input identities |

Current identifiers cover seven physical routes, three adapters, nine skills, five workflows, six recorded cases and six complete manuscripts. Case titles and status identifiers retain the wording of the recorded task. Bilingual case explanations are in the [examples guide](../automation/examples/README.md) and [Chinese guide](../automation/examples/README.zh-CN.md).

`reference_keys` points to the canonical [bibliography](../references/library.bib); [sources.json](../references/sources.json) records actual use. The catalog does not maintain a second bibliography. Source chapters are authoring inputs, while the manuscript entry points to the complete reading edition.

## File identities and recorded results

Every tracked resource includes a repository-relative path, reading/raw URLs, byte size and SHA-256. `hash_basis: raw-bytes` means the hash covers the exact working-tree file bytes with no newline or Unicode normalization. The repository's `.gitattributes` preserves these bytes. URLs follow `main`; when citing a result, use the actual commit read and the resource hash.

The generator reads only paths listed by Git and explicitly registered sources. It does not open ignored `outputs/` or restored `data/evidence/` artifacts, run calculations, download releases or probe local licenses. `input_resources` binds the files read to their exact hashes; no build date or current Git HEAD is embedded, so unchanged input bytes produce identical output.

`recorded_runs` preserves execution and physical acceptance separately. Manuscript `resources` identify the LaTeX master and generated reading; `chapter_sources` and `input_hashes` bind sections and all build inputs. `historical_releases` links to retained release identities.

## Updating and checking

```bash
python tools/BuildAgentCatalog.py
python tools/BuildAgentCatalog.py --check
```

The build writes `docs/agent-catalog.json`, `llms.txt` and `llms-full.txt`. `--check` writes nothing and returns 1 with the changed/missing output paths if regeneration is needed. Invalid registration, missing tracked input or a manuscript-preview hash mismatch returns 2. Update the source registry or source document first, rebuild, and include generated changes in the same commit.

For inspection in a separate directory, use `--output-dir PATH`; `--check` can compare against the same directory. Search and exact lookup never write files. The repository-design references used for this interface are recorded in [the source comparison](../provenance/maintenance/repository-patterns.json).
