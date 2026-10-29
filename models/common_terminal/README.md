# Common-terminal current sharing

Miao Yuxuan · Huainan Normal University

## Model and assumptions

Zi+e=V1; 1ᵀi=It

SI; exp(+j omega t); RMS; sigma=58 MS/m; mu_r=1; 20 C

Change strand count or return geometry; inspect complex strand currents and input/loss balance.

## Save inputs and execute

Run from the project root. Copy and edit the parameter file and choose a new run ID. The CLI validates parameter fields; save source and inputs before formal execution.

[Parameter file](examples/tutorial.json)

```bash
litz-research models coax
litz-research run coax --case tutorial --parameters models/common_terminal/examples/tutorial.json --run-id common_terminal_example_01 --dry-run
litz-research run coax --case tutorial --parameters models/common_terminal/examples/tutorial.json --run-id common_terminal_example_01
```

Use the installed `litz-research` command, or replace it with `.conda/project/python.exe -m litz_research.cli`.

## Asynchronous jobs and recovery

```bash
litz-research jobs submit coax --case tutorial --parameters models/common_terminal/examples/tutorial.json --run-id common_terminal_example_01
litz-research jobs status common_terminal_example_01
```

The synchronous and asynchronous examples are two ways to execute the same task. Choose one and assign a unique run ID. Cancel with `litz-research jobs cancel common_terminal_example_01`. Before resuming, verify input and source identities; use `jobs resume --help` to assign a linked new run ID.

## Results and acceptance

Inspect `execution_status`, `physical_acceptance_status`, `checks`, `scope` and parameters in `outputs/common_terminal_example_01/results.json`. Complex values retain real and imaginary parts; routes with native results also save `results.wxf`. One tutorial mesh does not establish convergence.

Tasks use at most eight logical processors and 24 GiB memory, retaining 8 GiB system reserve. Only task-created processes with matching creation identities are managed.

## Derivation and interpretation

Insulated strands are connected in parallel only at the ends. The 2D Az weak form couples each conductive region to its unknown axial electric potential gradient. A controlled conducting coaxial return closes the transport problem.
Linearity yields a coupled block system for Az and the source/return voltage gradients. Impose ΣIi=20 A RMS and Ireturn=−20 A; every strand shares the source voltage gradient, while each complex Ii follows from integrating its solved current density.
Compute bundle and return Joule losses separately and compare their sum with input real power. Rac,bundle=Pbundle/|It|² is valid for this pure transport case. Seven strands demonstrate the method and do not meet Q2 copper area.

## Continue the research

Change one supported parameter at a time, save a new run identity, and check conservation, discretization, boundary and length sensitivity. Preserve comparable returns, actual arc lengths, copper volume and the traditional multilevel Litz baseline.

[Research workflows / 研究工作流](../../automation/workflows/reproduce/README.md)

## Historical evidence and sources

data/evidence/v1.0.0-rc.1/; litz-research data fetch common-terminal

[P01](../../references/README.md), [P02](../../references/README.md)
