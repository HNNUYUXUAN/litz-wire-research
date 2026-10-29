# Litz research workflow

Read README, the selected route README, docs/建模约定与解析基准.md and tests/ACCEPTANCE.md. Use automation/workflows for reproduction, model extension, comparisons, diagnosis or scholarly output.

SI calculations; exp(+jωt); RMS phasors; copper σ=58 MS/m, μr=1, 20 °C. Main transport case: 200 kHz, 20 A RMS. Q1 diameter 2 mm is a calibration case with Jdc≈6.366 A/mm²; final Q2 nominal copper area is at least 5 mm².

Solve common-terminal voltage and total complex current. Preserve strand identity, actual arc length, return/boundary assumptions, complex currents, absolute Rac, Rac/Rdc and power. Traditional multilevel Litz is the strong baseline. Ranking requires improvement exceeding numerical uncertainty.

Use the shared CLI/Notebook task interface. Write source and inputs before formal execution. Choose explicit tutorial/campaign cases and unique run IDs. Record source hashes, versions, parameters, assumptions, execution status, physical acceptance and failures. Never treat tool success as physical validation.

Budget: eight logical processors, 24 GiB task memory, 8 GiB free system reserve; Student license limits additionally apply. Manage only processes created by the task and bind process ownership to creation identity. Preserve original evidence and independent user modifications.

Use official Wolfram and PyAEDT MCP versions from automation/mcp/upstreams.lock.json. Inspect available tools and actual responses. Use asynchronous jobs for long tasks. Resume only from verified inputs/checkpoints; otherwise create a linked new run. State missing runtime capabilities accurately.

Reference keys come from references/library.bib. Record actual use and license in references/sources.json. Third-party snapshots retain copyright. Public examples use portable paths and sanitized visible tool records.
