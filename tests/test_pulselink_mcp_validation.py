from unittest.mock import Mock

import pytest
from agent_utilities.security.secrets_client import SecretsClient

from pulselink_mcp.mcp_server import get_mcp_instance, get_runtime_mcp_instance
from pulselink_mcp.sources.base import CredentialAuthorityUnavailable


def test_mcp_instance_registration(monkeypatch):
    monkeypatch.setattr("sys.argv", ["pulselink-mcp"])
    mcp, args, middlewares = get_runtime_mcp_instance(
        secrets_client=Mock(spec=SecretsClient)
    )
    assert mcp is not None


@pytest.mark.asyncio
async def test_introspection_surface_cannot_execute_or_report_ready(monkeypatch):
    monkeypatch.setattr("sys.argv", ["pulselink-mcp"])
    mcp, _, _ = get_mcp_instance()
    status_tool = await mcp.get_tool("pulse_status")

    with pytest.raises(
        CredentialAuthorityUnavailable,
        match="runtime credential authority is unavailable",
    ):
        await status_tool.run({})

    search_tool = await mcp.get_tool("pulse_search")
    with pytest.raises(CredentialAuthorityUnavailable):
        await search_tool.run({"source": "web", "query": "authority"})
