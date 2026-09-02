from unittest.mock import Mock

import pytest
from agent_utilities.security.secrets_client import SecretsClient

from pulselink_mcp.api import PulseLinkClient
from pulselink_mcp.auth import create_client


def test_create_client_uses_injected_secret_authority():
    client = create_client(Mock(spec=SecretsClient))
    assert isinstance(client, PulseLinkClient)


def test_create_client_fails_closed_without_secret_authority():
    with pytest.raises(RuntimeError, match="injected secret"):
        create_client(None)


def test_client_lists_all_sources():
    client = create_client(Mock(spec=SecretsClient))
    sources = client.sources()
    # 14-channel parity + the keyless globals.
    for expected in ("youtube", "reddit", "x", "hackernews", "web", "rss"):
        assert expected in sources
