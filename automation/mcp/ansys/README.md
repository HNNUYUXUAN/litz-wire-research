# Ansys MCP setup

Create a Python 3.12+ environment, install PyAEDT 1.8.0 and the fixed ansys/pyaedt-mcp commit from upstreams.lock.json. Use adapters/ansys/StartMCP.py with LITZ_AEDT_EDITION=student for the explicit Student connector. Start OwnedAEDTSession.py, read its port receipt, and call connect_to_aedt using the matching version. CPython/PyAEDT code uses run_python_code; AEDT RunScript has a different runtime.

Use the [fixed upstream manifest](../upstreams.lock.json), retain the upstream license, and lock the environment with `python -m pip freeze` after verification. Configure through the generated project templates. STDIO is the default; Ansys also supports HTTP bound to 127.0.0.1.

Run `litz-research automation probe ansys --run-id ansys_mcp_probe_01`. Inspect initialize, tools/list and tools/call events. Tool errors may be text; check actual solver files and numerical acceptance. Long simulations use bounded jobs and status queries.

Uninstall this integration by removing its generated client entries and project virtual environment. Existing scientific applications and other MCP configurations are independent installations.

## Pinned environment

```powershell
python automation/mcp/setup.py ansys --destination build/ansys-env
python automation/mcp/setup.py ansys --destination build/ansys-env --apply
litz-research automation configure --output build/client-config --ansys-python build/ansys-env/Scripts/python.exe
```

The first command prints the plan; the second applies it in a new directory. The verified full dependency freeze is ansys-environment.lock. Use the [native replay instructions](../../examples/README.md) and the [official installation guide](https://aedt-mcp.docs.pyansys.com/version/stable/getting_started/installation.html). For optional local HTTP, launch StartMCP.py with `--transport http --http-host 127.0.0.1 --http-port 8080`, then generate the HTTP template. HTTP is configuration-only in the verification matrix.
