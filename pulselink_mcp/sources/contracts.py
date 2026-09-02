"""Stable source-ladder value types and credential boundary."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field


class CapabilityUnsupported(RuntimeError):
    """Raised when a backend does not implement a requested capability."""


class CredentialAuthorityUnavailable(RuntimeError):
    """Raised when source composition omitted credential authority."""


class SourceCredentialProvider(Protocol):
    """Typed source-credential provider wrapped by the runtime authority."""

    def available(self, source: str) -> bool: ...

    def get(self, source: str) -> Any: ...


class CredentialAuthority(SourceCredentialProvider, Protocol):
    """Single capability governing readiness, eligibility, and materialization."""

    def require_runtime_authority(self) -> None:
        raise CredentialAuthorityUnavailable(
            "Credential authority protocol has no runtime implementation"
        )


class RuntimeCredentialAuthority:
    """Runtime capability over one explicitly composed credential provider."""

    def __init__(self, provider: SourceCredentialProvider) -> None:
        self._provider = provider

    def require_runtime_authority(self) -> None:
        """Confirm this object was composed for executable runtime use."""
        if self._provider is None:
            raise CredentialAuthorityUnavailable(
                "PulseLink runtime credential authority is unavailable"
            )

    def available(self, source: str) -> bool:
        return self._provider.available(source)

    def get(self, source: str) -> Any:
        return self._provider.get(source)


class UnavailableCredentialAuthority:
    """Fail-closed authority used only to describe the MCP schema."""

    def require_runtime_authority(self) -> None:
        raise CredentialAuthorityUnavailable(
            "PulseLink runtime credential authority is unavailable"
        )

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
