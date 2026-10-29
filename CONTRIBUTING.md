# Contributing

[简体中文](CONTRIBUTING.zh-CN.md)

Contributions can improve a physical model, an execution adapter, a research workflow, a dataset reader or the bilingual publications. Start with [Development](docs/development.md), the selected route's README and the [acceptance targets](tests/ACCEPTANCE.md). [AGENTS.md](AGENTS.md) provides the same research conventions for agent-assisted work.

## Choose a focused change

Use [Issues](https://github.com/HNNUYUXUAN/litz-wire-research/issues) to describe a reproducible problem or a proposed research extension. Include the source revision, command, input parameters, software versions and relevant run ID. Explain the observed and expected behavior. Remove credentials, license details and personal machine paths from shared logs while preserving numerical values and error messages.

Implement the change on a branch. Keep model logic in `models/`, software integration in `adapters/`, and task instructions in `automation/`. Preserve useful compatibility entry points in `src/`. Update the relevant generator when changing generated documentation or indexes.

## Check the source checkout

Use Python 3.11 or 3.12 in an isolated environment. After installing the project, run the portable source checks from the checkout root:

```text
python -m pip install -e ".[automation]"
python -B tools/CheckSourceCheckout.py --output outputs/ci/source-checkout.json
```

The checker covers data identity and restoration fixtures, parameter and process contracts, CLI discovery, references and the six-document publication index. It uses temporary fixtures and does not require downloaded fields, Wolfram, Ansys, document fonts or GPU hardware. Its explicit test selection and JSON receipt identify the checks that ran. The [development guide](docs/development.md) separates this verification from native solver and publication validation.

## Preserve the scientific contract

Calculate in SI units with `exp(+jωt)` and RMS phasors. The reference copper case uses σ = 58 MS/m, μr = 1, 20 °C, 200 kHz and 20 A RMS. The 2 mm Q1 wire is a calibration case; the Q2 bundle requires at least 5 mm² nominal copper area.

Insulated strands share terminal voltage and the total complex-current constraint. Retain actual strand lengths, copper volume, complex strand currents, absolute AC resistance, the AC/DC ratio and loss. State return paths, terminal models, external fields and boundary assumptions. With an independent applied field, distinguish total loss divided by current squared from intrinsic transport resistance. Compare candidate geometries against traditional multilevel Litz using matched conditions and numerical uncertainty.

A physics change needs checks appropriate to its assumptions: analytical limits, independent integrations, power conservation, and mesh, segment, boundary or length sensitivity as applicable. Record failed checks as well as successful ones. Use unique run IDs, save source and input hashes, and keep existing evidence unchanged. [Model workflows](docs/tool-workflows.md) identify the execution routes and their validation scope.

## Maintain bilingual content and attribution

Update English and Chinese reader documentation together. Keep code identifiers, commands, units, equation identities and citation keys consistent. Maintain bibliographic entries in `references/library.bib` and actual contribution, version and license records in `references/sources.json`. After source changes to those registries, regenerate and verify their exports:

```text
litz-research references build
litz-research references verify
```

Preserve upstream copyright and license notices when adapting code. Original software and Notebook code use MIT; original prose, figures and data use CC BY 4.0. Third-party material keeps its own terms, as described in [Licenses](LICENSES/README.md).

## Submit a reviewable pull request

Describe the problem, the resulting behavior and the validation performed. For scientific changes, include the physical assumptions, comparison conditions, evidence locations and applicable uncertainty. For workflow changes, identify the tool or runner behavior exercised. Mark unavailable native runtimes and unfinished scientific checks accurately. Link new artifacts through a manifest with file hashes; keep credentials, caches and local application installations out of the contribution.

Publication and repository release steps are described in [Release preparation](docs/release-preparation.md).
