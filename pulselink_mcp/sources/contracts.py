"""Stable source-ladder value types and credential boundary."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field


class CapabilityUnsupported(RuntimeError):
    """Raised when a backend does not implement a requested capability."""


class CredentialAuthorityUnavailable(RuntimeError):
    """Raised when source composition omitted credential authority."""


class CredentialProvider(Protocol):
    """Minimal injected credential authority consumed by source ladders."""

    def available(self, source: str) -> bool: ...

    def get(self, source: str) -> Any: ...


class UnavailableCredentialProvider:
    """Fail-closed authority used only to describe the MCP schema."""

    def available(self, source: str) -> bool:
        raise CredentialAuthorityUnavailable(
            f"credential authority is unavailable for source {source!r}"
        )

    def get(self, source: str) -> Any:
        raise CredentialAuthorityUnavailable(
            f"credential authority is unavailable for source {source!r}"
        )


class PulseDocument(BaseModel):
    """One normalized source item ready for KG ingestion."""

    id: str
    source: str = ""
    title: str = ""
    url: str = ""
    text: str = ""
    author: str = ""
    created_at: str = ""
    metrics: dict[str, Any] = Field(default_factory=dict)
    extra: dict[str, Any] = Field(default_factory=dict)


class PulseResult(BaseModel):
    """A page of documents plus an opaque cursor for the next page."""

    documents: list[PulseDocument] = Field(default_factory=list)
    next_cursor: str | None = None
    backend: str = ""


class BackendHealth(BaseModel):
    """The doctor verdict for one backend of one source."""

    backend: str
    ok: bool
    needs_auth: bool = False
    detail: str = ""
