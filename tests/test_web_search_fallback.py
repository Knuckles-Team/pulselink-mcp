"""The web source falls back to a keyless search when the Jina search needs a key."""

from __future__ import annotations

import requests
from scion_sdk.credentials.provider import NoCredential

from pulselink_mcp.sources import build_registry
from pulselink_mcp.sources.web import BingRssWebBackend, JinaWebBackend

RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>One</title><link>https://example.org/1</link><description>First</description></item>
<item><title>Two</title><link>https://example.org/2</link><description>Second</description></item>
</channel></rss>"""


class _Authority:
    def require_runtime_authority(self) -> None:
        return None

    def available(self, source: str) -> bool:
        return False

    def get(self, source: str) -> NoCredential:
        return NoCredential()


def _unauthorized(self, *args, **kwargs):
    response = requests.Response()
    response.status_code = 401
    raise requests.HTTPError("401", response=response)


def test_web_search_falls_back_to_bing_rss_when_jina_search_is_unauthorized(
    monkeypatch,
):
    monkeypatch.setattr(JinaWebBackend, "get_text", _unauthorized)
    monkeypatch.setattr(BingRssWebBackend, "get_text", lambda self, *a, **k: RSS)
    result = build_registry(_Authority())["web"].search("llm", None, 5)
    assert result.backend == "bing-rss"
    assert [d.url for d in result.documents] == [
        "https://example.org/1",
        "https://example.org/2",
    ]
    assert all(d.source == "web" for d in result.documents)


def test_web_fetch_still_uses_the_jina_reader(monkeypatch):
    monkeypatch.setattr(
        JinaWebBackend, "get_text", lambda self, *a, **k: "Title: Page\nbody"
    )
    doc = build_registry(_Authority())["web"].fetch("example.org")
    assert doc.title == "Page"
    assert doc.extra["backend"] == "jina"
