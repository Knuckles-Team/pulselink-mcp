# CONN-PULSELINK-MCP-CONNECTOR-CONTENT — Requirements

Governing spec: [spec.md](spec.md).

Each row is one requirement. A row names the file it touches and the test that proves it. The generator sets each row's state in `status.json`.

| ID | Requirement | Acceptance |
|---|---|---|
| `CONN-PULSELINK-MCP-CONNECTOR-CONTENT-R001` | **Default content.** `pyproject.toml` declares `pulselink-mcp` as the single `scion_sdk.connector` entry point. The server lists the packaged `skill://` and `ontology://` resources and the packaged prompts with no `content=` argument. Proving test: `tests/test_default_content_surfaces.py`. | `resources/list` includes `skill://` and `ontology://`; `prompts/list` includes each packaged prompt. |
| `CONN-PULSELINK-MCP-CONNECTOR-CONTENT-R002` | **Register the offline bookmark reader.** Subsystem: connector. Caller: process start → `pulselink_mcp/mcp_server.py` → `scion_sdk.adapters.bookmark_source.register_bookmark_tool(server, BookmarkReader(root=...))`. Config key `PULSELINK_BOOKMARK_ROOT` names the authorized directory; no default, and a missing key skips registration. Refusals: reuse SCION-SOURCE-INGEST-R005.10. Writes: none. Depends on: SCION-SOURCE-INGEST-R005.9. | Test: `tests/test_bookmark_tool_served.py::test_tool_reads_authorized_root_only` (L3) calls the tool for a file inside and a path outside the root. |
