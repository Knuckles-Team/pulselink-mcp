"""Keyless web-content backends: generic web (Jina Reader), RSS/Atom, news.

CONCEPT:PULSE-002 — Web & syndication sources
"""

from __future__ import annotations

import urllib.parse

from .base import PulseDocument, PulseResult, SourceBackend


class JinaWebBackend(SourceBackend):
    """Generic web reader via Jina Reader (``r.jina.ai`` / ``s.jina.ai``), keyless.

    ``fetch`` returns a page as clean markdown; ``search`` uses Jina's keyless
    web search which already returns reader-extracted results.
    """

    name = "jina"

    def fetch(self, url_or_id: str) -> PulseDocument:
        url = url_or_id
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        text = self.get_text(
            f"https://r.jina.ai/{url}", headers={"Accept": "text/plain"}, timeout=40
        )
        title = ""
        for line in text.splitlines():
            if line.startswith("Title:"):
                title = line[len("Title:") :].strip()
                break
        return PulseDocument(id=url, url=url, title=title, text=text)

    def search(self, query: str, cursor: str | None, limit: int) -> PulseResult:
        text = self.get_text(
            f"https://s.jina.ai/{urllib.parse.quote(query)}",
            headers={"Accept": "text/plain"},
            timeout=40,
        )
        # s.jina.ai returns concatenated reader blocks separated by a rule.
        docs: list[PulseDocument] = []
        for i, block in enumerate(text.split("\n---\n")):
            block = block.strip()
            if not block:
                continue
            url = ""
            title = ""
            for line in block.splitlines():
                if line.startswith("URL Source:"):
                    url = line.split(":", 1)[1].strip()
                elif line.startswith("Title:"):
                    title = line.split(":", 1)[1].strip()
            docs.append(
                PulseDocument(id=url or f"jina-{i}", url=url, title=title, text=block)
            )
            if len(docs) >= limit:
                break
        return PulseResult(documents=docs)


class RssBackend(SourceBackend):
    """RSS/Atom feeds via ``feedparser`` (keyless, lazy-imported)."""

    name = "rss"

    def _parse(self, feed_url: str, limit: int) -> list[PulseDocument]:
        import feedparser  # lazy — heavy optional dep

        parsed = feedparser.parse(feed_url, agent=self._auth()[0]["User-Agent"])
        docs: list[PulseDocument] = []
        for entry in parsed.entries[:limit]:
            docs.append(
                PulseDocument(
                    id=entry.get("id") or entry.get("link", ""),
                    url=entry.get("link", ""),
                    title=entry.get("title", ""),
                    text=entry.get("summary", "") or entry.get("description", ""),
                    author=entry.get("author", ""),
                    created_at=entry.get("published", "") or entry.get("updated", ""),
                )
            )
        return docs

    def list_items(self, channel: str, cursor: str | None, limit: int) -> PulseResult:
        # ``channel`` is the feed URL.
        return PulseResult(documents=self._parse(channel, limit))

    def fetch(self, url_or_id: str) -> PulseDocument:
        docs = self._parse(url_or_id, 1)
        if not docs:
            return PulseDocument(id=url_or_id, url=url_or_id)
        return docs[0]


class GoogleNewsBackend(SourceBackend):
    """News search via the keyless Google News RSS endpoint (through feedparser)."""

    name = "google-news"

    def search(self, query: str, cursor: str | None, limit: int) -> PulseResult:
        import feedparser

        q = urllib.parse.quote(query)
        feed_url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
        parsed = feedparser.parse(feed_url, agent=self._auth()[0]["User-Agent"])
        docs: list[PulseDocument] = []
        for entry in parsed.entries[:limit]:
            docs.append(
                PulseDocument(
                    id=entry.get("id") or entry.get("link", ""),
                    url=entry.get("link", ""),
                    title=entry.get("title", ""),
                    text=entry.get("summary", ""),
                    author=entry.get("source", {}).get("title", "")
                    if isinstance(entry.get("source"), dict)
                    else "",
                    created_at=entry.get("published", ""),
                )
            )
        return PulseResult(documents=docs)
