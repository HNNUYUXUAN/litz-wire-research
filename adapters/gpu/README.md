# GPU execution and CPU comparison

Miao Yuxuan · Huainan Normal University

## Model and assumptions

Same-input double-precision numerical comparison

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Run a small GPU/CPU comparison; retain toolchain and numerical error.

## Save inputs and execute

Run from the project root. Copy and edit the parameter file and choose a new run ID. The CLI validates parameter fields; save source and inputs before formal execution.

[Parameter file](examples/tutorial.json)

```bash
litz-research models gpu
litz-research run gpu --case tutorial --parameters adapters/gpu/examples/tutorial.json --run-id gpu_example_01 --dry-run
litz-research run gpu --case tutorial --parameters adapters/gpu/examples/tutorial.json --run-id gpu_example_01
```

Use the installed `litz-research` command, or replace it with `.conda/project/python.exe -m litz_research.cli`.

## Asynchronous jobs and recovery

```bash
litz-research jobs submit gpu --case tutorial --parameters adapters/gpu/examples/tutorial.json --run-id gpu_example_01
litz-research jobs status gpu_example_01
```

The synchronous and asynchronous examples are two ways to execute the same task. Choose one and assign a unique run ID. Cancel with `litz-research jobs cancel gpu_example_01`. Before resuming, verify input and source identities; use `jobs resume --help` to assign a linked new run ID.

## Results and acceptance

Inspect `execution_status`, `physical_acceptance_status`, `checks`, `scope` and parameters in `outputs/gpu_example_01/results.json`. Complex values retain real and imaginary parts; routes with native results also save `results.wxf`. One tutorial mesh does not establish convergence.

Tasks use at most eight logical processors and 24 GiB memory, retaining 8 GiB system reserve. Only task-created processes with matching creation identities are managed.

## Derivation and interpretation

Execute the same small double-precision operations on CPU and GPU: matrix multiplication, a complex linear system with known solution and true residual, FFT and inverse roundtrip.
The comparison verifies arithmetic and runtime equivalence for the stated inputs. It does not establish a new physical solution, large-scale convergence or a performance advantage for a different workload.

## Continue the research

Change one supported parameter at a time, save a new run identity, and check conservation, discretization, boundary and length sensitivity. Preserve comparable returns, actual arc lengths, copper volume and the traditional multilevel Litz baseline.

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## Historical evidence and sources

data/evidence/v1.0.0-rc.1/; litz-research data fetch gpu

[CUDA](../../references/README.md)
