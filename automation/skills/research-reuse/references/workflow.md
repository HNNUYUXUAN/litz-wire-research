# Project workflow

Locate the Litz checkout from LITZ_PROJECT or the current working directory. Read automation/research/README.md and automation/research/upstreams.lock.json there. Run deterministic helpers from the checkout with the isolated research Python/Node runtime; use the project environment for litz-research.

The canonical citation and adopted-source records are references/library.bib and references/sources.json. Acquisition records and full text live in .local-library. Validate local records with python -m litz_research.research_records RECORDS --root EVIDENCE_ROOT. Keep provider field sources, timestamps, failures, conflicts and reuse rights explicit.

Before handing a task to execution, read its route README, docs/建模约定与解析基准.md and tests/ACCEPTANCE.md. Use automation/workflows/reproduce, extend-model, compare-solvers, diagnose or report as appropriate. Current delivery status and evidence are in automation/integration-plan.json.
