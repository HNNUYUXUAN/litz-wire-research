# Research skills

| Skill | Task | Next workflow |
|---|---|---|
| research-scout | Question, literature and implementation discovery | compare-solvers, extend-model |
| paper-acquire | Open or authorized full text with identity checks | reproduce |
| research-reuse | License, fixed source identity and executable comparison | diagnose, extend-model |
| research-handoff | Saved inputs and independent acceptance | reproduce, report |

Run `python tools/InstallResearchSkills.py --destination PATH` to install the four directories into your host's skill directory. The installer refuses to overwrite an existing skill. Set `LITZ_PROJECT` to the checkout or start the agent there. Each installed skill contains its own workflow reference; project scripts and pinned third-party code remain in the checkout.

The research environment supplies Python and Node; `litz-research` runs from the project environment. Read `automation/research/README.md` for the source-record contract and deterministic module commands. Installation establishes discoverability; the integration ledger records actual provider and case acceptance.
