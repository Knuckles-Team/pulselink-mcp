# Usage — API / CLI / MCP

`pulselink-mcp` exposes the same capability three ways: as **MCP tools** an agent
calls, as a **Python API** you import, and as a **CLI**.

## As an MCP server

Once [deployed](deployment.md), the server registers consolidated, action-routed
tool modules. Each module is independently togglable with a `*TOOL` environment
flag.

## As a Python API

```python
from pulselink_mcp.auth import get_client

api = get_client()        # reads PULSELINK_MCP_URL / PULSELINK_MCP_TOKEN from the environment / .env
status = api.get_system_status()
```

## As a CLI

```bash
export PULSELINK_MCP_URL="http://localhost:8080"
export PULSELINK_MCP_TOKEN="your_token"
pulselink-mcp --transport stdio
```
