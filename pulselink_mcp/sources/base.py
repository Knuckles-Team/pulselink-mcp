"""PulseLink source-backend ladder framework.

CONCEPT:PULSE-001 — Multi-backend source-fallback ladder + health doctor

A *source* (``youtube``, ``reddit``, ``x``, …) is served by an ordered list of
*backends*, each a distinct way to reach the same content: a keyless public
endpoint first, then a cookie-authenticated path, then an official paid API. The
ladder selects the **highest-fidelity backend that is eligible and healthy**:

  * A **keyless** backend (``requires_credential is None``) is always eligible.
  * An **auth** backend is eligible only when the
    :class:`~agent_utilities.security.credential_provider.CredentialProvider`
    reports a usable credential for its source key — so cookie/official backends
    light up only when their credential exists, and otherwise the ladder falls
    back to the keyless backend with zero configuration.

This ports Agent-Reach's per-channel fallback (its ``doctor.py``) into a durable,
server-side ladder, and unifies all outbound auth behind the shared credential
provider (OS-5.38/5.39) rather than ad-hoc per-source secret reads.
"""

from __future__ import annotations

import logging
from typing import Any

import requests
from pydantic import BaseModel, Field

logger = logging.getLogger("pulselink.sources")

# Sent on every outbound request so endpoints that sniff a default urllib/requests
# UA (and 403/412 it) see a normal browser string.
DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
DEFAULT_TIMEOUT = 20


class CapabilityUnsupported(RuntimeError):
    """Raised when a backend does not implement a requested capability."""


class PulseDocument(BaseModel):
    """One normalized item returned to the agent / KG ingestion pipeline.

    The field set is deliberately flat and stable so the agent-utilities
    ``mcp_tool`` connector presets (KG-2.59) can map it declaratively.
    """

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


class _KeylessMaterial:
    """Null auth material — contributes nothing (keyless / no provider)."""

    headers: dict[str, str] = {}
    params: dict[str, str] = {}
    cookies: dict[str, str] = {}

    @staticmethod
    def merged_into(
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
    ) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
        return dict(headers or {}), dict(params or {}), dict(cookies or {})


class _KeylessCredential:
    def materialize(self) -> _KeylessMaterial:
        return _KeylessMaterial()


class _NullProvider:
    """Fallback provider when the installed agent-utilities predates OS-5.38.

    Reports no credentials (so auth backends stay dark and the ladder uses its
    keyless backend) and applies nothing — keyless sources still work everywhere.
    """

    def available(self, source: str) -> bool:
        return False

    def get(self, source: str) -> _KeylessCredential:
        return _KeylessCredential()


_PROVIDER_OVERRIDE: Any = None


def set_credential_provider(provider: Any) -> None:
    """Inject a credential provider (tests / embedding). ``None`` restores default."""
    global _PROVIDER_OVERRIDE
    _PROVIDER_OVERRIDE = provider


def _provider() -> Any:
    """Return the shared credential provider.

    Prefers the unified agent-utilities provider (OS-5.38); falls back to a keyless
    null provider when that module is unavailable, so PulseLink runs standalone.
    """
    if _PROVIDER_OVERRIDE is not None:
        return _PROVIDER_OVERRIDE
    try:
        from agent_utilities.security.credential_provider import (
            get_credential_provider,
        )

        return get_credential_provider()
    except Exception:  # noqa: BLE001 — version skew / missing module → keyless mode
        return _NullProvider()


