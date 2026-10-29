# Reproduce a recorded model

Select a model, explicit case and evidence dataset. Verify source identity and physical assumptions. Run doctor and dry-run, execute into a new run, inspect checks and compare only matching observables.

Inputs: research question, selected model/case, physical conditions, source/evidence identities and resource budget.

Outputs: request.json, parameters.json, run_manifest.json, logs, results.json, test evidence, code diff when relevant, and a concise scientific explanation.

Use `litz-research models`, `litz-research run <model> --case tutorial --dry-run`, and `litz-research jobs submit/status/cancel/resume`. Read the route guide before a full campaign.

Completion: reproducible inputs and source, actual execution evidence, correct scope and an explicit acceptance state. Refer to tests/ACCEPTANCE.md and references/README.md.
