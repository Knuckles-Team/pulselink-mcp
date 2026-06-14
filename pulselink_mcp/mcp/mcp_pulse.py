"""PulseLink MCP tools — keyless open-web/social research reach.

CONCEPT:PULSE-001 — search/fetch/list/transcribe across every source ladder, plus
a server-side ``pulse_status`` doctor reporting per-source backend + credential
health. Each tool drives the :class:`~pulselink_mcp.api.PulseLinkClient` (over the
source registry); the blocking HTTP/yt-dlp work runs in a worker thread so the
server stays async.
"""

from __future__ import annotations

import asyncio

from fastmcp import Context, FastMCP
from pydantic import Field

from ..auth import get_client
from ..sources import list_sources


def register_pulse_tools(mcp: FastMCP) -> None:
    """Register the pulse reach tools onto ``mcp``."""

    @mcp.tool(tags={"pulse"})
    async def pulse_search(
        source: str = Field(
            description=f"Source to search. One of: {', '.join(list_sources())}."
        ),
        query: str = Field(description="Search query."),
        cursor: str | None = Field(
            default=None, description="Opaque pagination cursor from a prior call."
        ),
        limit: int = Field(default=10, description="Max results to return."),
        ctx: Context | None = None,
    ) -> dict:
        """Search a source and return normalized documents. CONCEPT:PULSE-001"""
        if ctx:
            ctx.info(f"pulse_search source={source!r} query={query!r}")
        try:
            return await asyncio.to_thread(
                get_client().search, source, query, cursor, limit
            )
        except Exception as exc:  # noqa: BLE001 — surface as a tool error, not a crash
            return {"error": str(exc), "source": source}

    @mcp.tool(tags={"pulse"})
    async def pulse_fetch(
        source: str = Field(description="Source the target belongs to."),
        target: str = Field(description="URL or source-native id to fetch in full."),
        ctx: Context | None = None,
    ) -> dict:
        """Fetch one item (full text/body/transcript). CONCEPT:PULSE-001"""
        if ctx:
            ctx.info(f"pulse_fetch source={source!r} target={target!r}")
        try:
            return await asyncio.to_thread(get_client().fetch, source, target)
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc), "source": source}

    @mcp.tool(tags={"pulse"})
    async def pulse_list(
        source: str = Field(description="Source to list from."),
        channel: str = Field(
            description="Channel/feed/subreddit/node within the source "
            "(e.g. a subreddit, an RSS feed URL, a V2EX node)."
        ),
        cursor: str | None = Field(default=None, description="Pagination cursor."),
        limit: int = Field(default=10, description="Max items to return."),
        ctx: Context | None = None,
    ) -> dict:
        """List items from a source channel/feed. CONCEPT:PULSE-001"""
        if ctx:
            ctx.info(f"pulse_list source={source!r} channel={channel!r}")
        try:
            return await asyncio.to_thread(
                get_client().list_items, source, channel, cursor, limit
            )
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc), "source": source}

    @mcp.tool(tags={"pulse"})
    async def pulse_transcribe(
        target: str = Field(description="Video/audio URL or id to transcribe."),
        source: str = Field(
            default="youtube",
            description="Source providing the media (default 'youtube').",
        ),
        ctx: Context | None = None,
    ) -> dict:
        """Transcribe video/audio to text. CONCEPT:PULSE-005"""
        if ctx:
            ctx.info(f"pulse_transcribe source={source!r} target={target!r}")
        try:
            return await asyncio.to_thread(get_client().transcribe, target, source)
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc), "source": source}

    @mcp.tool(tags={"pulse"})
    async def pulse_status(ctx: Context | None = None) -> dict:
        """Per-source backend + credential health (the doctor). CONCEPT:PULSE-001"""
        if ctx:
            ctx.info("pulse_status")
        return await asyncio.to_thread(get_client().status)
