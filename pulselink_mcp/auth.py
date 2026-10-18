#!/usr/bin/python
"""PulseLink client composition.

PulseLink has no single endpoint: it fans out across many source ladders and
authenticates per source through the SDK credential resolver. The composition
root injects the resolver; no process-global provider or secret-store discovery
is available here.
"""

from agent_connector_sdk.credentials.resolver import CredentialResolver

from .api import PulseLinkClient
from .credentials import SourceCredentials
from .sources.contracts import RuntimeCredentialAuthority


def create_client(credential_resolver: CredentialResolver | None) -> PulseLinkClient:
    """Build a client from an explicitly supplied credential resolver."""
    if credential_resolver is None:
        raise RuntimeError("PulseLink requires an injected credential resolver")
    return PulseLinkClient(
        RuntimeCredentialAuthority(SourceCredentials(credential_resolver))
    )
