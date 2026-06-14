"""Community/forum backends: Hacker News, Reddit, V2EX.

CONCEPT:PULSE-003 — Community & discussion sources
"""

from __future__ import annotations

from .base import PulseDocument, PulseResult, SourceBackend


class HackerNewsBackend(SourceBackend):
    """Hacker News via the keyless Algolia HN API (search + item fetch)."""

    name = "hn-algolia"
    _SEARCH = "https://hn.algolia.com/api/v1/search"
    _ITEM = "https://hn.algolia.com/api/v1/items/"

    def search(self, query: str, cursor: str | None, limit: int) -> PulseResult:
        page = int(cursor) if cursor else 0
        data = self.get_json(
            self._SEARCH,
            params={"query": query, "page": str(page), "hitsPerPage": str(limit)},
        )
        docs = [
            PulseDocument(
                id=str(h.get("objectID", "")),
                url=h.get("url")
                or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                title=h.get("title") or h.get("story_title") or "",
                text=h.get("comment_text") or h.get("story_text") or "",
                author=h.get("author", ""),
                created_at=h.get("created_at", ""),
                metrics={
                    "points": h.get("points") or 0,
                    "comments": h.get("num_comments") or 0,
                },
            )
            for h in data.get("hits", [])
        ]
        nb_pages = data.get("nbPages", 0)
        next_cursor = str(page + 1) if page + 1 < nb_pages else None
        return PulseResult(documents=docs, next_cursor=next_cursor)

    def fetch(self, url_or_id: str) -> PulseDocument:
        item_id = url_or_id.rstrip("/").split("=")[-1].split("/")[-1]
        data = self.get_json(f"{self._ITEM}{item_id}")
        return PulseDocument(
            id=str(data.get("id", item_id)),
            url=f"https://news.ycombinator.com/item?id={data.get('id', item_id)}",
            title=data.get("title", ""),
            text=data.get("text", "") or _flatten_hn_children(data),
            author=data.get("author", ""),
            created_at=data.get("created_at", ""),
            metrics={"points": data.get("points") or 0},
        )


def _flatten_hn_children(node: dict, depth: int = 0) -> str:
    """Flatten an HN item's comment tree into readable indented text."""
    parts: list[str] = []
    for child in node.get("children", []) or []:
        text = (child.get("text") or "").strip()
        if text:
            parts.append("  " * depth + f"{child.get('author', '?')}: {text}")
        parts.append(_flatten_hn_children(child, depth + 1))
    return "\n".join(p for p in parts if p)


class RedditPublicBackend(SourceBackend):
    """Reddit via the keyless ``.json`` endpoints (may 403 under heavy anti-bot)."""

    name = "reddit-public"

    def search(self, query: str, cursor: str | None, limit: int) -> PulseResult:
        data = self.get_json(
            "https://www.reddit.com/search.json",
            params={"q": query, "limit": str(limit), "after": cursor or ""},
        )
        return _reddit_listing(data)

    def list_items(self, channel: str, cursor: str | None, limit: int) -> PulseResult:
        sub = channel.lstrip("r/").strip("/")
        data = self.get_json(
            f"https://www.reddit.com/r/{sub}/hot.json",
            params={"limit": str(limit), "after": cursor or ""},
        )
        return _reddit_listing(data)

    def fetch(self, url_or_id: str) -> PulseDocument:
        url = url_or_id.split("?")[0].rstrip("/")
        data = self.get_json(f"{url}.json")
        post = data[0]["data"]["children"][0]["data"] if isinstance(data, list) else {}
        return PulseDocument(
            id=post.get("id", url),
            url="https://www.reddit.com" + post.get("permalink", ""),
            title=post.get("title", ""),
            text=post.get("selftext", ""),
            author=post.get("author", ""),
            created_at=str(post.get("created_utc", "")),
            metrics={
                "score": post.get("score", 0),
                "comments": post.get("num_comments", 0),
            },
        )


class RedditOAuthBackend(RedditPublicBackend):
    """Reddit via the official OAuth API — eligible only when a credential exists.

    Reuses the public ``.json`` parsing but targets ``oauth.reddit.com`` with the
    bearer token the credential provider supplies.
    """

    name = "reddit-oauth"
    requires_credential = "reddit"

    def search(self, query: str, cursor: str | None, limit: int) -> PulseResult:
        data = self.get_json(
            "https://oauth.reddit.com/search",
            params={
                "q": query,
                "limit": str(limit),
                "after": cursor or "",
                "raw_json": "1",
            },
        )
        return _reddit_listing(data)


def _reddit_listing(data: dict) -> PulseResult:
    children = data.get("data", {}).get("children", [])
    docs: list[PulseDocument] = []
    for child in children:
        d = child.get("data", {})
        docs.append(
            PulseDocument(
                id=d.get("id", ""),
                url="https://www.reddit.com" + d.get("permalink", ""),
                title=d.get("title", ""),
                text=d.get("selftext", "") or d.get("body", ""),
                author=d.get("author", ""),
                created_at=str(d.get("created_utc", "")),
                metrics={
                    "score": d.get("score", 0),
                    "comments": d.get("num_comments", 0),
                },
                extra={"subreddit": d.get("subreddit", "")},
            )
        )
    after = data.get("data", {}).get("after")
    return PulseResult(documents=docs, next_cursor=after)


class V2exBackend(SourceBackend):
    """V2EX via its keyless public JSON API (hot topics + topic detail)."""

    name = "v2ex"

    def list_items(self, channel: str, cursor: str | None, limit: int) -> PulseResult:
        if channel and channel != "hot":
            url = "https://www.v2ex.com/api/topics/show.json"
            topics = self.get_json(url, params={"node_name": channel})
        else:
            topics = self.get_json("https://www.v2ex.com/api/topics/hot.json")
        docs = [
            PulseDocument(
                id=str(t.get("id", "")),
                url=t.get("url", ""),
                title=t.get("title", ""),
                text=t.get("content", ""),
                author=(t.get("member") or {}).get("username", ""),
                created_at=str(t.get("created", "")),
                metrics={"replies": t.get("replies", 0)},
                extra={"node": (t.get("node") or {}).get("name", "")},
            )
            for t in (topics or [])[:limit]
        ]
        return PulseResult(documents=docs)

    def fetch(self, url_or_id: str) -> PulseDocument:
        topic_id = url_or_id.rstrip("/").split("/")[-1]
        topics = self.get_json(
            "https://www.v2ex.com/api/topics/show.json", params={"id": topic_id}
        )
        t = topics[0] if topics else {}
        return PulseDocument(
            id=str(t.get("id", topic_id)),
            url=t.get("url", ""),
            title=t.get("title", ""),
            text=t.get("content", ""),
            author=(t.get("member") or {}).get("username", ""),
            created_at=str(t.get("created", "")),
            metrics={"replies": t.get("replies", 0)},
        )


__all__ = [
    "HackerNewsBackend",
    "RedditPublicBackend",
    "RedditOAuthBackend",
    "V2exBackend",
    "_reddit_listing",
]
