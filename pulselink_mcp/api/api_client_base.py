from typing import Any

import requests
from agent_utilities.core.transport_security import (
    ResolvedTLSProfile,
    resolve_configured_tls_profile,
)


class ApiClientBase:
    """Base HTTP API client wrapper."""

    def __init__(
        self,
        base_url: str,
        token: str,
        tls_profile: ResolvedTLSProfile | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.tls_profile = tls_profile or resolve_configured_tls_profile("pulselink")
        self.session = self.tls_profile.configure_requests_session(requests.Session())
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return {"status": response.status_code, "text": response.text}

    def close(self) -> None:
        """Release transport resources and runtime-only TLS material."""
        self.session.close()
        self.tls_profile.cleanup()
