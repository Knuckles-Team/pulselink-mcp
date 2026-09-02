"""PulseLink source registry — wires every source to its backend ladder.

CONCEPT:PK-OS.governance.search-fetch-list-transcribe — the ladders are built here and resolved by name. A source's
ordered backend list encodes the fallback policy: highest-fidelity / keyless first,
auth backends below (they only become eligible when their credential exists).
"""

from __future__ import annotations

from .base import (
    BackendHealth,
    CapabilityUnsupported,
    CredentialAuthority,
    PulseDocument,
    PulseResult,
    SourceBackend,
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
    "SOURCE_NAMES",
    "build_registry",
    "BackendHealth",
    "CapabilityUnsupported",
    "PulseDocument",
    "PulseResult",
]

SOURCE_NAMES: tuple[str, ...] = (
    "bilibili",
    "exa",
    "github",
    "hackernews",
    "linkedin",
    "news",
    "podcast",
    "reddit",
    "rss",
    "v2ex",
    "web",
    "x",
    "xiaohongshu",
    "xueqiu",
    "youtube",
)


def build_registry(
    credential_authority: CredentialAuthority,
) -> dict[str, SourceLadder]:
    """Construct source ladders with one explicit credential authority."""

    def backend(backend_type: type[SourceBackend]) -> SourceBackend:
        return backend_type(credential_authority)

    def ladder(source: str, *backend_types: type[SourceBackend]) -> SourceLadder:
        return SourceLadder(source, [backend(kind) for kind in backend_types])

    ladders = [
        # --- keyless-first global sources ---
        ladder("youtube", YouTubeBackend),
        ladder("web", JinaWebBackend),
        ladder("rss", RssBackend),
        ladder("news", GoogleNewsBackend),
        ladder("hackernews", HackerNewsBackend),
        ladder("v2ex", V2exBackend),
        ladder("bilibili", BilibiliBackend),
        ladder("podcast", PodcastBackend),
        # --- auth-laddered: official API → cookie/public fallback ---
        ladder("github", GitHubTokenBackend, GitHubPublicBackend),
        ladder("reddit", RedditOAuthBackend, RedditPublicBackend),
        ladder("x", XApiBackend, XCookieBackend),
        ladder("linkedin", LinkedInCookieBackend, LinkedInJinaBackend),
        ladder("exa", ExaBackend),
        ladder("xiaohongshu", XiaohongshuBackend),
        ladder("xueqiu", XueqiuBackend),
    ]
    return {ladder.source: ladder for ladder in ladders}
