# CONN-PULSELINK-MCP-CONNECTOR-CONTENT — Design and implementation plan

Governing spec: [spec.md](spec.md).

## Architecture

`pyproject.toml` declares `pulselink-mcp` as the connector identity. `create_mcp_server` resolves the packaged content of `pulselink_mcp` from it.
