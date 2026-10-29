# Conda runtimes

Create separate prefixes under the ignored `.conda/` directory using Miniconda and conda-forge. Run MCP with the environment's absolute Python path. Wolfram, AEDT, Git Bash and MiKTeX remain external installations.

```bash
conda create -p .conda/project --override-channels -c conda-forge python=3.12 pip pandoc=3.13
.conda/project/python.exe -m pip install -e '.[automation,documents,figures,audit]' -c automation/mcp/project-environment.lock
conda create -p .conda/ansys --override-channels -c conda-forge python=3.12 pip
conda create -p .conda/research --override-channels -c conda-forge python=3.12 nodejs=24 pip
```

The ANSYS runtime consumes `automation/mcp/ansys-environment.lock` and the official commit in `upstreams.lock.json`. Validate imports, `pip check`, upstream identity, clean-environment probes and actual small cases before switching local configuration. Export explicit Conda package locks and pip inventories for every accepted environment. Python 3.13 upstream contribution environments are separate from the accepted application runtime.

Keep the existing runtime until replacement validation completes. Retire it only after checking configuration and process references. Record actual host OS/build separately from the Windows 10/11 target matrix.

The locks directory contains exported win-64 Conda package identities and pip inventories from the created environments. Restore Conda packages with `conda create -p PREFIX --file locks/NAME-win-64.explicit.txt`, then install `locks/NAME-pip.txt`. Install this project editable and the ANSYS MCP commit separately using the upstream manifest. All three clean-prefix rebuilds passed. The project and Codex configurations were backed up and switched, and the MCP services restarted. Native-client evidence confirms the new Conda paths, twelve Wolfram analytical checks and a controlled AEDT Student connection with owned-process cleanup. Both project-specific old prefixes were retired after configuration and process audits; 33,802 files were retained in local frozen archives and verified by SHA256. The public receipt is `provenance/research-integration/environment-retirement.json`.

The deterministic entry point reads the official repository and commit from the upstream manifest and installs directly from that origin. It refuses to overwrite an existing prefix:

```bash
python tools/CondaEnvironments.py rebuild project --prefix .conda/rebuilt-project
python tools/CondaEnvironments.py rebuild ansys --prefix .conda/rebuilt-ansys
python tools/CondaEnvironments.py rebuild research --prefix .conda/rebuilt-research
python tools/CondaEnvironments.py export project
```

Pass `--conda` with the Miniconda executable when it is outside PATH. Conda explicit packages are restored first, followed by the pip layer and project/upstream installation. Export again after any package adjustment. Candidate JSON (`mcpServers`) and TOML (`mcp_servers`) configurations can be tested with `litz-research automation probe SERVER --run-id UNIQUE --client-config PATH --clean-environment` before changing the live configuration.

For asynchronous solver cases, set `LITZ_MCP_CLIENT_CONFIG` to the absolute candidate path before `jobs submit`. The owned AEDT session and nested MCP probe both consume that candidate; the resulting manifest stores its hash. Check the actual result's Python and solver versions before recording a migration acceptance.
