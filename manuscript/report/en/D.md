<!-- id: D.workflow.p1 -->
Research entry points read model inputs and solver settings and produce run records and corresponding checks. Document entry points read saved quantities, figures, and Markdown prose to generate complete manuscripts. Input, source, and output hashes identify each build. Individual figures retain vector curves and font information, while composites record panel identities and layout parameters. The following source table links observables in the text to specific files and acceptance records.

<!-- id: D.sources -->
{{sources}}

<!-- id: D.automation.heading -->
## Agent workflows and software connections

<!-- id: D.automation.p1 -->
Codex invokes pinned AgentTools and PyAEDT-MCP through a standard MCP client bridge. Workflows define tasks and acceptance, adapters manage software connections, and model source defines deterministic computation. Formal tasks bind parameters, source hashes, and run identifiers. Status queries follow long tasks, and cancellation targets the owned process tree. Recovery uses verified inputs and checkpoints; tutorial restarts establish a linked new run identity.

<!-- id: D.automation.p2 -->
Wolfram records cover analytical integrals, testing, graphics, and Notebook save/readback. Ansys records cover initialization, discovery, actual calls, AEDT execution, and structured results. Repair of a unit-conversion API retains failed and successful calls with unchanged physical parameters. A–φ readback retains completed execution together with failed potential and gauge acceptance. Separate protocol, program, and scientific states let subsequent research target the actual failure layer.
