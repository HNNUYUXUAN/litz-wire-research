# Other agent clients

The portable contract consists of MCP STDIO/HTTP configuration, the research workflows, saved parameter files and the local CLI. A client must support MCP initialization, tool discovery and tool calls, and provide access to the checkout. Read AGENTS.md and the relevant SKILL.md explicitly when automatic instruction discovery differs.

Generate `mcp.json` with `litz-research automation configure`. Map its server command/args/cwd or HTTP URL to your client's configuration. Check paths and available tools; run automation/mcp/client.py as the independent protocol probe.

The workflow does not depend on Codex thread IDs or private conversation history. Results and source hashes, rather than a particular prompt response, determine scientific reproducibility. Other harnesses remain unverified until their own end-to-end records are supplied.
