# pulselink-mcp — Concept Overview

> **Category**: Integration | **Ecosystem Role**: MCP Server
> Built on [`agent-connector-sdk`](https://github.com/Knuckles-Team/agent-connector-sdk) — the unified AGI Harness.

## Description

PulseLink — keyless open-web & social research source (MCP Server)

## Architecture

This project follows the standardized agent-package pattern:

- **Modular Design**: split into `api/` (client mixins) and `mcp/` (action-routed
  tool modules) for cleaner organization.
- **Dynamic Tool Registration**: action-routed dynamic tool tags, strictly
  lowercase, each togglable with a `*TOOL` environment flag.

## Concept Registry

This project implements or inherits the following ecosystem concepts:

| Concept ID | Description | Source |
|:-----------|:------------|:-------|
| ECO-4.1 | MCP & Universal Skills | `agent-connector-sdk` (inherited) |

> 📖 **Full Registry**: See [`agent-connector-sdk/docs/overview.md`](https://github.com/Knuckles-Team/agent-connector-sdk/blob/main/docs/overview.md) for the complete 5-Pillar concept index.
