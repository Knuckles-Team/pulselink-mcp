---
name: pulselink-mcp-development
skill_type: skill
description: >-
  Develop and maintain the PulseLink connector while preserving its keyless
  source ladder, injected credential authority, MCP tool surfaces, source
  declarations, package content, and release evidence.
license: MIT
tags: [pulselink, connector, mcp, sdk, research]
metadata:
  author: Knuckles-Team
  version: '0.1.0'
---
# PulseLink MCP Development

This is the repository development skill for `pulselink-mcp`. The owning delivery
row is `PIPE-CONNSPEC-R155.4`; use this skill with the repository `AGENTS.md`,
the connector-content specification, and the focused tests.

## Repository and runtime map

- `pulselink_mcp/__init__.py` exposes the SDK `Connector` and keeps the safe
  import boundary for the core client and optional MCP server.
- `pulselink_mcp/api/api_client_pulse.py` is the client facade over the source
  adapters. Keep the stable search, fetch, list, status, ingest, and transcribe
  contracts while preserving source-specific fallback behavior.
- `pulselink_mcp/auth.py` composes `PulseLinkClient` from an injected
  `CredentialResolver`; `pulselink_mcp/credentials.py` resolves the
  `SOURCE_CREDENTIALS` descriptors without storing secret values in source.
- `pulselink_mcp/mcp_server.py` builds `ConnectorContent`, registers the
  `pulse` tool surface behind `PULSETOOL`, and supports the legacy and canonical
  SDK server paths. `pulselink_mcp/mcp/mcp_pulse.py` owns the action-routed
  registrars.
- `pulselink_mcp/sources/**` contains the source ladders, HTTP transport, and
  unavailable-credential boundary. `pulselink_mcp/connector_sources.py` is the
  live `pulselink-mcp` source and schema declaration; edit declarations rather
  than duplicating them in tool code.
- `pulselink_mcp/skills/**`, `prompts/**`, `ontology/**`, and `connectors/**`
  are package data. A skill change therefore needs a package-content check before
  publication. `pyproject.toml` also exposes the `pulselink-mcp` CLI and SDK
  connector entry point.

## Connection and security contract

PulseLink is a source ladder, not one remote endpoint. Keyless sources such as
web, RSS/news, Hacker News, YouTube, V2EX, and Bilibili must continue to work
without credentials. `SOURCE_CREDENTIALS` is an operator-supplied JSON map of
source descriptors; secret fields are URI references resolved by the injected
credential authority. Never place tokens, cookies, tenant data, or resolved
endpoints in code, skills, fixtures, logs, or docs.

`PULSELINK_TLS_PROFILE`, `PULSELINK_TLS_PROFILE_REF`, `TLS_PROFILE`, and
`TLS_PROFILES_REF` select the shared verified TLS policy. Keep certificate and
hostname verification enabled. `MCP_TOOL_MODE` selects the intent, condensed,
verbose, or both tool surfaces; `PULSETOOL` gates the condensed PulseLink
registrar. Preserve the supported `stdio`, `streamable-http`, and `sse`
transports, host/port configuration, and the SDK's runtime secret boundary.

## Rapid delivery: the 5-minute contract

1. Read the owning connector-content spec, this skill, `AGENTS.md`, and the
   focused tests before changing a connector surface.
2. Inspect the active `Connector`, MCP registrar and action maps, source client
   and ladders, credential resolver, source declarations, and package-data rules.
3. Make the smallest connector-owned change. Preserve public tool names and
   payloads, source IDs and mappings, keyless fallbacks, credential authority,
   TLS verification, canonical and legacy routes, and the SDK `Connector`
   boundary.
4. Run the directly bound tests with `uv run --locked --extra test pytest`, then
   run the repository hooks. Use the approved narrow test wrapper when the lane
   requires it; never bypass a hook or a failing gate.
5. If package code or packaged content changes, bump the version with the
   repository's `.bumpversion.cfg`, refresh `uv.lock`, and inspect the built
   wheel and sdist for the intended `pulselink_mcp/skills/**` content before
   publication.
6. Treat Pages and containers as separate evidence. After the exact main commit
   publishes, verify the Pages revision and `/spec-delivery/` artifacts. The
   container-release workflow is pin-driven: its public-wheel guard runs before
   the legacy-profile container build, and a deployed image pin must not move
   until the corresponding public package has passed its exact guard.

## Focused validation

For client or source changes, run the smallest relevant test file and keep
keyless, credentialed, and unavailable-authority paths distinct. Add source
mapping or ontology checks only when those declarations change. For a skill or
package-data change, verify frontmatter, the required rapid-delivery heading,
source-specific contract references, and wheel/sdist contents without contacting
an external provider.

Use the repository commands from `AGENTS.md`:

```bash
uv sync --locked
uv run --locked --extra test pytest -q tests/test_pulselink_development_skill.py
uvx pre-commit run --all-files
```

## Publication and Pages

`.github/workflows/pipeline.yml` publishes the Python package through
`Knuckles-Team/pipelines/.github/workflows/python_pipeline.yml@main` on `main`.
Its path filters deliberately leave the Docker pin refresh separate. The
`.github/workflows/container-release.yml` caller first verifies the exact public
wheel with `legacy-profile: true`, then invokes the shared container pipeline
with `legacy_profile: true` and `render_connector: false`; preserve that custom
Dockerfile and public-first ordering. `.github/workflows/pages.yml` delegates
README/docs publication to `pages_pipeline.yml@main`.

A successful local test or workflow run is not package, Pages, or image proof.
Record the exact merged source, public wheel/sdist hashes, skill bytes, Pages
revision, and image digest separately. Do not hand-edit central Pipelines
status or promote a rollup from a connector change. Never put credentials,
provider data, generated release artifacts, or bypass instructions in this
skill.
