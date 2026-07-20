# PulseLink MCP
## CLI or API | MCP | Agent

![PyPI - Version](https://img.shields.io/pypi/v/pulselink-mcp)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
![PyPI - Downloads](https://img.shields.io/pypi/dd/pulselink-mcp)
![GitHub Repo stars](https://img.shields.io/github/stars/Knuckles-Team/pulselink-mcp)
![PyPI - License](https://img.shields.io/pypi/l/pulselink-mcp)
![GitHub last commit (by committer)](https://img.shields.io/github/last-commit/Knuckles-Team/pulselink-mcp)

*Version: 1.0.1*

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

### MCP Configuration Examples

<!-- MCP-CONFIG-EXAMPLES:START -->

> **Install the connector-focused `[mcp]` extra.** Examples use `pulselink-mcp[mcp]` to add
> FastMCP / FastAPI through `agent-utilities[mcp]`; the required Agent Utilities core
> still carries `epistemic-graph[full]`. The `[agent-runtime]` extra additionally
> enables model orchestration.

#### stdio Transport (local IDEs — Cursor, Claude Desktop, VS Code)

```json
{
  "mcpServers": {
    "pulselink-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "pulselink-mcp[mcp]",
        "pulselink-mcp"
      ],
      "env": {
        "MCP_TOOL_MODE": "intent",
        "PULSETOOL": "True",
        "XAI_BASE_URL": "https://api.x.ai/v1",
        "XAI_SEARCH_MODEL": "grok-4.3",
        "XAI_SEARCH_RETRIES": "2",
        "XAI_SEARCH_TIMEOUT_SECONDS": "180"
      }
    }
  }
}
```

Runtime references require an alias-aware launcher such as GraphOS. Other
launchers must omit those entries and inject the resolved values through their
own runtime secret boundary.

#### Streamable-HTTP Transport (networked / production)

```json
{
  "mcpServers": {
    "pulselink-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "pulselink-mcp[mcp]",
        "pulselink-mcp",
        "--transport",
        "streamable-http",
        "--port",
        "8000"
      ],
      "env": {
        "TRANSPORT": "streamable-http",
        "HOST": "127.0.0.1",
        "PORT": "8000",
        "MCP_TOOL_MODE": "intent",
        "PULSETOOL": "True",
        "XAI_BASE_URL": "https://api.x.ai/v1",
        "XAI_SEARCH_MODEL": "grok-4.3",
        "XAI_SEARCH_RETRIES": "2",
        "XAI_SEARCH_TIMEOUT_SECONDS": "180"
      }
    }
  }
}
```

Alternatively, connect to a pre-deployed Streamable-HTTP instance by `url`:

```json
{
  "mcpServers": {
    "pulselink-mcp": {
      "url": "http://localhost:8000/pulselink-mcp/mcp"
    }
  }
}
```

Run a reviewed container image as a least-privilege stdio child (no
listener or published port):

```bash
docker run -i --rm \
  --read-only \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --pids-limit=256 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m \
  -e TRANSPORT=stdio \
  -e MCP_TOOL_MODE=intent \
  -e PULSETOOL=True \
  -e XAI_BASE_URL=https://api.x.ai/v1 \
  -e XAI_SEARCH_MODEL=grok-4.3 \
  -e XAI_SEARCH_RETRIES=2 \
  -e XAI_SEARCH_TIMEOUT_SECONDS=180 \
  registry.example.invalid/pulselink-mcp@sha256:<digest> pulselink-mcp
```

For containerized network HTTP, supply an authenticated TLS ingress (or
direct server TLS), exact `MCP_ALLOWED_HOSTS`, and an exact trusted-proxy
CIDR policy through the operator-owned deployment profile. The generator
does not emit an unauthenticated non-loopback listener.

_Auto-generated from the code-read env surface (`MCP_TOOL_MODE` + package vars) — do not edit._
<!-- MCP-CONFIG-EXAMPLES:END -->

<!-- BEGIN GENERATED: additional-deployment-options -->
### Additional Deployment Options

`pulselink-mcp` can run as a local stdio process or container, or behind a remote
network boundary. The
[Deployment guide](https://knuckles-team.github.io/pulselink-mcp/deployment/) carries
the detailed transport contract.

- **Local container** — launch a reviewed immutable image as a least-privilege
  stdio child with no listener or published port.
- **Remote URL** — connect through an operator-supplied authenticated HTTPS
  ingress. Keep its URL, outbound identity references, trust profile, and exact
  `MCP_ALLOWED_HOSTS` in `AgentConfig`.
<!-- END GENERATED: additional-deployment-options -->

## Available MCP Tools

This table is auto-generated from the live server — do not edit by hand.

<!-- MCP-TOOLS-TABLE:START -->

#### Condensed action-routed tools (default — `MCP_TOOL_MODE=condensed`)

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `pulse_fetch` | `PULSETOOL` | Fetch one item (full text/body/transcript). CONCEPT:PK-OS.governance.search-fetch-list-transcribe |
| `pulse_list` | `PULSETOOL` | List items from a source channel/feed. CONCEPT:PK-OS.governance.search-fetch-list-transcribe |
| `pulse_search` | `PULSETOOL` | Search a source and return normalized documents. CONCEPT:PK-OS.governance.search-fetch-list-transcribe |
| `pulse_status` | `PULSETOOL` | Per-source backend + credential health (the doctor). CONCEPT:PK-OS.governance.search-fetch-list-transcribe |
| `pulse_transcribe` | `PULSETOOL` | Transcribe video/audio to text. CONCEPT:PK-OS.governance.audio-video-sources-transcript |

#### Verbose 1:1 API-mapped tools (`MCP_TOOL_MODE=verbose` or `both`)

<details>
<summary>6 per-operation tools — one per public API method (click to expand)</summary>

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `pulselink_fetch` | `PULSE_LINK_CLIENTTOOL` | Invoke the fetch operation. |
| `pulselink_list_items` | `PULSE_LINK_CLIENTTOOL` | Invoke the list_items operation. |
| `pulselink_search` | `PULSE_LINK_CLIENTTOOL` | Invoke the search operation. |
| `pulselink_sources` | `PULSE_LINK_CLIENTTOOL` | Invoke the sources operation. |
| `pulselink_status` | `PULSE_LINK_CLIENTTOOL` | Invoke the status operation. |
| `pulselink_transcribe` | `PULSE_LINK_CLIENTTOOL` | Invoke the transcribe operation. |

</details>

_5 action-routed tool(s) (default) · 6 verbose 1:1 tool(s). Each is enabled unless its `<DOMAIN>TOOL` toggle is set false; `MCP_TOOL_MODE` selects the surface (`condensed` default · `verbose` 1:1 · `both`). Auto-generated — do not edit._
<!-- MCP-TOOLS-TABLE:END -->

## Environment Variables

Every variable the server reads.

### MCP server / transport
| Variable | Description | Default |
|----------|-------------|---------|
| `TRANSPORT` | `stdio`, `streamable-http`, or `sse` | `stdio` |
| `HOST` | Bind host (HTTP transports) | `0.0.0.0` |
| `PORT` | Bind port (HTTP transports) | `8000` |
| `MCP_TOOL_MODE` | Tool surface: `condensed`, `verbose`, or `both` | `condensed` |
| `MCP_ENABLED_TOOLS` / `MCP_DISABLED_TOOLS` | Comma-separated tool allow/deny list | — |
| `MCP_ENABLED_TAGS` / `MCP_DISABLED_TAGS` | Comma-separated tag allow/deny list | — |
| `DEBUG` | Verbose logging | `False` |
| `PYTHONUNBUFFERED` | Unbuffered stdout (recommended in containers) | `1` |

### X / xAI Live Search (optional)
Used by the X source backend; all optional with sensible defaults.

| Variable | Description | Default |
|----------|-------------|---------|
| `XAI_BASE_URL` | xAI API base URL | `https://api.x.ai/v1` |
| `XAI_SEARCH_MODEL` | Model used for X live search | `grok-4.3` |
| `XAI_SEARCH_TIMEOUT_SECONDS` | Per-request timeout (seconds) | `180` |
| `XAI_SEARCH_RETRIES` | Retry attempts on failure | `2` |

### Source credentials (keyless-first)
| Variable | Description | Default |
|----------|-------------|---------|
| `SOURCE_CREDENTIALS` | JSON object mapping a source → credential descriptor (secret values are URI refs resolved via the secrets backend: `vault://`, `env://`, `sqlite://`). Keyless sources (youtube, web, rss, news, hackernews, v2ex, bilibili) need nothing here; auth-laddered sources (x, reddit, github, exa…) light up higher-fidelity backends when set. | — |

### Tool toggles
Each action-routed tool can be disabled individually via its toggle env var (set to `false`).
The full list is in the [Available MCP Tools](#available-mcp-tools) table above.

| Variable | Description | Default |
|----------|-------------|---------|
| `PULSETOOL` | Enable the PulseLink source tools (`pulse_search` / `pulse_list` / `pulse_fetch` / `pulse_transcribe` / `pulse_status`) | `True` |

### Telemetry & governance
| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_OTEL` | Enable OpenTelemetry export | `True` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint | — |
| `OTEL_EXPORTER_OTLP_PUBLIC_KEY` / `OTEL_EXPORTER_OTLP_SECRET_KEY` | OTLP auth keys | — |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | OTLP protocol (e.g. `http/protobuf`) | — |
| `EUNOMIA_TYPE` | Authorization mode: `none`, `embedded`, `remote` | `none` |
| `EUNOMIA_POLICY_FILE` | Embedded policy file | `mcp_policies.json` |
| `EUNOMIA_REMOTE_URL` | Remote Eunomia server URL | — |

### Agent CLI (full `[agent]` runtime only)
| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_URL` | URL of the MCP server the agent connects to | `http://localhost:8000/mcp` |
| `PROVIDER` | LLM provider (e.g. `openai`) | `openai` |
| `MODEL_ID` | Model id (e.g. `gpt-4o`) | `gpt-4o` |
| `ENABLE_WEB_UI` | Serve the AG-UI web interface | `True` |

See [`.env.example`](.env.example) for a copy-paste starting point.

## Installation

Pick the extra that matches what you want to run:

| Extra | Installs | Use when |
|-------|----------|----------|
| `pulselink-mcp[mcp]` | Connector-focused MCP server (`agent-utilities[mcp]` — FastMCP/FastAPI + `epistemic-graph[full]`) | You only run the **MCP server** (smallest install / image) |
| `pulselink-mcp[agent]` | Agent runtime (`agent-utilities[agent-runtime,logfire]` — model orchestration + `epistemic-graph[full]`) | You run the **integrated agent** |
| `pulselink-mcp[all]` | Everything (`mcp` + `agent` + `logfire` + the `youtube`/`feeds`/`audio` source extras) | Development / both surfaces |

```bash
# Connector-focused MCP server (includes the shared graph engine)
uv pip install "pulselink-mcp[mcp]"

# Agent runtime (adds model orchestration to the shared graph engine)
uv pip install "pulselink-mcp[agent]"

# Everything (development)
uv pip install "pulselink-mcp[all]"      # or: python -m pip install "pulselink-mcp[all]"
```

> The optional source extras (`youtube` → `yt-dlp`, `feeds` → `feedparser`,
> `audio` → `faster-whisper`) are lazy-imported; the keyless web/forum/news/dev
> sources need none of them. Install `pulselink-mcp[sources]` for `youtube` + `feeds`.

### Container images (`:mcp` vs `:agent`)

One multi-stage `docker/Dockerfile` builds two right-sized images, selected by `--target`:

| Image tag | Build target | Contents | Entrypoint |
|-----------|--------------|----------|------------|
| `example/pulselink-mcp:mcp` | `--target mcp` | `pulselink-mcp[mcp]` — **connector-focused**, includes `epistemic-graph[full]`; no model-orchestration stack | `pulselink-mcp` |
| `example/pulselink-mcp@sha256:<digest>` | `--target agent` (default) | `pulselink-mcp[agent]` — **agent runtime**, model orchestration + `epistemic-graph[full]` | `pulselink-agent` |

```bash
docker build --target mcp   -t example/pulselink-mcp:mcp    docker/   # connector-focused MCP server
docker build --target agent -t example/pulselink-mcp:agent-local docker/   # agent runtime
```

`docker/mcp.compose.yml` runs the connector-focused `:mcp` server; `docker/agent.compose.yml` runs the
agent (`immutable agent digest`) with a co-located `:mcp` sidecar.

### Knowledge-graph database (`epistemic-graph`)

Both `[mcp]` and `[agent]` carry the **epistemic-graph** engine through the required
Agent Utilities core dependency (`epistemic-graph[full]`). The `[mcp]` extra keeps
the server connector-focused; `[agent]` additionally enables model orchestration. Local
deployments can use the bundled engine. For production or shared state, run
**epistemic-graph as a dedicated database service** and configure the runtime to use it.
Deployment recipes (single-node + Raft HA), connection configuration, and architecture
diagrams are documented in the
[epistemic-graph deployment guide](https://knuckles-team.github.io/epistemic-graph/deployment/).


<!-- BEGIN agent-utilities-deployment (generated; do not edit between markers) -->

## Deploy with `agent-utilities-deployment`

Provision this package with the consolidated **`agent-utilities-deployment`**
workflow. It selects an installed-package, editable-source, or immutable-container
path; records only runtime secret and TLS-profile references in `AgentConfig`; and
runs doctor, registration, policy, observability, and rollback gates. Ask your agent
to **"deploy `pulselink-mcp` with agent-utilities-deployment"**.

| Install mode | Command |
|------|---------|
| Installed package | `uv tool install "pulselink-mcp[mcp]"`, then run `pulselink-mcp` |
| Editable source | `uv pip install -e ".[agent]"`, then run `pulselink-mcp` |
| Immutable container | deploy `registry.example.invalid/pulselink-mcp@sha256:<digest>` through the operator-selected orchestrator |

The repository embeds no deployment profile, credential value, certificate path, or
environment-specific endpoint. Supply those at runtime through `AgentConfig` and the
configured secret provider.

<!-- END agent-utilities-deployment -->

<!-- GOVERNED-CAPABILITY:START -->
## Governed capability contract

This package ships a compact canonical skill surface with specialist procedures
kept as referenced workflows. The current MCP tools, skill metadata,
`connector_manifest.yml`, ontology, mappings, shapes, fixtures, migrations,
tool-schema fingerprints, and certification metadata form one versioned
capability contract. Validate them together; do not rely on stale tool names or
historical per-task skill wrappers.

Runtime endpoints, credentials, certificate trust, tenant identity, retention,
and observability policy are deployment inputs and are never packaged values.
See [Configuration, trust, and privacy](docs/configuration.md) before enabling a
network transport, connector ingestion, GraphOS delegation, or trace export.
<!-- GOVERNED-CAPABILITY:END -->
