#!/usr/bin/python
"""PulseLink client composition.

PulseLink has no single endpoint: it fans out across many source ladders and
authenticates per-source through the shared credential provider (OS-5.38). So
The composition root injects the encrypted secret client used to construct the
typed credential provider. No process-global provider or secret-store discovery
is available here.
"""

from agent_utilities.security.credential_provider import CredentialProvider
from agent_utilities.security.secrets_client import SecretsClient

from .api import PulseLinkClient


def create_client(secrets_client: SecretsClient | None) -> PulseLinkClient:
    """Build a client from explicitly supplied encrypted-secret authority."""
    if secrets_client is None:
        raise RuntimeError("PulseLink requires an injected secret client")
    return PulseLinkClient(CredentialProvider(secrets=secrets_client))
