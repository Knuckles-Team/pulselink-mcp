import inspect
from unittest.mock import Mock

import pytest
from scion_sdk.credentials.resolver import CredentialResolver

from pulselink_mcp.api import PulseLinkClient
from pulselink_mcp.mcp_server import get_mcp_instance, get_runtime_mcp_instance
from pulselink_mcp.sources.base import CredentialAuthorityUnavailable
from pulselink_mcp.sources.contracts import UnavailableCredentialAuthority
from pulselink_mcp.sources.forums import HackerNewsBackend


def test_mcp_instance_registration(monkeypatch):
    monkeypatch.setattr("sys.argv", ["pulselink-mcp"])
    mcp, args, middlewares = get_runtime_mcp_instance(
        credential_resolver=Mock(spec=CredentialResolver)
    )
    assert mcp is not None


def test_runtime_constructor_annotation_is_import_safe() -> None:
    parameter = inspect.signature(get_runtime_mcp_instance).parameters[
        "credential_resolver"
    ]
    assert "CredentialResolver" in str(parameter.annotation)


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


@pytest.mark.asyncio
async def test_runtime_and_canonical_introspection_keep_separate_clients(monkeypatch):
    from scion_sdk.connector import build_server

    resolver = Mock(spec=CredentialResolver)
    captured = []
    import importlib

    server_module = importlib.import_module("pulselink_mcp.mcp_server")

    register = server_module.register_pulse_tools

    def capture(server, client):
        captured.append(client)
        return register(server, client)

    monkeypatch.setattr(server_module, "register_pulse_tools", capture)
    command_args = ["--transport", "stdio", "--auth-type", "none"]
    runtime, _, _ = get_runtime_mcp_instance(
        credential_resolver=resolver, command_args=command_args
    )
    _, canonical = build_server("pulselink_mcp", command_args=command_args)
    introspection, _, _ = get_mcp_instance(command_args=command_args)
    assert len(captured) == 3
    assert len({id(client) for client in captured}) == 3
    captured[0]._credential_authority.require_runtime_authority()
    for server in (canonical, introspection):
        status = await server.get_tool("pulse_status")
        with pytest.raises(CredentialAuthorityUnavailable):
            await status.run({})
    # The executable server retains its own resolver-composed authority after
    # both schema-only surfaces are constructed; they never replace its client.
    captured[0]._credential_authority.require_runtime_authority()
    assert runtime is not canonical
