"""Per-source credentials for PulseLink, resolved through agent-connector-sdk.

``SOURCE_CREDENTIALS`` is a JSON object mapping a source name to a descriptor.
Descriptor secrets are references (``env://NAME`` or ``openbao://mount/path#field``)
resolved on each use through the SDK credential provider, scoped to this
connector. Nothing resolved here is retained, logged or echoed.

Descriptor types: ``api_key`` (``secret``, optional ``prefix``/``header``/
``param``), ``bearer`` (``secret``), ``cookie_session`` (``secret`` holds a
``name=value; name2=value2`` cookie string) and ``oauth2`` (client-credentials:
``token_url``, ``client_id``, ``client_secret_secret``).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import requests
from agent_connector_sdk.config import setting
from agent_connector_sdk.credentials.provider import CredentialProvider
from agent_connector_sdk.credentials.references import parse_secret_reference
from agent_connector_sdk.credentials.resolver import (
    CredentialResolver,
    CredentialUnavailableError,
)

CONNECTOR = "pulselink-mcp"
_TOKEN_TIMEOUT = 15


@dataclass(frozen=True)
class CredentialMaterial:
    """Headers, query parameters and cookies one credential contributes."""

    headers: Mapping[str, str] = field(default_factory=dict)
    params: Mapping[str, str] = field(default_factory=dict)
    cookies: Mapping[str, str] = field(default_factory=dict)

    def merged_into(
        self,
        headers: Mapping[str, str] | None,
        params: Mapping[str, str] | None,
        cookies: Mapping[str, str] | None,
    ) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
        """Return the three request mappings with this material applied."""
        return (
            {**(headers or {}), **self.headers},
            {**(params or {}), **self.params},
            {**(cookies or {}), **self.cookies},
        )


@dataclass(frozen=True)
class SourceCredential:
    """One configured source credential; secrets resolve at ``materialize``."""

    descriptor: Mapping[str, Any]
    provider: CredentialProvider

    def _secret(self, key: str) -> str:
        reference = self.descriptor.get(key)
        if not isinstance(reference, str):
            raise CredentialUnavailableError(f"credential field {key!r} is missing")
        return self.provider.get_secret(parse_secret_reference(reference))

    def materialize(self) -> CredentialMaterial:
        """Resolve the secret(s) into request material."""
        kind = self.descriptor.get("type")
        if kind == "api_key":
            value = f"{self.descriptor.get('prefix', '')}{self._secret('secret')}"
            if "param" in self.descriptor:
                return CredentialMaterial(params={self.descriptor["param"]: value})
            header = self.descriptor.get("header", "Authorization")
            return CredentialMaterial(headers={header: value})
        if kind == "bearer":
            return CredentialMaterial(
                headers={"Authorization": f"Bearer {self._secret('secret')}"}
            )
        if kind == "cookie_session":
            pairs = (
                part.strip().partition("=") for part in self._secret("secret").split(";")
            )
            return CredentialMaterial(
                cookies={name: value for name, _, value in pairs if name}
            )
        if kind == "oauth2":
            response = requests.post(
                str(self.descriptor["token_url"]),
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.descriptor.get("client_id", ""),
                    "client_secret": self._secret("client_secret_secret"),
                },
                timeout=_TOKEN_TIMEOUT,
            )
            response.raise_for_status()
            token = response.json().get("access_token")
            if not isinstance(token, str) or not token:
                raise CredentialUnavailableError("token endpoint returned no token")
            return CredentialMaterial(headers={"Authorization": f"Bearer {token}"})
        raise CredentialUnavailableError(f"unsupported credential type {kind!r}")


class SourceCredentials:
    """The ``SourceCredentialProvider`` over ``SOURCE_CREDENTIALS`` descriptors."""

    def __init__(
        self,
        resolver: CredentialResolver,
        descriptors: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> None:
        self._provider = CredentialProvider(resolver=resolver, connector=CONNECTOR)
        if descriptors is None:
            raw = setting("SOURCE_CREDENTIALS", "") or ""
            descriptors = json.loads(raw) if raw else {}
        self._descriptors = dict(descriptors)

    def available(self, source: str) -> bool:
        """Whether a credential descriptor is configured for ``source``."""
        return source in self._descriptors

    def get(self, source: str) -> SourceCredential:
        """The credential for ``source``; raises when none is configured."""
        if source not in self._descriptors:
            raise CredentialUnavailableError(f"no credential configured for {source!r}")
        return SourceCredential(self._descriptors[source], self._provider)
