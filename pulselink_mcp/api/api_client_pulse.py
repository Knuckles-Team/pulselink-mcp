"""PulseLink client facade over the source-ladder registry.

CONCEPT:PK-OS.governance.search-fetch-list-transcribe — the single object the MCP server and agent use. Unlike a
classic single-endpoint API client, PulseLink fans out across many source ladders
and authenticates per-source through the shared credential provider, so there is no
base URL or token here; the composition root supplies its credential authority.
"""

from __future__ import annotations

from typing import Any

from ..sources import build_registry
from ..sources.base import (
    CredentialAuthorityUnavailable,
    CredentialProvider,
    SourceLadder,
)


class PulseLinkClient:
    """Thin facade delegating to the source registry."""

    def __init__(
        self,
        credential_provider: CredentialProvider,
        *,
        runtime_authority: bool = True,
    ) -> None:
        self._sources = build_registry(credential_provider)
        self._runtime_authority = runtime_authority

    def _require_runtime_authority(self) -> None:
        if not self._runtime_authority:
            raise CredentialAuthorityUnavailable(
                "PulseLink runtime credential authority is unavailable"
            )

    def _ladder(self, source: str) -> SourceLadder:
        self._require_runtime_authority()
        ladder = self._sources.get(source)
        if ladder is None:
            raise KeyError(
                f"unknown source {source!r}. Available: "
                f"{', '.join(sorted(self._sources))}"
            )
        return ladder

    def sources(self) -> list[str]:
        return sorted(self._sources)

    def search(
        self, source: str, query: str, cursor: str | None = None, limit: int = 10
    ) -> dict[str, Any]:
        return self._ladder(source).search(query, cursor, limit).model_dump()

    def fetch(self, source: str, target: str) -> dict[str, Any]:
        return self._ladder(source).fetch(target).model_dump()

    def list_items(
        self, source: str, channel: str, cursor: str | None = None, limit: int = 10
    ) -> dict[str, Any]:
        return self._ladder(source).list_items(channel, cursor, limit).model_dump()

    def transcribe(self, target: str, source: str = "youtube") -> dict[str, Any]:
        return self._ladder(source).transcribe(target).model_dump()

    def status(self) -> dict[str, list[dict[str, Any]]]:
        self._require_runtime_authority()
        return {
            name: [h.model_dump() for h in backends]
            for name, backends in (
                (name, ladder.health()) for name, ladder in self._sources.items()
            )
        }
