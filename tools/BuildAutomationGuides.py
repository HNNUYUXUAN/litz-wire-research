"""Build maintained project navigation, portable workflows and skill resources."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]

def put(relative,text):
    p=ROOT/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.strip()+'\n',encoding='utf-8')

def main():
    if (ROOT/'automation/examples/verification.json').exists():
        raise SystemExit('Guide bootstrap is complete. Maintain the published workflow/architecture Markdown directly.')
    put('AGENTS.md','''# Litz research workflow

Read README, the selected route README, docs/建模约定与解析基准.md and tests/ACCEPTANCE.md. Use automation/workflows for reproduction, model extension, comparisons, diagnosis or scholarly output.

SI calculations; exp(+jωt); RMS phasors; copper σ=58 MS/m, μr=1, 20 °C. Main transport case: 200 kHz, 20 A RMS. Q1 diameter 2 mm is a calibration case with Jdc≈6.366 A/mm²; final Q2 nominal copper area is at least 5 mm².

Solve common-terminal voltage and total complex current. Preserve strand identity, actual arc length, return/boundary assumptions, complex currents, absolute Rac, Rac/Rdc and power. Traditional multilevel Litz is the strong baseline. Ranking requires improvement exceeding numerical uncertainty.

Use the shared CLI/Notebook task interface. Write source and inputs before formal execution. Choose explicit tutorial/campaign cases and unique run IDs. Record source hashes, versions, parameters, assumptions, execution status, physical acceptance and failures. Never treat tool success as physical validation.

Budget: eight logical processors, 24 GiB task memory, 8 GiB free system reserve; Student license limits additionally apply. Manage only processes created by the task and bind process ownership to creation identity. Preserve original evidence and independent user modifications.

Use official Wolfram and PyAEDT MCP versions from automation/mcp/upstreams.lock.json. Inspect available tools and actual responses. Use asynchronous jobs for long tasks. Resume only from verified inputs/checkpoints; otherwise create a linked new run. State missing runtime capabilities accurately.

Reference keys come from references/library.bib. Record actual use and license in references/sources.json. Third-party snapshots retain copyright. Public examples use portable paths and sanitized visible tool records.
''')
    workflows={
      'reproduce':('Reproduce a recorded model','复现已有模型','Select a model, explicit case and evidence dataset. Verify source identity and physical assumptions. Run doctor and dry-run, execute into a new run, inspect checks and compare only matching observables.','选择模型、案例和证据数据集，核对来源与假设；完成环境检查和预检后使用新运行号执行，解释验收并比较一致的观测量。'),
      'extend-model':('Extend a model with verification','扩展模型并验证','State the new capability and unchanged scientific conventions. Read the equations and implementation. Save a focused code change, add independent physical/regression checks, run original and new cases, explain scope and unresolved uncertainty.','说明新增能力与物理条件，阅读方程和实现；保存代码差异，增加独立物理及回归检查，运行原案例与新案例，解释适用范围与不确定性。'),
      'compare-solvers':('Compare matching field models','比较一致的场模型','Align geometry, copper area, material, frequency, RMS/peak convention, axial length, terminal constraints, return and boundaries. Solve independently. Compare complex currents, power and Rac with discretization and geometry differences visible.','对齐几何、铜面积、材料、频率、RMS/峰值、轴向长度、端口、回流和边界；独立求解后比较复电流、功率与 Rac，同时报告离散和几何差异。'),
      'diagnose':('Diagnose and recover a failed run','诊断失败并恢复','Preserve the original failure and actual tool response. Separate transport, API, solver, resource and physical failures. Test the smallest relevant correction, record its rationale and code diff, rerun with a new identity, compare acceptance without weakening tolerances.','保留原失败和工具响应，定位协议、API、求解、资源或物理问题；验证最小相关修正，记录依据与差异，使用新身份重跑并核对原验收条件。'),
      'report':('Build evidence-backed research output','构建有证据支持的研究成果','Use explicit accepted or diagnostic run identities. Read results and assumptions, preserve units and complex quantities, generate traceable figures, cite the canonical library, build and visually inspect the requested documents.','选用明确的验收或诊断运行身份，核对结果、假设、单位和复数；生成可追溯图件，引用统一题录，构建并实际阅读所需文档。'),
    }
    for key,(en,zh,body_en,body_zh) in workflows.items():
        for lang,title,body in [('en',en,body_en),('zh-CN',zh,body_zh)]:
            put(f'automation/workflows/{key}/'+('README.md' if lang=='en' else 'README.zh-CN.md'),f'''# {title}

{body}

Inputs: research question, selected model/case, physical conditions, source/evidence identities and resource budget.

Outputs: request.json, parameters.json, run_manifest.json, logs, results.json, test evidence, code diff when relevant, and a concise scientific explanation.

Use `litz-research models`, `litz-research run <model> --case tutorial --dry-run`, and `litz-research jobs submit/status/cancel/resume`. Read the route guide before a full campaign.

Completion: reproducible inputs and source, actual execution evidence, correct scope and an explicit acceptance state. Refer to tests/ACCEPTANCE.md and references/README.md.
''')
        put(f'automation/skills/litz-{key}/SKILL.md',f'''---
name: litz-{key}
description: {en} in the Litz research checkout using its scientific conventions, shared run interface and traceable evidence.
---

{body_en}

Find the checkout from pyproject.toml and configs/reference_parameters.json. Read AGENTS.md, the selected route guide and automation/workflows/{key}/README.md. Use explicit model/case and supported parameters. The complete procedure and output contract live in that workflow guide.

Inspect the available MCP tools. Wolfram operations use the fixed AgentTools server; Maxwell operations use the fixed PyAEDT-MCP server and the project Student connector when applicable. Save formal source and inputs, then execute through the bounded runner. Read actual return values and result files, including semantic API errors returned as text.

Long tasks use unique run IDs and status queries. Preserve failures and link revised runs. Report execution and physical acceptance independently, with the model assumptions and scientific limits.
''')
    put('automation/README.md','''# Agent-driven modeling and simulation

Start with a research question and a checked physical contract. The agent reads the selected model and evidence, uses Wolfram or Ansys MCP to explore and construct the model, saves the source, schedules the bounded solver, evaluates independent checks, and explains the result or next diagnostic step.

```mermaid
flowchart LR
  Q[Question and constraints] --> H[Codex / MCP client]
  H --> W[Research workflows and skills]
  W --> M[Wolfram / PyAEDT MCP]
  M --> R[Source and bounded runner]
  R --> V[Results and scientific checks]
  V --> H
  V --> D[Notebook, figures and publications]
```

Use [Codex setup](harnesses/codex/README.md), [generic MCP setup](harnesses/generic/README.md), and the [fixed upstreams](mcp/upstreams.lock.json). The [examples](examples/README.md) contain actual task and tool evidence. [Workflows](workflows/reproduce/README.md) cover reproduction, extension, comparison, diagnosis and reporting.

Protocol initialization, tool execution, solver execution and physical acceptance have separate records. A fresh model run reproduces saved code and inputs; agent-generated revisions can vary and must satisfy the same scientific checks.
''')
    put('automation/README.zh-CN.md','''# 智能体驱动建模与仿真

从研究问题与物理约束开始：智能体读取模型和证据，通过 Wolfram 或 Ansys MCP 探索并建立模型，保存源码，调用受资源限制的运行器，检查独立验收，然后解释结果或继续诊断。

入口为 [Codex 配置](harnesses/codex/README.md)、[通用 MCP 配置](harnesses/generic/README.md)、[固定上游](mcp/upstreams.lock.json)及[完整案例](examples/README.md)。工作流覆盖复现、模型扩展、跨求解器比较、失败诊断和科学成稿。

连接、工具调用、求解执行和物理验收分别记录。保存的源码与输入用于确定性复现；智能体的开发过程允许不同实现，但需要满足相同科学验收。
''')
    put('automation/harnesses/codex/README.md','''# Codex reference harness

1. Clone this checkout and install `python -m pip install -e ".[automation]"` in a virtual environment.
2. Install licensed Wolfram/AEDT separately. Follow the fixed MCP setup guides.
3. Generate inspectable configuration with `litz-research automation configure --output build/codex-config --ansys-python <Python in the Ansys MCP environment>`.
4. Inspect and merge the generated TOML into the selected project `.codex/config.toml`; keep local executable paths out of Git. Refresh the client, list active tools and run both protocol probes.
5. Install the desired folders under automation/skills into the client's skill directory or read their SKILL.md explicitly. The root AGENTS.md supplies the shared research conventions.
6. Submit a concrete task from automation/examples. Observe actual tools, inspect the code and result artifacts, and read physical acceptance separately.

For long execution: `litz-research jobs submit peec --case tutorial --run-id peec_job_01`, then `jobs status peec_job_01`. `jobs cancel` requests cancellation; `jobs resume --new-run-id` restarts from saved input under a linked identity.

Reference verification uses Codex orchestrating the standard MCP client in automation/mcp/client.py and the official Wolfram tools. Native client registration is checked separately from this bridge. Model and client versions are recorded only when observable.
''')
    put('automation/harnesses/generic/README.md','''# Other agent clients

The portable contract consists of MCP STDIO/HTTP configuration, the research workflows, saved parameter files and the local CLI. A client must support MCP initialization, tool discovery and tool calls, and provide access to the checkout. Read AGENTS.md and the relevant SKILL.md explicitly when automatic instruction discovery differs.

Generate `mcp.json` with `litz-research automation configure`. Map its server command/args/cwd or HTTP URL to your client's configuration. Check paths and available tools; run automation/mcp/client.py as the independent protocol probe.

The workflow does not depend on Codex thread IDs or private conversation history. Results and source hashes, rather than a particular prompt response, determine scientific reproducibility. Other harnesses remain unverified until their own end-to-end records are supplied.
''')
    for server in ['wolfram','ansys']:
        setup=('Install Wolfram/AgentTools 2.2.0 from the pinned source or paclet. Set LITZ_WOLFRAM_KERNEL to the licensed Wolfram executable. The server entry is PacletSymbol["Wolfram/AgentTools","Wolfram`AgentTools`StartMCPServer"]["WolframLanguage"].'
               if server=='wolfram' else 'Create a Python 3.12+ environment, install PyAEDT 1.8.0 and the fixed ansys/pyaedt-mcp commit from upstreams.lock.json. Use adapters/ansys/StartMCP.py with LITZ_AEDT_EDITION=student for the explicit Student connector. Start OwnedAEDTSession.py, read its port receipt, and call connect_to_aedt using the matching version. CPython/PyAEDT code uses run_python_code; AEDT RunScript has a different runtime.')
        put(f'automation/mcp/{server}/README.md',f'''# {server.title()} MCP setup

{setup}

Use the [fixed upstream manifest](../upstreams.lock.json), retain the upstream license, and lock the environment with `python -m pip freeze` after verification. Configure through the generated project templates. STDIO is the default; Ansys also supports HTTP bound to 127.0.0.1.

Run `litz-research automation probe {server} --run-id {server}_mcp_probe_01`. Inspect initialize, tools/list and tools/call events. Tool errors may be text; check actual solver files and numerical acceptance. Long simulations use bounded jobs and status queries.

Uninstall this integration by removing its generated client entries and project virtual environment. Existing scientific applications and other MCP configurations are independent installations.
''')
    examples=[('wolfram-calibration','Build and verify a Bessel Notebook through Wolfram MCP'),('ansys-native','Build and solve seven common-terminal strands through Ansys MCP'),('cross-solver','Compare matching Wolfram and Maxwell seven-strand cases'),('frequency-extension','Extend the analytical case to a frequency study with integral regression'),('diagnosis','Diagnose the explicit Student connector and native material-setting failures'),('aphi-diagnostics','Recompute preserved A-phi field diagnostics and report failed gates')]
    for name,task in examples:
        p=ROOT/'automation/examples'/name/'task.json';p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps({'id':name,'task':task,'harness':'Codex with standard MCP client bridge','scientific_conventions':'SI, exp(+j omega t), RMS','resource_policy':{'cpu_threads':8,'task_memory_GiB':24,'system_free_GiB':8},'evidence':'See the versioned acceptance report; actual records are bound by run ID and hash.'},indent=2)+'\n',encoding='utf-8')
    put('automation/examples/README.md','# Complete automation examples\n\n'+ '\n'.join('- ['+n+']('+n+'/task.json): '+t for n,t in examples)+'\n\nActual protocol events and solver files are versioned attachments. The source, parameters, tool requests, repairs and acceptance records provide the replay contract.')
    style={'approved_specimen_run_id':'publication_20261013_paper_sample_09','approval':'User approved the complete specimen after reviewing figures 4, 5, 9 and 10','fonts':{'zh-CN':'SimSun','latin':'Times New Roman'},'independent_figure_width_mm':88.9,'composed_figure_width_mm':182,'caption_title_alignment':'center','caption_description_alignment':'left','panel_letters':'above panels','independent_figure_box_pt':[252,198],'source_review':'docs/revision-sample-review.zh-CN.md','scope':'Approved specimen and reusable editorial/plotting convention; full scholarly edition propagation is a subsequent stage'}
    (ROOT/'manuscript/style.json').write_text(json.dumps(style,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    put('docs/automation-architecture.md','''# Architecture and extension

Automation workflows describe research decisions; adapters connect software; models implement physics. `litz_research.tasks` owns explicit cases, parameters, source manifests and bounded execution. CLI, MCP Python/Wolfram calls and native research Notebooks invoke this shared contract.

Add a case by implementing its scientific operation in the route source, declaring supported parameters in tasks.DEFAULTS/parameters, saving assumptions and structured results, and adding independent checks. Add its bilingual explanation in BuildResearchEntrypoints, then regenerate and evaluate the research Notebooks. A new backend changes adapters and must match the same input, unit and result contract.

Legacy src entries forward to maintained route/tool implementations. Historical source snapshots retain the code actually used for each frozen run. Source capture covers models, adapters, shared, automation, python, tools and configs.

Historical data fetch restores into data/evidence/<catalogue tag>/<original relative path>. The archive's logical paths, run IDs and hashes remain original. New runs use outputs/<run_id>. Missing evidence identifies the dataset fetch command; a new solver run is never silently substituted for a missing historical file.

The task runner records process creation identities, resource samples and true exit status. Cancellation is a request to the owning worker. Restarting a saved request uses a new run identity; model-specific checkpoint continuation requires an explicit verified checkpoint implementation.
''')
    put('docs/citation-guide.md','''# Cite the software, data and workflow

Use CITATION.cff for the released project, identifying the version and commit. Cite a dataset by repository/release, dataset name, source run ID and manifest hash. Cite the automation method through docs/automation-architecture.md and its release/commit. These identities support precise reproduction without a DOI.

Use references/library.bib for methods and upstream software; references/sources.json records actual roles and use. The generated references/README.md, ACKNOWLEDGMENTS and THIRD_PARTY_NOTICES expose the same identities. Retained reviewed repositories are labeled read-only; dependencies and adapted files carry their own status and license.

Bibliographic keys are stable. Display numbers follow first citation in each complete edition, share a bilingual mapping and are inherited by chapter excerpts. Generated BibTeX compatibility files are exports of the canonical library.
''')
    put('CITATION.cff','''cff-version: 1.2.0
message: "Cite this software version, the source run and dataset manifest used, and the relevant modeling references."
type: software
title: "Litz Wire Research: agent-driven reproducible modeling and simulation"
version: 1.0.0-rc.2
authors:
  - family-names: Miao
    given-names: Yuxuan
    affiliation: Huainan Normal University
repository-code: "https://github.com/HNNUYUXUAN/litz-wire-research"
url: "https://github.com/HNNUYUXUAN/litz-wire-research"
license: MIT
keywords:
  - agent-driven simulation
  - MCP
  - Litz wire
  - reproducible research
''')
    for lang in ['en','zh-CN']:
        title='Litz Wire Research' if lang=='en' else 'Litz Wire Research：智能体驱动建模与仿真'
        intro=('A reproducible scientific modeling workflow driven by Codex or another MCP-compatible agent, with Litz-wire loss as a complete research case.' if lang=='en' else '以 Codex 或其他支持 MCP 的智能体驱动可复核科学建模，以 Litz 线损耗提供完整研究案例。')
        text=f'''# {title}

**Miao Yuxuan / 缪雨轩 · Huainan Normal University / 淮南师范学院**

{intro}

[English](README.md) · [简体中文](README.zh-CN.md) · [Automation](automation/README.md) · [Publications](publications/README.md) · [Sources and acknowledgments](references/README.md)

```mermaid
flowchart LR
  Q[Research question] --> A[Codex / MCP agent]
  A --> M[Wolfram / Ansys MCP]
  M --> S[Saved model and bounded solver]
  S --> V[Independent scientific checks]
  V --> A
  V --> N[Notebook and research findings]
```

## {'From a question to evidence' if lang=='en' else '从研究问题到计算证据'}

{'Ask the agent to construct a model, run it, inspect conservation and diagnose a failed check. The project supplies research workflows, fixed MCP connections, deterministic runners and complete tool/solver records. Start with the Wolfram calibration or the native seven-strand Maxwell example.' if lang=='en' else '让智能体建立模型、执行求解、检查守恒并诊断失败。项目提供研究工作流、固定 MCP 接入、确定性运行器及完整工具和求解记录。可从 Wolfram 解析校准或 Maxwell 原生七股案例开始。'}

- [Connect Codex](automation/harnesses/codex/README.md) · [Other MCP clients](automation/harnesses/generic/README.md)
- [Complete automation examples](automation/examples/README.md) · [Architecture and extension](docs/automation-architecture.md)
- [Reproduce](automation/workflows/reproduce/README.md) · [Extend a model](automation/workflows/extend-model/README.md) · [Compare solvers](automation/workflows/compare-solvers/README.md) · [Diagnose](automation/workflows/diagnose/README.md)

## {'What the Litz case establishes' if lang=='en' else 'Litz 案例中的研究认识'}

{'At 200 kHz and 20 A RMS, the 2 mm isolated round-wire calibration gives 20.0162 mΩ/m internal AC resistance and 8.00648 W/m Joule loss. Common terminal voltage does not force equal complex strand currents. Finite-length longitudinal PEEC supports model-specific loss and sensitivity comparisons; field, geometry and end-region models retain their own validation ranges.' if lang=='en' else '在 200 kHz、20 A RMS 下，2 mm 孤立圆线校准的交流内电阻为 20.0162 mΩ/m，焦耳损耗为 8.00648 W/m。共同端电压下仍可能存在复电流差异。有限长度纵向 PEEC 支持其模型范围内的损耗与敏感性比较；外场、几何和端区模型各自保留验收范围。'}

{'Explore the analytical profile, 640-strand currents and PEEC sensitivity in the publications. Each figure connects to its source data, model and acceptance evidence.' if lang=='en' else '从成稿中的解析径向分布、640 股复电流和 PEEC 敏感性图进入研究；每张图关联数据、模型和验收证据。'}

## {'Run a first result' if lang=='en' else '运行第一个结果'}

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[automation]"
.venv/Scripts/litz-research.exe run analytic --case tutorial --run-id analytic_example_01
.venv/Scripts/litz-research.exe automation doctor
```

{'Read outputs/analytic_example_01/results.json. Scientific execution uses SI, exp(+jωt) and RMS. Q1 is a calibration case with 6.3662 A/mm²; final Q2 design requires at least 5 mm² nominal copper.' if lang=='en' else '读取 outputs/analytic_example_01/results.json。计算采用 SI、exp(+jωt) 和 RMS；Q1 的电流密度为 6.3662 A/mm²，用作校准，Q2 最终设计要求至少 5 mm² 名义铜面积。'}

## {'Choose a model and continue the research' if lang=='en' else '选择模型并继续研究'}

| Route | Research entry |
| --- | --- |
| Bessel calibration | [analytic](models/analytic/README.md) |
| 2D field calibration | [fem2](models/fem2/README.md) |
| Common-terminal currents | [common_terminal](models/common_terminal/README.md) |
| Geometry and transposition | [geometry](models/geometry/README.md) |
| Longitudinal PEEC | [peec](models/peec/README.md) |
| RT0 volume model | [rt0](models/rt0/README.md) |
| A–φ diagnostics | [aphi](models/aphi/README.md) |

{'Each route includes bilingual interactive Notebooks, editable tutorial inputs, source and checks. Continue from a small verified case toward mesh, boundary and length studies. Real transposition, finite terminal fields and experiments remain research directions defined by the preserved diagnostics.' if lang=='en' else '每条路线包含双语交互 Notebook、可编辑教程输入、源码和验收。先复现小型案例，再研究网格、边界和长度；真实换位、有限端场和实验沿保存的诊断资料继续推进。'}

## {'Read, cite and reuse' if lang=='en' else '阅读、引用与复用'}

[Publications](publications/README.md) · [Datasets](docs/datasets.md) · [Citation guide](docs/citation-guide.md) · [Acknowledgments](ACKNOWLEDGMENTS.md) · [Licenses](LICENSES/README.md)

Original software uses MIT; original text, figures and data use CC BY 4.0. Upstream software retains its own license. Wolfram and Ansys are external licensed applications. This candidate repository remains private with a draft release while its handoff is reviewed.
'''
        put('README.md' if lang=='en' else 'README.zh-CN.md',text)
    print('Automation, skills, route navigation and style records built')

if __name__=='__main__':main()
