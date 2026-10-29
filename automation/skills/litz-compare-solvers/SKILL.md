---
name: litz-compare-solvers
description: Compare matching field models in the Litz research checkout using its scientific conventions, shared run interface and traceable evidence.
---

Align geometry, copper area, material, frequency, RMS/peak convention, axial length, terminal constraints, return and boundaries. Solve independently. Compare complex currents, power and Rac with discretization and geometry differences visible.

Find the checkout from pyproject.toml and configs/reference_parameters.json. Read AGENTS.md, the selected route guide and automation/workflows/compare-solvers/README.md. Use explicit model/case and supported parameters. The complete procedure and output contract live in that workflow guide.

Inspect the available MCP tools. Wolfram operations use the fixed AgentTools server; Maxwell operations use the fixed PyAEDT-MCP server and the project Student connector when applicable. Save formal source and inputs, then execute through the bounded runner. Read actual return values and result files, including semantic API errors returned as text.

Long tasks use unique run IDs and status queries. Preserve failures and link revised runs. Report execution and physical acceptance independently, with the model assumptions and scientific limits.
