"""A KG-ingest failure must not turn a successful search into 'Operation failed'."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from pulselink_mcp.mcp.mcp_pulse import register_pulse_tools


def _tools(client: Any) -> dict:
    tools: dict = {}

    class MockMCP:
        def tool(self, *args, **kwargs):
            def decorator(func):
                tools[func.__name__] = func
                return func

            return decorator

    register_pulse_tools(MockMCP(), client)  # type: ignore[arg-type]
    return tools


@pytest.mark.asyncio
async def test_search_result_survives_ingest_failure():
    client = MagicMock()
    client.search.return_value = {"documents": [{"id": "1", "title": "t"}]}
    boom = RuntimeError("knowledge ingest is not configured")
    with patch("pulselink_mcp.kg_ingest.ingest_pulse_documents", side_effect=boom):
        result = await _tools(client)["pulse_search"](
            source="hackernews", query="q", cursor=None, limit=1
        )
    assert result["documents"] == [{"id": "1", "title": "t"}]
    assert "not configured" in result["ingest"]["error"]


@pytest.mark.asyncio
async def test_client_failure_reports_its_cause():
    client = MagicMock()
    client.search.side_effect = ValueError("bad source")
    result = await _tools(client)["pulse_search"](
        source="x", query="q", cursor=None, limit=1
    )
    assert result["error"] == "Operation failed"
    assert result["cause"] == "bad source"
