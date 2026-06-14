# Installation

`pulselink-mcp` is a standard Python package and a prebuilt container image.

## Requirements

- **Python 3.11 – 3.14**.
- A reachable target service instance and access token.

## From PyPI (recommended)

```bash
pip install pulselink-mcp
```

### Optional extras

| Extra | Install | Pulls in |
|---|---|---|
| `mcp` | `pip install "pulselink-mcp[mcp]"` | FastMCP MCP-server runtime (`agent-utilities[mcp]`) |
| `agent` | `pip install "pulselink-mcp[agent]"` | Pydantic-AI agent + Logfire tracing |
| `all` | `pip install "pulselink-mcp[all]"` | Everything above |

## From source

```bash
git clone https://github.com/Knuckles-Team/pulselink-mcp.git
cd pulselink-mcp
pip install -e ".[all]"
```

## Docker

```bash
docker pull knucklessg1/pulselink-mcp:latest
```
