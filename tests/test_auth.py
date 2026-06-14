import pulselink_mcp.auth as auth_module
from pulselink_mcp.api import PulseLinkClient
from pulselink_mcp.auth import get_client


def test_get_client_returns_pulselink_singleton():
    auth_module._client = None
    c1 = get_client()
    c2 = get_client()
    assert isinstance(c1, PulseLinkClient)
    assert c1 is c2  # singleton
    auth_module._client = None


def test_client_lists_all_sources():
    client = get_client()
    sources = client.sources()
    # 14-channel parity + the keyless globals.
    for expected in ("youtube", "reddit", "x", "hackernews", "web", "rss"):
        assert expected in sources
