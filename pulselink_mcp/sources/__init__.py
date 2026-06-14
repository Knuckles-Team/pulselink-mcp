"""PulseLink source registry — wires every source to its backend ladder.

CONCEPT:PULSE-001 — the ladders are built here and resolved by name. A source's
ordered backend list encodes the fallback policy: highest-fidelity / keyless first,
auth backends below (they only become eligible when their credential exists).
"""

from __future__ import annotations

from .base import (
    BackendHealth,
    CapabilityUnsupported,
    PulseDocument,
    PulseResult,
    SourceLadder,
)
from .china import BilibiliBackend, XiaohongshuBackend, XueqiuBackend
from .dev import ExaBackend, GitHubPublicBackend, GitHubTokenBackend
from .forums import (
    HackerNewsBackend,
    RedditOAuthBackend,
    RedditPublicBackend,
    V2exBackend,
)
from .media import PodcastBackend, YouTubeBackend
from .social import (
    LinkedInCookieBackend,
    LinkedInJinaBackend,
    XApiBackend,
    XCookieBackend,
)
from .web import GoogleNewsBackend, JinaWebBackend, RssBackend

__all__ = [
    "SOURCES",
    "get_ladder",
    "list_sources",
    "doctor",
    "BackendHealth",
    "CapabilityUnsupported",
    "PulseDocument",
    "PulseResult",
]


def _build_registry() -> dict[str, SourceLadder]:
    """Construct every source ladder. Order within a ladder = fallback priority."""
    ladders = [
        # --- keyless-first global sources ---
        SourceLadder("youtube", [YouTubeBackend()]),
        SourceLadder("web", [JinaWebBackend()]),
        SourceLadder("rss", [RssBackend()]),
        SourceLadder("news", [GoogleNewsBackend()]),
        SourceLadder("hackernews", [HackerNewsBackend()]),
        SourceLadder("v2ex", [V2exBackend()]),
        SourceLadder("bilibili", [BilibiliBackend()]),
        SourceLadder("podcast", [PodcastBackend()]),
        # --- auth-laddered: official API → cookie/public fallback ---
        SourceLadder("github", [GitHubTokenBackend(), GitHubPublicBackend()]),
        SourceLadder("reddit", [RedditOAuthBackend(), RedditPublicBackend()]),
        SourceLadder("x", [XApiBackend(), XCookieBackend()]),
        SourceLadder("linkedin", [LinkedInCookieBackend(), LinkedInJinaBackend()]),
        SourceLadder("exa", [ExaBackend()]),
        SourceLadder("xiaohongshu", [XiaohongshuBackend()]),
        SourceLadder("xueqiu", [XueqiuBackend()]),
    ]
    return {ladder.source: ladder for ladder in ladders}


SOURCES: dict[str, SourceLadder] = _build_registry()


def get_ladder(source: str) -> SourceLadder:
    """Return the ladder for ``source`` (raises ``KeyError`` with the valid set)."""
    ladder = SOURCES.get(source)
    if ladder is None:
        raise KeyError(
            f"unknown source {source!r}. Available: {', '.join(sorted(SOURCES))}"
        )
    return ladder


def list_sources() -> list[str]:
    """All registered source names."""
    return sorted(SOURCES)


def doctor() -> dict[str, list[BackendHealth]]:
    """Per-source backend health (the server-side 'doctor')."""
    return {name: ladder.health() for name, ladder in SOURCES.items()}
