# PulseLink MCP
## CLI or API | MCP | Agent

![PyPI - Version](https://img.shields.io/pypi/v/pulselink-mcp)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
![PyPI - Downloads](https://img.shields.io/pypi/dd/pulselink-mcp)
![GitHub Repo stars](https://img.shields.io/github/stars/Knuckles-Team/pulselink-mcp)
![PyPI - License](https://img.shields.io/pypi/l/pulselink-mcp)
![GitHub last commit (by committer)](https://img.shields.io/github/last-commit/Knuckles-Team/pulselink-mcp)

*Version: 0.3.0*

> **Documentation** — Installation, deployment, usage across the API, CLI, and MCP
> interfaces, the integrated A2A agent server, and guidance for provisioning the
> backing platform are maintained in the
> [official documentation](https://knuckles-team.github.io/pulselink-mcp/).

---

## Overview

**PulseLink MCP MCP Server + A2A Agent**

PulseLink — keyless open-web & social research source (MCP Server + A2A Server)

This repository is actively maintained - Contributions are welcome!

## MCP

### Using as an MCP Server

The MCP Server can be run in `stdio` (local), `streamable-http` (networked), or
`sse` mode.

#### Environment Variables

*   `PULSELINK_MCP_URL`: The URL of the target service.
*   `PULSELINK_MCP_TOKEN`: The API token or access token.

#### stdio Transport (local IDEs — Cursor, Claude Desktop, VS Code)

```json
{
  "mcpServers": {
    "pulselink-mcp": {
      "command": "uvx",
      "args": ["--from", "pulselink-mcp", "pulselink-mcp"],
      "env": {
        "PULSELINK_MCP_URL": "https://service.example.com",
        "PULSELINK_MCP_TOKEN": "your_token"
      }
    }
  }
}
```

#### Streamable-HTTP Transport (networked / production)

```json
{
  "mcpServers": {
    "pulselink-mcp": {
      "command": "uvx",
      "args": ["--from", "pulselink-mcp", "pulselink-mcp", "--transport", "streamable-http", "--port", "8000"],
      "env": {
        "TRANSPORT": "streamable-http",
        "HOST": "0.0.0.0",
        "PORT": "8000",
        "PULSELINK_MCP_URL": "https://service.example.com",
        "PULSELINK_MCP_TOKEN": "your_token"
      }
    }
  }
}
```

<!-- BEGIN GENERATED: additional-deployment-options -->
### Additional Deployment Options

`pulselink-mcp` can also run as a **local container** (Docker / Podman / `uv`) or be
consumed from a **remote deployment**. The
[Deployment guide](https://knuckles-team.github.io/pulselink-mcp/deployment/) has full,
copy-paste `mcp_config.json` for all four transports — **stdio**, **streamable-http**,
**local container / uv**, and **remote URL**:

- **Local container / uv** — launch the server from `mcp_config.json` via `uvx`,
  `docker run`, or `podman run`, or point at a local streamable-http container by `url`.
- **Remote URL** — connect to a server deployed behind Caddy at
  `http://pulselink-mcp.arpa/mcp` using the `"url"` key.
<!-- END GENERATED: additional-deployment-options -->

## Available MCP Tools

This table is auto-generated from the live server — do not edit by hand.

<!-- MCP-TOOLS-TABLE:START -->

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `pulse_fetch` | `PULSETOOL` | Fetch one item (full text/body/transcript). CONCEPT:PULSE-001 |
| `pulse_list` | `PULSETOOL` | List items from a source channel/feed. CONCEPT:PULSE-001 |
| `pulse_search` | `PULSETOOL` | Search a source and return normalized documents. CONCEPT:PULSE-001 |
| `pulse_status` | `PULSETOOL` | Per-source backend + credential health (the doctor). CONCEPT:PULSE-001 |
| `pulse_transcribe` | `PULSETOOL` | Transcribe video/audio to text. CONCEPT:PULSE-005 |

_5 action-routed tools (default `MCP_TOOL_MODE=condensed`). Each is enabled unless its toggle is set false; set `MCP_TOOL_MODE=verbose` (or `both`) for the 1:1 per-operation surface. Auto-generated — do not edit._
<!-- MCP-TOOLS-TABLE:END -->

## Install Python Package

```bash
python -m pip install pulselink-mcp
```


<!-- BEGIN agent-os-genesis-deploy (generated; do not edit between markers) -->

## Deploy with `agent-os-genesis`

This package can be provisioned for you — skill-guided — by the **`agent-os-genesis`**
universal skill (its *single-package deploy mode*): it picks your install method, seeds
secrets to OpenBao/Vault (or `.env`), trusts your enterprise CA, registers the MCP
server, and verifies it — the same machinery that stands up the whole Agent OS, narrowed
to just this package. Ask your agent to **"deploy `pulselink-mcp` with agent-os-genesis"**.

| Install mode | Command |
|------|---------|
| Bare-metal, prod (PyPI) | `uvx pulselink-mcp` · or `uv tool install pulselink-mcp` |
| Bare-metal, dev (editable) | `uv pip install -e ".[all]"` · or `pip install -e ".[all]"` |
| Container, prod | deploy `knucklessg1/pulselink-mcp:latest` via docker-compose / swarm / podman / podman-compose / kubernetes |
| Container, dev (editable) | deploy `docker/compose.dev.yml` (source-mounted at `/src`; edits live on restart) |

Secrets are read-existing + seeded via `vault_sync` — you are only prompted for what's missing.

<!-- END agent-os-genesis-deploy -->
