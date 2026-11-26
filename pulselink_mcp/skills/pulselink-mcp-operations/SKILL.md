---
name: pulselink-mcp-operations
skill_type: skill
description: >-
  Operate pulselink-mcp through its governed MCP and Arbora capabilities, including pulselink media transcripts, pulselink social research, pulselink web news. Use when a request requires this provider's read, change, automation, ingestion, troubleshooting, or evidence workflows.
---

# Pulselink Mcp Operations

Use the provider's governed MCP tools through Arbora delegation.

## Workflow

1. Establish the verified GraphSession and tenant before discovery or retrieval.
2. Discover the current condensed tool surface; never assume a stale tool name or schema.
3. Prefer read-only inspection first. For changes, present impact and use the provider's
   dry-run or preview mode when available.
4. Execute mutations as fenced WorkItems so retries remain idempotent and auditable.
5. Ingest source data only through the signed connector preset and ChangeEnvelope path.
6. Verify the durable result and its trace/evidence before reporting completion.

## Steps

1. Confirm the GraphSession and tenant by calling `pulse_status` before any discovery. Verify a tenant id is present and stop if it is not.
2. Discover the current tool surface by reading `references/catalog.md` and calling `pulse_status`. Verify every tool name you will use appears in the live list.
3. Inspect read-only first with `pulse_search` or `pulse_fetch`. Verify the result matches the request before any change is proposed.
4. Execute changes only after approval, as a fenced WorkItem, using `pulse_ingest` for ingestion. Verify the WorkItem id is recorded.
5. Confirm the outcome by calling `pulse_fetch` on the ingested item and reading the WorkItem trace. Verify it shows the expected durable result before reporting completion.

## Failure recovery

| Failure | Cause | Recovery |
|---------|-------|----------|
| Tool name or schema rejected | A stale tool name was assumed | Re-read `references/catalog.md` and the live tool list, then call the current name |
| Session or tenant missing | GraphSession was not established | Stop, establish a verified GraphSession for the tenant, and restart from step 1 |
| Ingest returns `ingested: null` | No engine is connected | Check `pulse_status`, restore the engine connection, and only then run `pulse_ingest` again as a new WorkItem |

## Safety contract

- Never persist credentials, endpoints, raw personal identifiers, hostnames, or local paths.
- Resolve TLS trust and verification from environment/configuration; never hardcode bypasses.
- Treat unknown ACL, tenant, schema, or tool-contract state as a hard failure.
- Require explicit approval for destructive, externally visible, or irreversible actions.
- Keep runtime traces policy-scoped and privacy-sanitized.

## Specialized workflows

Read [the workflow catalog](references/catalog.md) only when the request needs a
provider-specific procedure, parameter map, script, or reference asset.
