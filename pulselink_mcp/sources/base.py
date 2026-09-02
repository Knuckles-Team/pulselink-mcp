"""PulseLink source-backend ladder framework.

CONCEPT:PK-OS.governance.search-fetch-list-transcribe — Multi-backend source-fallback ladder + health doctor

A *source* (``youtube``, ``reddit``, ``x``, …) is served by an ordered list of
*backends*, each a distinct way to reach the same content: a keyless public
endpoint first, then a cookie-authenticated path, then an official paid API. The
ladder selects the **highest-fidelity backend that is eligible and healthy**:

  * A **keyless** backend (``requires_credential is None``) is always eligible.
  * An **auth** backend is eligible only when the
    injected credential authority reports a usable credential for its source key
    — so cookie/official backends
    light up only when their credential exists, and otherwise the ladder falls
    back to the keyless backend with zero configuration.

This ports Agent-Reach's per-channel fallback (its ``doctor.py``) into a durable,
server-side ladder, and unifies all outbound auth behind the shared credential
provider (OS-5.38/5.39) rather than ad-hoc per-source secret reads.
"""

from __future__ import annotations

import logging
from typing import Any

from .contracts import (
    BackendHealth,
    CapabilityUnsupported,
    CredentialAuthority,
    CredentialAuthorityUnavailable,
    PulseDocument,
    PulseResult,
)
from .http_transport import AuthenticatedHttpTransport

logger = logging.getLogger("pulselink.sources")


class SourceBackend(AuthenticatedHttpTransport):
    """One way to reach a source's content.

    Subclasses set :attr:`name` and (for auth backends) :attr:`requires_credential`
    — the provider source key whose credential must be present for this backend to
    be eligible. They implement whichever of ``search``/``fetch``/``list_items``/
    ``transcribe`` they support; the rest raise :class:`CapabilityUnsupported`.
    """

    name: str = "base"
    #: Provider source key required for eligibility, or ``None`` for keyless.
    requires_credential: str | None = None

    def __init__(self, credential_authority: CredentialAuthority) -> None:
        if credential_authority is None:
            raise CredentialAuthorityUnavailable(
                "source backend requires injected credential authority"
            )
        super().__init__(credential_authority, self.requires_credential)

    # -- eligibility / health ------------------------------------------------
    def is_eligible(self) -> bool:
        """Keyless backends are always eligible; auth backends need a credential."""
        if self.requires_credential is None:
            return True
        return self._credential_authority.available(self.requires_credential)

    def health(self) -> BackendHealth:
        """Cheap reachability/credential probe (overridable)."""
        if (
            self.requires_credential is not None
            and not self._credential_authority.available(self.requires_credential)
        ):
            return BackendHealth(
                backend=self.name,
                ok=False,
                needs_auth=True,
                detail=f"needs credential for '{self.requires_credential}'",
            )
        return BackendHealth(backend=self.name, ok=True, detail="ready")

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

    def __init__(
        self,
        source: str,
        backends: list[SourceBackend],
    ) -> None:
        if not backends:
            raise CredentialAuthorityUnavailable(
                "source ladder requires an authority-bound backend"
            )
        authority = backends[0]._credential_authority
        if any(backend._credential_authority is not authority for backend in backends):
            raise CredentialAuthorityUnavailable(
                "source ladder backends must share one credential authority"
            )
        self.source = source
        self.backends = backends
        self._credential_authority = authority

    def _eligible(self) -> list[SourceBackend]:
        return [backend for backend in self.backends if backend.is_eligible()]

    def _run(self, capability: str, *args: Any) -> PulseResult | PulseDocument:
        eligible = self._eligible()
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
                errors.append(f"{backend.name}: {type(exc).__name__}")
                logger.warning(
                    "[%s] backend %s failed %s (error_type=%s)",
                    self.source,
                    backend.name,
                    capability,
                    type(exc).__name__,
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
        return [backend.health() for backend in self.backends]


def _stamp(result: PulseResult | PulseDocument, source: str, backend: str) -> None:
    """Stamp the winning backend + source onto the result for provenance."""
    if isinstance(result, PulseResult):
        result.backend = backend
        for doc in result.documents:
            doc.source = doc.source or source
    elif isinstance(result, PulseDocument):
        result.source = result.source or source
        result.extra.setdefault("backend", backend)
