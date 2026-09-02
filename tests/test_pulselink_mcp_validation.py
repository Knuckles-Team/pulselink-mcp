import inspect
from unittest.mock import Mock

import pytest
from agent_utilities.security.secrets_client import SecretsClient

from pulselink_mcp.api import PulseLinkClient
from pulselink_mcp.mcp_server import get_mcp_instance, get_runtime_mcp_instance
from pulselink_mcp.sources.base import CredentialAuthorityUnavailable
from pulselink_mcp.sources.contracts import UnavailableCredentialAuthority
from pulselink_mcp.sources.forums import HackerNewsBackend


def test_mcp_instance_registration(monkeypatch):
    monkeypatch.setattr("sys.argv", ["pulselink-mcp"])
    mcp, args, middlewares = get_runtime_mcp_instance(
        secrets_client=Mock(spec=SecretsClient)
    )
    assert mcp is not None


def test_runtime_constructor_annotation_is_import_safe() -> None:
    parameter = inspect.signature(get_runtime_mcp_instance).parameters["secrets_client"]
    assert "SecretsClient" in str(parameter.annotation)


def test_unavailable_authority_blocks_keyless_backend_before_access(monkeypatch):
    backend_accessed = False

    def mark_backend_accessed(*_args, **_kwargs):
        nonlocal backend_accessed
        backend_accessed = True
        raise AssertionError("BACKEND_ACCESSED")

    monkeypatch.setattr(HackerNewsBackend, "search", mark_backend_accessed)
    client = PulseLinkClient(UnavailableCredentialAuthority())

    with pytest.raises(CredentialAuthorityUnavailable):
        client.search("hackernews", "authority")

    assert backend_accessed is False


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
