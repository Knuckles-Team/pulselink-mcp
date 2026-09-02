#!/usr/bin/python

import logging
import sys
from typing import Any

from agent_utilities.base_utilities import get_logger
from agent_utilities.core.config import load_config
from agent_utilities.mcp.server_factory import create_mcp_server
from agent_utilities.mcp.verbose_tools import register_tool_surface

from pulselink_mcp.api import PulseLinkClient
from pulselink_mcp.auth import create_client
from pulselink_mcp.sources.base import UnavailableCredentialProvider

from .mcp import register_pulse_tools

__version__ = "2.1.0"

logger = get_logger(name="MCP_Server")
logger.setLevel(logging.INFO)


def get_mcp_instance(*, secrets_client: Any = None) -> tuple[Any, Any, Any]:
    """Initialize PulseLink from explicitly injected encrypted-secret authority."""
    load_config()
    client = (
        PulseLinkClient(UnavailableCredentialProvider())
        if secrets_client is None
        else create_client(secrets_client)
    )

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


def mcp_server():
    if any(argument in {"-h", "--help"} for argument in sys.argv[1:]):
        get_mcp_instance()
        return

    from agent_utilities.knowledge_graph.core.graph_compute import GraphComputeEngine
    from agent_utilities.security.secrets_client import (
        InEpistemicGraphBackend,
        SecretsClient,
    )

    engine = GraphComputeEngine.get_or_create(
        graph_name="__secrets__",
        backend_type="rust",
    )
    secrets_client = SecretsClient(InEpistemicGraphBackend(engine))
    mcp, args, _ = get_mcp_instance(secrets_client=secrets_client)

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
