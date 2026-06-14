#!/usr/bin/python
"""PulseLink client accessor.

PulseLink has no single endpoint: it fans out across many source ladders and
authenticates per-source through the shared credential provider (OS-5.38). So
``get_client`` takes no URL/token — it returns a registry-backed facade that works
keyless out of the box; cookie/official backends light up when their credential
(``SOURCE_CREDENTIALS``) is present.
"""

from .api import PulseLinkClient

_client: PulseLinkClient | None = None


def get_client() -> PulseLinkClient:
    """Get or create the singleton PulseLink client facade."""
    global _client
    if _client is None:
        _client = PulseLinkClient()
    return _client
