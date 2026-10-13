# Wolfram MCP setup

Install Wolfram/AgentTools 2.2.0 from the pinned source or paclet. Set LITZ_WOLFRAM_KERNEL to the licensed Wolfram executable. The server entry is PacletSymbol["Wolfram/AgentTools","Wolfram`AgentTools`StartMCPServer"]["WolframLanguage"].

Use the [fixed upstream manifest](../upstreams.lock.json), retain the upstream license, and lock the environment with `python -m pip freeze` after verification. Configure through the generated project templates. STDIO is the default; Ansys also supports HTTP bound to 127.0.0.1.

Run `litz-research automation probe wolfram --run-id wolfram_mcp_probe_01`. Inspect initialize, tools/list and tools/call events. Tool errors may be text; check actual solver files and numerical acceptance. Long simulations use bounded jobs and status queries.

Uninstall this integration by removing its generated client entries and project virtual environment. Existing scientific applications and other MCP configurations are independent installations.

## Fixed installation and probes

In a licensed Wolfram kernel, inspect `PacletFind["Wolfram/AgentTools"]`. If installation is needed, use `PacletInstall["Wolfram/AgentTools" -> "2.2.0", KeepExistingVersion -> True]`; inspect the returned version. The official [PacletInstall documentation](https://reference.wolfram.com/language/ref/PacletInstall.html) defines the explicit version form. Source identity and the retained MIT notice are in upstreams.lock.json and LICENSES/third-party.

The WolframLanguage server exposes seven tools in this baseline. The default unnamed server exposes a different tool set. Use the generated configuration and the five-tool calibration sequence. The 20-Notebook verifier tests actual local frontend save/read/render independently of protocol initialization.
