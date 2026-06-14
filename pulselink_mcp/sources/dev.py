"""Developer-source backends: GitHub, Exa semantic search.

CONCEPT:PULSE-004 — Developer & semantic-search sources
"""

from __future__ import annotations

from .base import PulseDocument, PulseResult, SourceBackend


class GitHubPublicBackend(SourceBackend):
    """GitHub repo/code search via the public REST API (keyless, low rate limit)."""

    name = "github-public"
    _API = "https://api.github.com"

    def search(self, query: str, cursor: str | None, limit: int) -> PulseResult:
        page = int(cursor) if cursor else 1
        data = self.get_json(
            f"{self._API}/search/repositories",
            params={
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": str(limit),
                "page": str(page),
            },
            headers={"Accept": "application/vnd.github+json"},
        )
        docs = [
            PulseDocument(
                id=str(r.get("id", "")),
                url=r.get("html_url", ""),
                title=r.get("full_name", ""),
                text=r.get("description") or "",
                author=(r.get("owner") or {}).get("login", ""),
                created_at=r.get("created_at", ""),
                metrics={
                    "stars": r.get("stargazers_count", 0),
                    "forks": r.get("forks", 0),
                },
                extra={"language": r.get("language", "")},
            )
            for r in data.get("items", [])
        ]
        next_cursor = str(page + 1) if len(docs) >= limit else None
        return PulseResult(documents=docs, next_cursor=next_cursor)

    def fetch(self, url_or_id: str) -> PulseDocument:
        # Accept either "owner/repo" or a full GitHub URL.
        slug = url_or_id.replace("https://github.com/", "").strip("/")
        owner_repo = "/".join(slug.split("/")[:2])
        r = self.get_json(
            f"{self._API}/repos/{owner_repo}",
            headers={"Accept": "application/vnd.github+json"},
        )
        return PulseDocument(
            id=str(r.get("id", owner_repo)),
            url=r.get("html_url", ""),
            title=r.get("full_name", owner_repo),
            text=r.get("description") or "",
            author=(r.get("owner") or {}).get("login", ""),
            created_at=r.get("created_at", ""),
            metrics={"stars": r.get("stargazers_count", 0)},
        )


class GitHubTokenBackend(GitHubPublicBackend):
    """GitHub with an authenticated token — higher rate limits + private repos."""

    name = "github-token"
    requires_credential = "github"


class ExaBackend(SourceBackend):
    """Exa AI semantic web search via its API (credential-gated)."""

    name = "exa"
    requires_credential = "exa"
    _API = "https://api.exa.ai/search"

    def search(self, query: str, cursor: str | None, limit: int) -> PulseResult:
        h, _, c = self._auth(headers={"Content-Type": "application/json"})
        import requests

        resp = requests.post(
            self._API,
            json={"query": query, "numResults": limit, "contents": {"text": True}},
            headers=h,
            cookies=c,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        docs = [
            PulseDocument(
                id=r.get("id") or r.get("url", ""),
                url=r.get("url", ""),
                title=r.get("title", ""),
                text=(r.get("text") or "")[:20000],
                author=r.get("author", ""),
                created_at=r.get("publishedDate", ""),
                metrics={"score": r.get("score", 0)},
            )
            for r in data.get("results", [])
        ]
        return PulseResult(documents=docs)
