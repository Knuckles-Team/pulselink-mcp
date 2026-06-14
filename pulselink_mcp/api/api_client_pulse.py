"""PulseLink client facade over the source-ladder registry.

CONCEPT:PULSE-001 — the single object the MCP server and agent use. Unlike a
classic single-endpoint API client, PulseLink fans out across many source ladders
and authenticates per-source through the shared credential provider, so there is no
base URL / token here — :func:`pulselink_mcp.auth.get_client` constructs it with no
configuration and every keyless source works immediately.
"""

from __future__ import annotations

from typing import Any

from ..sources import doctor, get_ladder, list_sources


class PulseLinkClient:
    """Thin facade delegating to the source registry."""

    def sources(self) -> list[str]:
        return list_sources()

    def search(
        self, source: str, query: str, cursor: str | None = None, limit: int = 10
    ) -> dict[str, Any]:
        return get_ladder(source).search(query, cursor, limit).model_dump()

    def fetch(self, source: str, target: str) -> dict[str, Any]:
        return get_ladder(source).fetch(target).model_dump()

    def list_items(
        self, source: str, channel: str, cursor: str | None = None, limit: int = 10
    ) -> dict[str, Any]:
        return get_ladder(source).list_items(channel, cursor, limit).model_dump()

    def transcribe(self, target: str, source: str = "youtube") -> dict[str, Any]:
        return get_ladder(source).transcribe(target).model_dump()

    def status(self) -> dict[str, list[dict[str, Any]]]:
        return {
            name: [h.model_dump() for h in backends]
            for name, backends in doctor().items()
        }
