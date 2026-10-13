# Diagnose and recover a failed run

Preserve the original failure and actual tool response. Separate transport, API, solver, resource and physical failures. Test the smallest relevant correction, record its rationale and code diff, rerun with a new identity, compare acceptance without weakening tolerances.

Inputs: research question, selected model/case, physical conditions, source/evidence identities and resource budget.

Outputs: request.json, parameters.json, run_manifest.json, logs, results.json, test evidence, code diff when relevant, and a concise scientific explanation.

Use `litz-research models`, `litz-research run <model> --case tutorial --dry-run`, and `litz-research jobs submit/status/cancel/resume`. Read the route guide before a full campaign.

Completion: reproducible inputs and source, actual execution evidence, correct scope and an explicit acceptance state. Refer to tests/ACCEPTANCE.md and references/README.md.