class SourceBackend:
    """One way to reach a source's content.

    Subclasses set :attr:`name` and (for auth backends) :attr:`requires_credential`
    — the provider source key whose credential must be present for this backend to
    be eligible. They implement whichever of ``search``/``fetch``/``list_items``/
    ``transcribe`` they support; the rest raise :class:`CapabilityUnsupported`.
    """

    name: str = "base"
    #: Provider source key required for eligibility, or ``None`` for keyless.
    requires_credential: str | None = None

    # -- eligibility / health ------------------------------------------------
    def is_eligible(self, provider: Any) -> bool:
        """Keyless backends are always eligible; auth backends need a credential."""
        if self.requires_credential is None:
            return True
        return provider.available(self.requires_credential)

    def health(self, provider: Any) -> BackendHealth:
        """Cheap reachability/credential probe (overridable)."""
        if self.requires_credential is not None and not provider.available(
            self.requires_credential
        ):
            return BackendHealth(
                backend=self.name,
                ok=False,
                needs_auth=True,
                detail=f"needs credential for '{self.requires_credential}'",
            )
        return BackendHealth(backend=self.name, ok=True, detail="ready")

    # -- shared HTTP with unified auth ---------------------------------------
    def _auth(
        self,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
    ) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
        """Merge this backend's credential material onto a request's pieces."""
        base_headers = {"User-Agent": DEFAULT_UA, **(headers or {})}
        if self.requires_credential is None:
            return base_headers, dict(params or {}), dict(cookies or {})
        material = _provider().get(self.requires_credential).materialize()
        return material.merged_into(base_headers, params, cookies)

    def get(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> requests.Response:
        """Authenticated GET applying this backend's credential material."""
        h, p, c = self._auth(headers, params)
        resp = requests.get(url, params=p, headers=h, cookies=c, timeout=timeout)
        resp.raise_for_status()
        return resp

    def get_json(self, url: str, **kw: Any) -> Any:
        return self.get(url, **kw).json()

    def get_text(self, url: str, **kw: Any) -> str:
        return self.get(url, **kw).text

    # -- capabilities (override the ones a backend supports) -----------------
    def search(self, query: str, cursor: str | None, limit: int) -> PulseResult:
        raise CapabilityUnsupported(f"{self.name} does not support search")

    def fetch(self, url_or_id: str) -> PulseDocument:
        raise CapabilityUnsupported(f"{self.name} does not support fetch")

    def list_items(self, channel: str, cursor: str | None, limit: int) -> PulseResult:
        raise CapabilityUnsupported(f"{self.name} does not support list")

    def transcribe(self, url_or_id: str) -> PulseDocument:
        raise CapabilityUnsupported(f"{self.name} does not support transcribe")


class SourceLadder:
    """An ordered set of backends for one source, with first-success fallback."""

    def __init__(self, source: str, backends: list[SourceBackend]) -> None:
        self.source = source
        self.backends = backends

    def _eligible(self, provider: Any) -> list[SourceBackend]:
        return [b for b in self.backends if b.is_eligible(provider)]

    def _run(self, capability: str, *args: Any) -> PulseResult | PulseDocument:
        provider = _provider()
        eligible = self._eligible(provider)
        if not eligible:
            raise CapabilityUnsupported(
                f"no eligible backend for source '{self.source}'"
            )
        errors: list[str] = []
        for backend in eligible:
            method = getattr(backend, capability)
            try:
                result = method(*args)
                _stamp(result, self.source, backend.name)
                return result
            except CapabilityUnsupported:
                continue
            except Exception as exc:  # noqa: BLE001 — try the next backend in the ladder
                errors.append(f"{backend.name}: {exc}")
                logger.warning(
                    "[%s] backend %s failed %s: %s",
                    self.source,
                    backend.name,
                    capability,
                    exc,
                )
                continue
        raise RuntimeError(
            f"all backends failed {capability} for '{self.source}': {'; '.join(errors)}"
        )

    def search(self, query: str, cursor: str | None, limit: int) -> PulseResult:
        return self._run("search", query, cursor, limit)  # type: ignore[return-value]

    def fetch(self, url_or_id: str) -> PulseDocument:
        return self._run("fetch", url_or_id)  # type: ignore[return-value]

    def list_items(self, channel: str, cursor: str | None, limit: int) -> PulseResult:
        return self._run("list_items", channel, cursor, limit)  # type: ignore[return-value]

    def transcribe(self, url_or_id: str) -> PulseDocument:
        return self._run("transcribe", url_or_id)  # type: ignore[return-value]

    def health(self) -> list[BackendHealth]:
        provider = _provider()
        return [b.health(provider) for b in self.backends]


def _stamp(result: PulseResult | PulseDocument, source: str, backend: str) -> None:
    """Stamp the winning backend + source onto the result for provenance."""
    if isinstance(result, PulseResult):
        result.backend = backend
        for doc in result.documents:
            doc.source = doc.source or source
    elif isinstance(result, PulseDocument):
        result.source = result.source or source
        result.extra.setdefault("backend", backend)
