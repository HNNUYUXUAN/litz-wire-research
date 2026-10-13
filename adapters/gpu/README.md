# GPU execution and CPU comparison

Miao Yuxuan · Huainan Normal University

## Model and assumptions

Same-input double-precision numerical comparison

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Run a small GPU/CPU comparison; retain toolchain and numerical error.

## Run the tutorial

```powershell
litz-research run gpu --case tutorial --parameters adapters/gpu/examples/tutorial.json --run-id gpu_example_01
```

[Interactive Notebook](notebooks/gpu_en.nb)

## Result and acceptance

Read `results.json`, the checks, complex real/imaginary values and `results.wxf`. Execution status and physical acceptance describe different observations. A single tutorial mesh does not establish convergence.

## Research continuation

Start from the tutorial configuration. Vary one supported parameter at a time, save new run identities, check conservation and discretization sensitivity, then compare frozen evidence. Complete campaigns remain available through the stage runner.

## Sources

[CUDA](../../references/README.md)

## Derivation and interpretation

Execute the same small double-precision operations on CPU and GPU: matrix multiplication, a complex linear system with known solution and true residual, FFT and inverse roundtrip.
The comparison verifies arithmetic and runtime equivalence for the stated inputs. It does not establish a new physical solution, large-scale convergence or a performance advantage for a different workload.

## Historical evidence

data/evidence/v1.0.0-rc.1/; litz-research data fetch gpu
