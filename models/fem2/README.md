# Two-dimensional diffusion FEM

Miao Yuxuan · Huainan Normal University

## Model and assumptions

∇⊥²Ez−jωμσEz=0; Jz=σEz

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Change mesh_h; run at least three meshes before making a convergence claim.

## Save inputs and execute

Run from the project root. Copy and edit the parameter file and choose a new run ID. The CLI validates parameter fields; save source and inputs before formal execution.

[Parameter file](examples/tutorial.json)

```bash
litz-research models fem2
litz-research run fem2 --case tutorial --parameters models/fem2/examples/tutorial.json --run-id fem2_example_01 --dry-run
litz-research run fem2 --case tutorial --parameters models/fem2/examples/tutorial.json --run-id fem2_example_01
```

Use the installed `litz-research` command, or replace it with `.conda/project/python.exe -m litz_research.cli`.

## Asynchronous jobs and recovery

```bash
litz-research jobs submit fem2 --case tutorial --parameters models/fem2/examples/tutorial.json --run-id fem2_example_01
litz-research jobs status fem2_example_01
```

The synchronous and asynchronous examples are two ways to execute the same task. Choose one and assign a unique run ID. Cancel with `litz-research jobs cancel fem2_example_01`. Before resuming, verify input and source identities; use `jobs resume --help` to assign a linked new run ID.

## Results and acceptance

Inspect `execution_status`, `physical_acceptance_status`, `checks`, `scope` and parameters in `outputs/fem2_example_01/results.json`. Complex values retain real and imaginary parts; routes with native results also save `results.wxf`. One tutorial mesh does not establish convergence.

Tasks use at most eight logical processors and 24 GiB memory, retaining 8 GiB system reserve. Only task-created processes with matching creation identities are managed.

## Derivation and interpretation

The circular cross section solves ∇⊥²Ez−jωμσEz=0. A constant boundary field is normalized to the total complex current; the circle polygon, interpolation order and mesh size determine numerical error.
The weak form integrates ∇v·∇Ez+jωμσvEz over the domain, subject to the stated boundary value. Integrate the resulting current and Joule density independently and compare Rac with the Bessel solution.
This tutorial uses one mesh. Repeat at three or more decreasing h/a values and inspect boundary/polygon resolution before claiming accuracy; integral conservation alone does not bound field error.

## Continue the research

Change one supported parameter at a time, save a new run identity, and check conservation, discretization, boundary and length sensitivity. Preserve comparable returns, actual arc lengths, copper volume and the traditional multilevel Litz baseline.

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## Historical evidence and sources

data/evidence/v1.0.0-rc.1/; litz-research data fetch fem2

[FEMDOC](../../references/README.md), [P04](../../references/README.md)
