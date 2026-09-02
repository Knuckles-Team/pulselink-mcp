"""Authenticated HTTP mechanics shared by PulseLink source backends."""

from __future__ import annotations

import atexit
from typing import Any

import requests
from agent_utilities.core.transport_security import (
    ResolvedTLSProfile,
    resolve_configured_tls_profile,
)

from .contracts import CredentialProvider

DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
DEFAULT_TIMEOUT = 20

_HTTP_SESSION: requests.Session | None = None
_TLS_PROFILE: ResolvedTLSProfile | None = None


def configured_session() -> requests.Session:
    """Return the process-wide Requests session under the configured TLS policy."""
    global _HTTP_SESSION, _TLS_PROFILE
    if _HTTP_SESSION is None:
        _TLS_PROFILE = resolve_configured_tls_profile("pulselink")
        _HTTP_SESSION = _TLS_PROFILE.configure_requests_session(requests.Session())
    return _HTTP_SESSION


def close_configured_session() -> None:
    """Release the shared session and runtime-only TLS material."""
    global _HTTP_SESSION, _TLS_PROFILE
    if _HTTP_SESSION is not None:
        _HTTP_SESSION.close()
    if _TLS_PROFILE is not None:
        _TLS_PROFILE.cleanup()
    _HTTP_SESSION = None
    _TLS_PROFILE = None


atexit.register(close_configured_session)


class AuthenticatedHttpTransport:
    """Apply one injected source credential to bounded HTTP GET requests."""

    def __init__(
        self,
        credential_provider: CredentialProvider,
        credential_key: str | None,
    ) -> None:
        self._credential_provider = credential_provider
        self._credential_key = credential_key

    def _auth(
        self,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
    ) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
        base_headers = {"User-Agent": DEFAULT_UA, **(headers or {})}
        if self._credential_key is None:
            return base_headers, dict(params or {}), dict(cookies or {})
        material = self._credential_provider.get(self._credential_key).materialize()
        return material.merged_into(base_headers, params, cookies)

    def get(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> requests.Response:
        """GET with the backend's credential and configured TLS policy."""
        request_headers, request_params, request_cookies = self._auth(headers, params)
        response = configured_session().get(
            url,
            params=request_params,
            headers=request_headers,
            cookies=request_cookies,
            timeout=timeout,
        )
        response.raise_for_status()
        return response

    def get_json(self, url: str, **kwargs: Any) -> Any:
        """GET and decode one JSON response."""
        return self.get(url, **kwargs).json()

    def get_text(self, url: str, **kwargs: Any) -> str:
        """GET and return one text response."""
        return self.get(url, **kwargs).text
