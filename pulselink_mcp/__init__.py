#!/usr/bin/env python

import importlib
import inspect

__all__: list[str] = []

CORE_MODULES = [
    "pulselink_mcp.api",
]

OPTIONAL_MODULES = {
    "pulselink_mcp.mcp_server": "mcp",
}


def _import_module_safely(module_name: str):
    """Try to import a module and return it, or None if not available."""
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


def _expose_members(module):
    """Expose public classes and functions from a module into globals and __all__."""
    for name, obj in inspect.getmembers(module):
        if (inspect.isclass(obj) or inspect.isfunction(obj)) and not name.startswith(
            "_"
        ):
            globals()[name] = obj
            __all__.append(name)


for module_name in CORE_MODULES:
    try:
        module = importlib.import_module(module_name)
        _expose_members(module)
    except ImportError:
        pass

for module_name, extra_name in OPTIONAL_MODULES.items():
    module = _import_module_safely(module_name)
    if module is not None:
        _expose_members(module)
        globals()[f"_{extra_name.upper()}_AVAILABLE"] = True
    else:
        globals()[f"_{extra_name.upper()}_AVAILABLE"] = False

__all__.extend(["_MCP_AVAILABLE", "_AGENT_AVAILABLE"])


from scion_sdk.connector import Connector
from scion_sdk.connector_hooks import RegistrationContext


def _register_introspection_surface(context: RegistrationContext) -> None:
    from pulselink_mcp.api import PulseLinkClient
    from pulselink_mcp.mcp_server import register_server_surface
    from pulselink_mcp.sources.contracts import UnavailableCredentialAuthority

    register_server_surface(
        context.server, PulseLinkClient(UnavailableCredentialAuthority())
    )


connector = Connector(
    instructions=(
        "PulseLink — keyless open-web & social research reach. Search, fetch, "
        "list, and transcribe across YouTube, Reddit, X, Hacker News, the web, "
        "RSS/news, GitHub and more; pulse_status reports per-source health."
    ),
    extra_registrations=(_register_introspection_surface,),
)
