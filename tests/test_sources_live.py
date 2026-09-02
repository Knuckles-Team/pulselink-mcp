"""Live-network checks for PulseLink keyless backends (CONCEPT:PULSE-*).

Marked ``live`` and skipped by default (``-m "not live"``). Run with
``pytest -m live`` against the open internet. These exercise only the **keyless**
sources (no credentials), asserting real, normalized results with a working cursor.
Auth-walled sources (x/reddit-oauth/linkedin/exa/xiaohongshu/xueqiu) are validated
in the unit suite with injected credentials, not here.
"""

from __future__ import annotations

import pytest
from agent_utilities.security.source_credentials import NoCredential

from pulselink_mcp.sources import build_registry

pytestmark = pytest.mark.live


class KeylessCredentialProvider:
    def available(self, source: str) -> bool:
        return False

    def get(self, source: str) -> NoCredential:
        return NoCredential()


SOURCES = build_registry(KeylessCredentialProvider())


def test_hackernews_live_search():
    result = SOURCES["hackernews"].search("python", cursor=None, limit=5)
    assert result.documents
    assert all(d.id for d in result.documents)
    assert result.documents[0].title or result.documents[0].text


def test_web_live_fetch_via_jina():
    doc = SOURCES["web"].fetch("https://example.com")
    assert "example" in doc.text.lower()


def test_v2ex_live_hot():
    result = SOURCES["v2ex"].list_items("hot", None, 5)
    assert result.documents
    assert result.documents[0].url


def test_github_public_live_search():
    result = SOURCES["github"].search("knowledge graph", None, 3)
    assert result.documents
    assert result.documents[0].metrics.get("stars") is not None


@pytest.mark.skipif(
    pytest.importorskip("feedparser", reason="needs feeds extra") is None,
    reason="feedparser not installed",
)
def test_news_live_search():
    result = SOURCES["news"].search("artificial intelligence", None, 5)
    assert result.documents


@pytest.mark.skipif(
    pytest.importorskip("yt_dlp", reason="needs youtube extra") is None,
    reason="yt-dlp not installed",
)
def test_youtube_live_search():
    result = SOURCES["youtube"].search("transformer architecture", None, 3)
    assert result.documents
    assert all("youtube.com" in d.url or d.id for d in result.documents)
