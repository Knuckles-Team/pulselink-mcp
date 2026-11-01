# CONN-PULSELINK-MCP-CONNECTOR-CONTENT — The connector serves its packaged content

Owner: pulselink-mcp. Cross-repo IDs: `SCION-CONNECTOR-CONTROL-R071`, `SCION-CONNECTOR-CONTROL-R073`.

## Purpose and user stories

The `pulselink-mcp` server serves its packaged skills, prompts and ontology to any client, with no wiring of its own.

## Delivery mapping

Component: pulselink-mcp connector

Code: ../../pulselink_mcp/__init__.py

## Why a new spec

Searched `specs/` of `pulselink-mcp` with `git grep` for the terms of this spec. No other spec of this repository owns the capability, so this spec owns it.

## User Scenarios & Testing

### User Story 1 - Default content (Priority: P1)

The fleet operator and the engine rely on this behaviour of `pulselink-mcp`: `pyproject.toml` declares `pulselink-mcp` as the single `scion_sdk.connector` entry point. It is proven independently of the other stories.

**Acceptance Scenarios**:

1. **Given** the `pulselink-mcp` connector built from the default branch, **When** `tests/test_default_content_surfaces.py::test_default_content_surfaces` runs, **Then** `resources/list` includes `skill://` and `ontology://`; `prompts/list` includes each packaged prompt.

### User Story 2 - Register the offline bookmark reader (Priority: P1)

The fleet operator and the engine rely on this behaviour of `pulselink-mcp`: Subsystem: connector. It is proven independently of the other stories.

**Acceptance Scenarios**:

1. **Given** the `pulselink-mcp` connector built from the default branch, **When** `tests/test_bookmark_tool_served.py::test_tool_reads_authorized_root_only` runs, **Then** test: `tests/test_bookmark_tool_served.py::test_tool_reads_authorized_root_only` (L3) calls the tool for a file inside and a path outside the root.

### Edge Cases

- The vendor service is unreachable or rejects the credential: the connector returns the SDK typed error and never a partial result.
- An argument outside the documented inputs is refused with the SDK typed refusal and causes no effect on the vendor service.

## Requirements

- **FR-001**: Default content. Rows: `CONN-PULSELINK-MCP-CONNECTOR-CONTENT-R001`.
- **FR-002**: Register the offline bookmark reader. Rows: `CONN-PULSELINK-MCP-CONNECTOR-CONTENT-R002`.

## Success Criteria

- **SC-001**: `resources/list` includes `skill://` and `ontology://`; `prompts/list` includes each packaged prompt. Rows: `CONN-PULSELINK-MCP-CONNECTOR-CONTENT-R001`.
- **SC-002**: Test: `tests/test_bookmark_tool_served.py::test_tool_reads_authorized_root_only` (L3) calls the tool for a file inside and a path outside the root. Rows: `CONN-PULSELINK-MCP-CONNECTOR-CONTENT-R002`.

## Assumptions

- The `pulselink-mcp` package keeps the entry point and module layout named in the rows.
- The shared SDK supplies the transport, authentication, retry and certification helpers the rows reuse.

## Traceability

| Label | Rows | Design section | Test ID | Evidence |
|---|---|---|---|---|
| FR-001 | `CONN-PULSELINK-MCP-CONNECTOR-CONTENT-R001` | plan.md Production caller chain | T-001 | tests/test_default_content_surfaces.py::test_default_content_surfaces |
| FR-002 | `CONN-PULSELINK-MCP-CONNECTOR-CONTENT-R002` | plan.md Production caller chain | T-002 | tests/test_bookmark_tool_served.py::test_tool_reads_authorized_root_only |
