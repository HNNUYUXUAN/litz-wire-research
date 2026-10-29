# Codex reference harness

1. Clone this checkout and install `python -m pip install -e ".[automation]"` in a virtual environment.
2. Install licensed Wolfram/AEDT separately. Follow the fixed MCP setup guides.
3. Generate inspectable configuration with `litz-research automation configure --output build/codex-config --ansys-python <Python in the Ansys MCP environment>`.
4. Inspect and merge the generated TOML into the selected project `.codex/config.toml`; keep local executable paths out of Git. Refresh the client, list active tools and run both protocol probes.
5. Install the desired folders under automation/skills into the client's skill directory or read their SKILL.md explicitly. The root AGENTS.md supplies the shared research conventions.
6. Submit a concrete task from automation/examples. Observe actual tools, inspect the code and result artifacts, and read physical acceptance separately.

For long execution: `litz-research jobs submit peec --case tutorial --run-id peec_job_01`, then `jobs status peec_job_01`. `jobs cancel` requests cancellation; `jobs resume --new-run-id` restarts from saved input under a linked identity.

Reference verification uses Codex orchestrating the standard MCP client in automation/mcp/client.py and the official Wolfram tools. Native client registration is checked separately from this bridge. Model and client versions are recorded only when observable.

Run `litz-research automation readiness --run-id <new-id> --client-config <active-config.toml>` to compare desktop and project settings. After changes, run both `automation probe` commands with `--clean-environment`; see [Reproduction readiness](../../../docs/reproduction-readiness.md).

[Official MCP configuration documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli). The project generator locates the installed kernel through wolframscript when it is absent from PATH and records unresolved executable paths explicitly.
