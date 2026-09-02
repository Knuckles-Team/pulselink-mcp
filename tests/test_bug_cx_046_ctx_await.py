# tests/test_bug_cx_046_ctx_await.py
"""Regression test for BUG-CX-046.

`ctx.info(...)` is an async coroutine method on fastmcp's `Context`. Calling
it without `await` creates a coroutine object that is discarded, the log
line never emits, and Python raises `RuntimeWarning: coroutine
'Context.info' was never awaited`. This test proves the tool under test
actually awaits `ctx.info(...)`.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from pulselink_mcp.mcp.mcp_pulse import register_pulse_tools


@pytest.mark.asyncio
async def test_pulse_status_awaits_ctx_info():
    tools_dict = {}

    class MockMCP:
        def tool(self, *args, **kwargs):
            def decorator(func):
                tools_dict[func.__name__] = func
                return func

            return decorator

    mock_mcp: Any = MockMCP()
    mock_client = MagicMock()
    mock_client.status.return_value = {"ok": True}
    register_pulse_tools(mock_mcp, mock_client)  # type: ignore

    mock_ctx = MagicMock()
    mock_ctx.info = AsyncMock()

    pulse_status = tools_dict["pulse_status"]
    await pulse_status(ctx=mock_ctx)

    mock_ctx.info.assert_awaited_once()
