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

## Install Python Package

```bash
python -m pip install pulselink-mcp
```
