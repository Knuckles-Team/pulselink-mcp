"""China-platform backends: Bilibili, Xiaohongshu, Xueqiu.

CONCEPT:PULSE-007 — China-platform sources
"""

from __future__ import annotations

from .base import PulseDocument, PulseResult, SourceBackend


class BilibiliBackend(SourceBackend):
    """Bilibili via its keyless public web-interface search API."""

    name = "bilibili"
    _SEARCH = "https://api.bilibili.com/x/web-interface/search/all/v2"
    _VIEW = "https://api.bilibili.com/x/web-interface/view"

    def search(self, query: str, cursor: str | None, limit: int) -> PulseResult:
        page = int(cursor) if cursor else 1
        data = self.get_json(
            self._SEARCH,
            params={"keyword": query, "page": str(page)},
            headers={"Referer": "https://www.bilibili.com"},
        )
        docs: list[PulseDocument] = []
        for group in data.get("data", {}).get("result", []) or []:
            if group.get("result_type") != "video":
                continue
            for v in group.get("data", [])[:limit]:
                bvid = v.get("bvid", "")
                docs.append(
                    PulseDocument(
                        id=bvid,
                        url=f"https://www.bilibili.com/video/{bvid}",
                        title=_strip_em(v.get("title", "")),
                        text=v.get("description", ""),
                        author=v.get("author", ""),
                        created_at=str(v.get("pubdate", "")),
                        metrics={
                            "play": v.get("play", 0),
                            "danmaku": v.get("danmaku", 0),
                        },
                    )
                )
        return PulseResult(documents=docs, next_cursor=str(page + 1) if docs else None)

    def fetch(self, url_or_id: str) -> PulseDocument:
        bvid = url_or_id.rstrip("/").split("/")[-1]
        data = self.get_json(
            self._VIEW,
            params={"bvid": bvid},
            headers={"Referer": "https://www.bilibili.com"},
        )
        d = data.get("data", {})
        return PulseDocument(
            id=bvid,
            url=f"https://www.bilibili.com/video/{bvid}",
            title=d.get("title", ""),
            text=d.get("desc", ""),
            author=(d.get("owner") or {}).get("name", ""),
            created_at=str(d.get("pubdate", "")),
            metrics=(d.get("stat") or {}),
        )


def _strip_em(text: str) -> str:
    import re

    return re.sub(r"</?em[^>]*>", "", text)


class XiaohongshuBackend(SourceBackend):
    """Xiaohongshu note fetch — keyless public note JSON, cookie for feed/search."""

    name = "xiaohongshu"
    requires_credential = "xiaohongshu"

    def search(self, query: str, cursor: str | None, limit: int) -> PulseResult:
        # Search requires an authenticated session; the credential supplies it.
        data = self.get_json(
            "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes",
            params={"keyword": query, "page": str(int(cursor) if cursor else 1)},
        )
        docs = [
            PulseDocument(
                id=n.get("id", ""),
                url=f"https://www.xiaohongshu.com/explore/{n.get('id', '')}",
                title=(n.get("note_card") or {}).get("display_title", ""),
                text=(n.get("note_card") or {}).get("desc", ""),
                author=((n.get("note_card") or {}).get("user") or {}).get(
                    "nickname", ""
                ),
            )
            for n in data.get("data", {}).get("items", [])
        ]
        return PulseResult(documents=docs)


class XueqiuBackend(SourceBackend):
    """Xueqiu (stocks) quotes/posts — cookie-authenticated."""

    name = "xueqiu"
    requires_credential = "xueqiu"

    def search(self, query: str, cursor: str | None, limit: int) -> PulseResult:
        data = self.get_json(
            "https://xueqiu.com/query/v1/symbol/search/status.json",
            params={"q": query, "count": str(limit)},
            headers={"Referer": "https://xueqiu.com"},
        )
        docs = [
            PulseDocument(
                id=str(p.get("id", "")),
                url="https://xueqiu.com" + p.get("target", ""),
                title=p.get("title", ""),
                text=p.get("description", "") or p.get("text", ""),
                author=(p.get("user") or {}).get("screen_name", ""),
                created_at=str(p.get("created_at", "")),
                metrics={
                    "reply": p.get("reply_count", 0),
                    "like": p.get("like_count", 0),
                },
            )
            for p in data.get("list", [])
        ]
        return PulseResult(documents=docs)
