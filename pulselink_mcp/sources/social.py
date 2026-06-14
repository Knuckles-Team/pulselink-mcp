"""Social backends: X/Twitter, LinkedIn.

CONCEPT:PULSE-006 — Social sources (auth-laddered; keyless paths are gone)

X and LinkedIn no longer permit anonymous access, so these backends are
credential-gated through the shared provider: an official-API backend when a key
is present, a cookie-session backend when browser cookies are held, and (for
LinkedIn) a keyless best-effort read of public pages via the Jina reader.
"""

from __future__ import annotations

from .base import PulseDocument, PulseResult, SourceBackend
from .web import JinaWebBackend


class XApiBackend(SourceBackend):
    """X/Twitter via the official API v2 (recent search) — credential-gated."""

    name = "x-api"
    requires_credential = "x"
    _API = "https://api.twitter.com/2"

    def search(self, query: str, cursor: str | None, limit: int) -> PulseResult:
        params = {
            "query": query,
            "max_results": str(max(10, min(limit, 100))),
            "tweet.fields": "created_at,author_id,public_metrics",
        }
        if cursor:
            params["next_token"] = cursor
        data = self.get_json(f"{self._API}/tweets/search/recent", params=params)
        docs = [
            PulseDocument(
                id=t.get("id", ""),
                url=f"https://x.com/i/web/status/{t.get('id')}",
                text=t.get("text", ""),
                author=t.get("author_id", ""),
                created_at=t.get("created_at", ""),
                metrics=t.get("public_metrics", {}),
            )
            for t in data.get("data", [])
        ]
        return PulseResult(
            documents=docs, next_cursor=data.get("meta", {}).get("next_token")
        )

    def fetch(self, url_or_id: str) -> PulseDocument:
        tweet_id = url_or_id.rstrip("/").split("/")[-1].split("?")[0]
        data = self.get_json(
            f"{self._API}/tweets/{tweet_id}",
            params={"tweet.fields": "created_at,author_id,public_metrics"},
        )
        t = data.get("data", {})
        return PulseDocument(
            id=t.get("id", tweet_id),
            url=f"https://x.com/i/web/status/{tweet_id}",
            text=t.get("text", ""),
            author=t.get("author_id", ""),
            created_at=t.get("created_at", ""),
            metrics=t.get("public_metrics", {}),
        )


class XCookieBackend(SourceBackend):
    """X/Twitter via authenticated session cookies (``auth_token``/``ct0``).

    Uses the public GraphQL search surface the web client uses, with the cookie
    credential the provider supplies. Best-effort: X actively changes these
    endpoints, so this sits *below* the official-API backend in the ladder.
    """

    name = "x-cookie"
    requires_credential = "x"
    # The web client's bearer is a public constant shipped in its JS bundle.
    _GUEST_BEARER = (
        "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D"
        "1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
    )

    def search(self, query: str, cursor: str | None, limit: int) -> PulseResult:
        material = self._provider_material()
        ct0 = material.cookies.get("ct0", "")
        headers = {
            "Authorization": self._GUEST_BEARER,
            "x-csrf-token": ct0,
            "Content-Type": "application/json",
        }
        # SearchTimeline GraphQL endpoint (variables kept minimal/best-effort).
        import json

        variables = {"rawQuery": query, "count": limit, "product": "Latest"}
        url = "https://x.com/i/api/graphql/search/SearchTimeline"
        resp = self.get(
            url,
            params={"variables": json.dumps(variables)},
            headers=headers,
        )
        return _parse_x_graphql(resp.json())

    def _provider_material(self):
        from .base import _provider

        return _provider().get(self.requires_credential).materialize()


def _parse_x_graphql(payload: dict) -> PulseResult:
    """Best-effort flatten of an X SearchTimeline GraphQL response to documents."""
    docs: list[PulseDocument] = []
    try:
        instructions = payload["data"]["search_by_raw_query"]["search_timeline"][
            "timeline"
        ]["instructions"]
    except (KeyError, TypeError):
        return PulseResult(documents=docs)
    for inst in instructions:
        for entry in inst.get("entries", []) or []:
            result = (
                entry.get("content", {})
                .get("itemContent", {})
                .get("tweet_results", {})
                .get("result", {})
            )
            legacy = result.get("legacy") or {}
            if not legacy:
                continue
            docs.append(
                PulseDocument(
                    id=legacy.get("id_str", ""),
                    url=f"https://x.com/i/web/status/{legacy.get('id_str', '')}",
                    text=legacy.get("full_text", ""),
                    created_at=legacy.get("created_at", ""),
                    metrics={
                        "likes": legacy.get("favorite_count", 0),
                        "retweets": legacy.get("retweet_count", 0),
                    },
                )
            )
    return PulseResult(documents=docs)


class LinkedInJinaBackend(JinaWebBackend):
    """LinkedIn public pages via the keyless Jina reader (best-effort fetch)."""

    name = "linkedin-jina"


class LinkedInCookieBackend(SourceBackend):
    """LinkedIn via session cookies — credential-gated fetch of authed pages."""

    name = "linkedin-cookie"
    requires_credential = "linkedin"

    def fetch(self, url_or_id: str) -> PulseDocument:
        text = self.get_text(url_or_id, timeout=30)
        return PulseDocument(id=url_or_id, url=url_or_id, text=text)
