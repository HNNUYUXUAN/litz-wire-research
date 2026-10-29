# Geometry and transposition

Miao Yuxuan · Huainan Normal University

## Model and assumptions

ℓi=∫√(1+x′²+y′²) dz; Rdc=(ΣσAi/ℓi)⁻¹

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Change topology, pitch or length; inspect gaps, arc lengths and copper volume. Geometry is a model input.

## Save inputs and execute

Run from the project root. Copy and edit the parameter file and choose a new run ID. The CLI validates parameter fields; save source and inputs before formal execution.

[Parameter file](examples/tutorial.json)

```bash
litz-research models geometry
litz-research run geometry --case tutorial --parameters models/geometry/examples/tutorial.json --run-id geometry_example_01 --dry-run
litz-research run geometry --case tutorial --parameters models/geometry/examples/tutorial.json --run-id geometry_example_01
```

Use the installed `litz-research` command, or replace it with `.conda/project/python.exe -m litz_research.cli`.

## Asynchronous jobs and recovery

```bash
litz-research jobs submit geometry --case tutorial --parameters models/geometry/examples/tutorial.json --run-id geometry_example_01
litz-research jobs status geometry_example_01
```

The synchronous and asynchronous examples are two ways to execute the same task. Choose one and assign a unique run ID. Cancel with `litz-research jobs cancel geometry_example_01`. Before resuming, verify input and source identities; use `jobs resume --help` to assign a linked new run ID.

## Results and acceptance

Inspect `execution_status`, `physical_acceptance_status`, `checks`, `scope` and parameters in `outputs/geometry_example_01/results.json`. Complex values retain real and imaginary parts; routes with native results also save `results.wxf`. One tutorial mesh does not establish convergence.

Tasks use at most eight logical processors and 24 GiB memory, retaining 8 GiB system reserve. Only task-created processes with matching creation identities are managed.

## Derivation and interpretation

A topology maps a persistent strand identity to a centerline (xi(z),yi(z),z). The tutorial samples the path, evaluates surface gaps and integrates each arc length ℓi=∫√(1+x′i²+y′i²)dz.
For axially cut length L, copper volume is ΣAiℓi and common-terminal Rdc=(ΣσAi/ℓi)⁻¹. Equal nominal copper area does not remove arc-length growth or change terminal constraints.
Geometry supplies the subsequent field model. Performance ranking requires an independent electromagnetic solve, controlled return/end effects and numerical uncertainty, using traditional multilevel Litz as a strong baseline.

## Continue the research

Change one supported parameter at a time, save a new run identity, and check conservation, discretization, boundary and length sensitivity. Preserve comparable returns, actual arc lengths, copper volume and the traditional multilevel Litz baseline.

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## Historical evidence and sources

data/evidence/v1.0.0-rc.1/; litz-research data fetch geometry

[P01](../../references/README.md), [N01](../../references/README.md)
