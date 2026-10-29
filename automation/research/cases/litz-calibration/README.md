# Literature-to-model handoff: round-wire calibration

The reviewed sources C01 (doi:10.12263/DZXB.20230001) and Zhu et al. (doi:10.1109/TTE.2025.3610369) address Litz winding AC loss. Their winding and homogenization models require separate applicability checks. This task first verifies the project's existing isolated round-wire internal-field reference before considering those extensions.

Inputs are saved in `parameters.json`. Use copper at 20 °C, conductivity 58 MS/m, relative permeability 1, radius 1 mm, SI units, exp(+jωt), and RMS current. The model excludes winding proximity fields, finite ends and return-path external inductance. Q1 is a calibration case; its copper area does not satisfy the final Q2 area requirement.

From the repository root:

```bash
.conda/project/python.exe -m litz_research.cli run analytic --case tutorial --parameters automation/research/cases/litz-calibration/parameters.json --run-id research_handoff_20261028_01
```

Inspect `outputs/research_handoff_20261028_01/request.json`, `parameters.json`, `results.json` and the saved source/environment identities. Require all analytical checks to pass, integrated complex current to agree with 20 A RMS, and integrated Joule loss to agree with |I|² Re(Zint). Expected reference values are 20.016203627649 mΩ/m and 8.006481451060 W/m. Execution completion and these physical checks have distinct meanings.

Resource limits are eight logical processors, 24 GiB task memory and 8 GiB system reserve. Follow-up winding tasks must introduce explicit geometry, common-terminal constraints, local fields, strand identities and convergence checks. Literature agreement alone does not validate these additional models.

Acquisition and metadata evidence: `outputs/research_online_20261028_01/`. Public records retain canonical source URLs; institutional session details and downloaded full text remain local. This task tests a research handoff to an existing model, not a reproduction of either paper's winding results.
