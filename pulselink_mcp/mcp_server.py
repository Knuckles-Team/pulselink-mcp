#!/usr/bin/python
# coding: utf-8

import logging
import os
import sys
from typing import Any

from agent_utilities.base_utilities import to_boolean
from agent_utilities.mcp_utilities import create_mcp_server
from agent_utilities.utilities import get_logger
from dotenv import find_dotenv, load_dotenv

from .mcp import register_system_tools

__version__ = "0.1.0"

logger = get_logger(name="MCP_Server")
logger.setLevel(logging.INFO)


def get_mcp_instance() -> tuple[Any, Any, Any]:
    """Initialize and return the PulseLink MCP MCP instance, args, and middlewares."""
    load_dotenv(find_dotenv())

    args, mcp, middlewares = create_mcp_server(
        name="PulseLink MCP MCP",
        version=__version__,
        instructions="PulseLink MCP MCP Server — Condensed Action-Routed Tools.",
    )

    DEFAULT_SYSTEMTOOL = to_boolean(os.getenv("SYSTEMTOOL", "True"))
    if DEFAULT_SYSTEMTOOL:
        register_system_tools(mcp)

    for mw in middlewares:
        mcp.add_middleware(mw)

    return mcp, args, middlewares


def mcp_server():
    mcp, args, _ = get_mcp_instance()

    print(f"PulseLink MCP MCP v{__version__}", file=sys.stderr)
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
