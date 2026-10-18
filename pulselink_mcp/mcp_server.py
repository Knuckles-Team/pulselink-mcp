#!/usr/bin/python
from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any

from agent_connector_sdk.config import load_config
from agent_connector_sdk.mcp.server import create_mcp_server
from agent_connector_sdk.mcp.tool_surface import register_tool_surface

from pulselink_mcp.api import PulseLinkClient
from pulselink_mcp.auth import create_client
from pulselink_mcp.sources.contracts import UnavailableCredentialAuthority

from .mcp import register_pulse_tools

if TYPE_CHECKING:
    from agent_connector_sdk.credentials.resolver import CredentialResolver

__version__ = "2.2.1"

logger = logging.getLogger("MCP_Server")
logger.setLevel(logging.INFO)


def _build_mcp(client: PulseLinkClient) -> tuple[Any, Any, Any]:
    """Register one already-composed client on a new MCP surface."""
    load_config()
    args, mcp, middlewares = create_mcp_server(
        name="PulseLink MCP",
        version=__version__,
        instructions=(
            "PulseLink — keyless open-web & social research reach. Search, fetch, "
            "list, and transcribe across YouTube, Reddit, X, Hacker News, the web, "
            "RSS/news, GitHub and more; pulse_status reports per-source health."
        ),
    )

    register_tool_surface(
        mcp,
        client_cls=PulseLinkClient,
        get_client=lambda: client,
        service="pulselink-mcp",
        registrars=[
            ("pulse", "PULSETOOL", lambda target: register_pulse_tools(target, client))
        ],
    )

    for mw in middlewares:
        mcp.add_middleware(mw)

    return mcp, args, middlewares


def get_mcp_instance() -> tuple[Any, Any, Any]:
    """Build the non-executable schema surface used by fleet introspection."""
    client = PulseLinkClient(
        UnavailableCredentialAuthority(),
    )
    return _build_mcp(client)


def get_runtime_mcp_instance(
    *,
    credential_resolver: CredentialResolver,
) -> tuple[Any, Any, Any]:
    """Build an executable surface from an explicit credential resolver."""
    return _build_mcp(create_client(credential_resolver))


def mcp_server():
    if any(argument in {"-h", "--help"} for argument in sys.argv[1:]):
        get_mcp_instance()
        return

    from agent_connector_sdk.credentials.resolution import (
        default_credential_resolver,
    )

    mcp, args, _ = get_runtime_mcp_instance(
        credential_resolver=default_credential_resolver()
    )

    print(f"PulseLink MCP v{__version__}", file=sys.stderr)
    print("\nStarting MCP Server", file=sys.stderr)
    print(f"  Transport: {args.transport.upper()}", file=sys.stderr)

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        logger.error(f"Invalid transport: {args.transport}")
        sys.exit(1)


if __name__ == "__main__":
    mcp_server()
