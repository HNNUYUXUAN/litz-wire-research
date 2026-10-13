# Wolfram environment and execution

Miao Yuxuan · Huainan Normal University

## Model and assumptions

Independent kernel execution and native frontend rendering

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Probe the local kernel, then follow the MCP workflow for actual tool and Notebook operations.

## Run the tutorial

```powershell
litz-research run wolfram --case tutorial --parameters adapters/wolfram/examples/tutorial.json --run-id wolfram_example_01
```

[Interactive Notebook](notebooks/wolfram_en.nb)

## Result and acceptance

Read `results.json`, the checks, complex real/imaginary values and `results.wxf`. Execution status and physical acceptance describe different observations. A single tutorial mesh does not establish convergence.

## Research continuation

Start from the tutorial configuration. Vary one supported parameter at a time, save new run identities, check conservation and discretization sensitivity, then compare frozen evidence. Complete campaigns remain available through the stage runner.

## Sources

[WOLFRAM](../../references/README.md), [AGENTTOOLS](../../references/README.md)

## Derivation and interpretation

Probe the actual local kernel and arithmetic first. The native Notebook runs the same saved task interface as the CLI in an independent process. The MCP example separately checks tool discovery, numerical evaluation, TestReport, Notebook writing and reading.
A working connection is distinct from a successful numerical test or field acceptance. Record the installed AgentTools version and visible tool schemas before using version-specific arguments.

## Historical evidence

data/evidence/v1.0.0-rc.1/; litz-research data fetch analytic
