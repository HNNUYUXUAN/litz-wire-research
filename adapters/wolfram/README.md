# Wolfram environment and execution

Miao Yuxuan · Huainan Normal University

## Model and assumptions

Independent kernel execution and native frontend rendering

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Probe the local kernel, then follow the MCP workflow for actual tool and Notebook operations.

## Save inputs and execute

Run from the project root. Copy and edit the parameter file and choose a new run ID. The CLI validates parameter fields; save source and inputs before formal execution.

[Parameter file](examples/tutorial.json)

```bash
litz-research models wolfram
litz-research run wolfram --case tutorial --parameters adapters/wolfram/examples/tutorial.json --run-id wolfram_example_01 --dry-run
litz-research run wolfram --case tutorial --parameters adapters/wolfram/examples/tutorial.json --run-id wolfram_example_01
```

Use the installed `litz-research` command, or replace it with `.conda/project/python.exe -m litz_research.cli`.

## Asynchronous jobs and recovery

```bash
litz-research jobs submit wolfram --case tutorial --parameters adapters/wolfram/examples/tutorial.json --run-id wolfram_example_01
litz-research jobs status wolfram_example_01
```

The synchronous and asynchronous examples are two ways to execute the same task. Choose one and assign a unique run ID. Cancel with `litz-research jobs cancel wolfram_example_01`. Before resuming, verify input and source identities; use `jobs resume --help` to assign a linked new run ID.

## Results and acceptance

Inspect `execution_status`, `physical_acceptance_status`, `checks`, `scope` and parameters in `outputs/wolfram_example_01/results.json`. Complex values retain real and imaginary parts; routes with native results also save `results.wxf`. One tutorial mesh does not establish convergence.

Tasks use at most eight logical processors and 24 GiB memory, retaining 8 GiB system reserve. Only task-created processes with matching creation identities are managed.

## Derivation and interpretation

Probe the actual local kernel and arithmetic first. The native Notebook runs the same saved task interface as the CLI in an independent process. The MCP example separately checks tool discovery, numerical evaluation, TestReport, Notebook writing and reading.
A working connection is distinct from a successful numerical test or field acceptance. Record the installed AgentTools version and visible tool schemas before using version-specific arguments.

## Continue the research

Change one supported parameter at a time, save a new run identity, and check conservation, discretization, boundary and length sensitivity. Preserve comparable returns, actual arc lengths, copper volume and the traditional multilevel Litz baseline.

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## Historical evidence and sources

data/evidence/v1.0.0-rc.1/; litz-research data fetch analytic

[WOLFRAM](../../references/README.md), [AGENTTOOLS](../../references/README.md)
