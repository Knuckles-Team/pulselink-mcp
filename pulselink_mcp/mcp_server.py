#!/usr/bin/python
from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any

from agent_connector_sdk.config import load_config
from agent_connector_sdk.mcp.server import create_mcp_server
from agent_connector_sdk.utilities import get_logger
from agent_utilities.mcp.verbose_tools import register_tool_surface

# A plain import of `secrets_client` is side-effect free (it only defines
# classes); the eager cost this module works around is *constructing*
# `InEpistemicGraphBackend`/`GraphComputeEngine`, not importing the module
# that defines them. Imported for real (not under TYPE_CHECKING) so
# `_LazyEpistemicGraphBackend` can genuinely subclass the ABC below.
from agent_utilities.security.secrets_client import SecretsBackend

from pulselink_mcp.api import PulseLinkClient
from pulselink_mcp.auth import create_client
from pulselink_mcp.sources.contracts import UnavailableCredentialAuthority

from .mcp import register_pulse_tools

if TYPE_CHECKING:
    from agent_utilities.security.secrets_client import SecretsClient

__version__ = "2.1.0"

logger = get_logger(name="MCP_Server")
logger.setLevel(logging.INFO)


class _LazyEpistemicGraphBackend(SecretsBackend):
    """Defer the local epistemic-graph engine connection to the first real
    secret lookup, never to server startup.

    ``mcp_server()`` used to build ``InEpistemicGraphBackend`` (and the
    ``GraphComputeEngine`` it wraps) eagerly, before the MCP surface could
    even answer ``tools/list`` -- so anything that only needs the tool
    schema (connector-certify's own introspection included) required a live
    local engine subprocess to be up first. PulseLink's tools only need a
    real secret when a source actually authenticates; listing tools never
    does.
    """

    def __init__(self) -> None:
        self._backend: SecretsBackend | None = None

    def _resolve(self) -> SecretsBackend:
        if self._backend is None:
            from agent_utilities.knowledge_graph.core.graph_compute import (
                GraphComputeEngine,
            )
            from agent_utilities.security.secrets_client import (
                InEpistemicGraphBackend,
            )

            engine = GraphComputeEngine.get_or_create(
                graph_name="__secrets__", backend_type="rust"
            )
            self._backend = InEpistemicGraphBackend(engine)
        return self._backend

    def get(self, key: str) -> str | None:
        return self._resolve().get(key)

    def set(self, key: str, value: str, **metadata: Any) -> None:
        self._resolve().set(key, value, **metadata)

    def delete(self, key: str) -> bool:
        return self._resolve().delete(key)

    def list_keys(self) -> list[str]:
        return self._resolve().list_keys()


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
    secrets_client: SecretsClient,
) -> tuple[Any, Any, Any]:
    """Build an executable surface from explicit encrypted-secret authority."""
    return _build_mcp(create_client(secrets_client))


def mcp_server():
    if any(argument in {"-h", "--help"} for argument in sys.argv[1:]):
        get_mcp_instance()
        return

    from agent_utilities.security.secrets_client import SecretsClient

    # Lazy: the local epistemic-graph engine only starts on the first real
    # secret lookup a tool call makes, not here -- so building the MCP
    # surface and answering `tools/list` never requires a live engine.
    secrets_client = SecretsClient(_LazyEpistemicGraphBackend())
    mcp, args, _ = get_runtime_mcp_instance(secrets_client=secrets_client)

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
