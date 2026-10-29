---
name: research-handoff
description: Turn verified research findings and reusable implementations into an executable modeling or engineering task with explicit acceptance evidence.
---

Read the accepted research brief, source records and reuse comparison. Produce a task specifying question, chosen model or component, input files, assumptions, dependencies, resource budget, expected observations and independent acceptance checks. Identify uncertain claims and the experiment that can resolve each one.

Use [the workflow reference](references/workflow.md) to locate the project and deterministic interfaces.

For this repository use the existing litz-research models/run/jobs interfaces and automation/workflows. Read the chosen route guide and tests/ACCEPTANCE.md. Save source and inputs before execution. Preserve unique run IDs and source/environment hashes; link revised runs to their predecessors.

Keep connection, tool execution, solver execution and scientific acceptance distinct. Preserve complex quantities and model-specific assumptions. Long jobs use submit/status/cancel/resume; manage only task-owned processes by creation identity. Respect eight logical processors, 24 GiB task memory and 8 GiB free reserve.

Deliver a self-contained Markdown task and machine-readable inputs with source locators. Route completed evidence to the reporting workflow. Label capability scope by observed cases and platforms; broader generalization requires independent cases and a clean-environment replay.
