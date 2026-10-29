# Compare matching field models

Align geometry, copper area, material, frequency, RMS/peak convention, axial length, terminal constraints, return and boundaries. Solve independently. Compare complex currents, power and Rac with discretization and geometry differences visible.

Inputs: research question, selected model/case, physical conditions, source/evidence identities and resource budget.

Outputs: request.json, parameters.json, run_manifest.json, logs, results.json, test evidence, code diff when relevant, and a concise scientific explanation.

Use `litz-research models`, `litz-research run <model> --case tutorial --dry-run`, and `litz-research jobs submit/status/cancel/resume`. Read the route guide before a full campaign.

Completion: reproducible inputs and source, actual execution evidence, correct scope and an explicit acceptance state. Refer to tests/ACCEPTANCE.md and references/README.md.
