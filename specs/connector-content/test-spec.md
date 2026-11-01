# CONN-PULSELINK-MCP-CONNECTOR-CONTENT — Test specification

Governing spec: [spec.md](spec.md).

| Test ID | Requirement | Proving test | Expected observation |
|---|---|---|---|
| T-001 | `CONN-PULSELINK-MCP-CONNECTOR-CONTENT-R001` | `tests/test_default_content_surfaces.py::test_default_content_surfaces` | `resources/list` includes `skill://` and `ontology://`; `prompts/list` includes each packaged prompt. |
| T-002 | `CONN-PULSELINK-MCP-CONNECTOR-CONTENT-R002` | `tests/test_bookmark_tool_served.py::test_tool_reads_authorized_root_only` (planned) | Test: `tests/test_bookmark_tool_served.py::test_tool_reads_authorized_root_only` (L3) calls the tool for a file inside and a path outside the root. |

## Negative and boundary cases

Each proving test above includes the refusal or error case that its row names. A vendor outage or an unauthorised call must return the SDK typed error.

## Quality and release proof

Run `uv run pytest tests` and `pre-commit run --all-files` from the repository root. A planned test is added by the code change that lands the row.
