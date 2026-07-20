"""PulseLink MCP tools — keyless open-web/social research reach.

CONCEPT:PK-OS.governance.search-fetch-list-transcribe — search/fetch/list/transcribe across every source ladder, plus
a server-side ``pulse_status`` doctor reporting per-source backend + credential
health. Each tool drives the :class:`~pulselink_mcp.api.PulseLinkClient` (over the
source registry); the blocking HTTP/yt-dlp work runs in a worker thread so the
server stays async.
"""

from __future__ import annotations

import asyncio
import logging

from fastmcp import Context, FastMCP
from pydantic import Field

from ..auth import get_client
from ..sources import list_sources

logger = logging.getLogger("pulselink_mcp.mcp")


def _maybe_ingest(source: str, result: dict) -> None:
    """Push a search/list/fetch result's documents into the authoritative KG."""
    if not isinstance(result, dict) or result.get("error"):
        return
    docs = result.get("documents")
    if docs is None and result.get("id"):  # a single fetched document
        docs = [result]
    if not docs:
        return
    from ..kg_ingest import ingest_pulse_documents

    ingest_pulse_documents(source, docs)


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
        """Search a source and return normalized documents. CONCEPT:PK-OS.governance.search-fetch-list-transcribe"""
        if ctx:
            ctx.info("Executing configured pulse search")
        try:
            result = await asyncio.to_thread(
                get_client().search, source, query, cursor, limit
            )
            await asyncio.to_thread(_maybe_ingest, source, result)
            return result
        except Exception:  # noqa: BLE001 — surface as a tool error, not a crash
            return {"error": "Operation failed", "source": source}

    @mcp.tool(tags={"pulse"})
    async def pulse_fetch(
        source: str = Field(description="Source the target belongs to."),
        target: str = Field(description="URL or source-native id to fetch in full."),
        ctx: Context | None = None,
    ) -> dict:
        """Fetch one item (full text/body/transcript). CONCEPT:PK-OS.governance.search-fetch-list-transcribe"""
        if ctx:
            ctx.info(f"pulse_fetch source={source!r} target={target!r}")
        try:
            result = await asyncio.to_thread(get_client().fetch, source, target)
            await asyncio.to_thread(_maybe_ingest, source, result)
            return result
        except Exception:  # noqa: BLE001
            return {"error": "Operation failed", "source": source}

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
        """List items from a source channel/feed. CONCEPT:PK-OS.governance.search-fetch-list-transcribe"""
        if ctx:
            ctx.info(f"pulse_list source={source!r} channel={channel!r}")
        try:
            result = await asyncio.to_thread(
                get_client().list_items, source, channel, cursor, limit
            )
            await asyncio.to_thread(_maybe_ingest, source, result)
            return result
        except Exception:  # noqa: BLE001
            return {"error": "Operation failed", "source": source}

    @mcp.tool(tags={"pulse"})
    async def pulse_transcribe(
        target: str = Field(description="Video/audio URL or id to transcribe."),
        source: str = Field(
            default="youtube",
            description="Source providing the media (default 'youtube').",
        ),
        ctx: Context | None = None,
    ) -> dict:
        """Transcribe video/audio to text. CONCEPT:PK-OS.governance.audio-video-sources-transcript"""
        if ctx:
            ctx.info(f"pulse_transcribe source={source!r} target={target!r}")
        try:
            return await asyncio.to_thread(get_client().transcribe, target, source)
        except Exception:  # noqa: BLE001
            return {"error": "Operation failed", "source": source}

    @mcp.tool(tags={"pulse"})
    async def pulse_status(ctx: Context | None = None) -> dict:
        """Per-source backend + credential health (the doctor). CONCEPT:PK-OS.governance.search-fetch-list-transcribe"""
        if ctx:
            ctx.info("pulse_status")
        return await asyncio.to_thread(get_client().status)

    @mcp.tool(tags={"pulse", "kg"})
    async def pulse_ingest(
        source: str = Field(description="Source to pull from (see pulse_search)."),
        query: str = Field(
            default="", description="Search query (used when no channel is given)."
        ),
        channel: str = Field(
            default="",
            description="Channel/feed/subreddit/node to list from instead of searching.",
        ),
        limit: int = Field(default=10, description="Max documents to pull + ingest."),
        ctx: Context | None = None,
    ) -> dict:
        """Search/list a source and natively ingest the results into epistemic-graph.

        Lists via the real PulseLink client (``pulse_list`` when ``channel`` is set,
        else ``pulse_search``) and pushes the documents as typed :Document nodes linked to
        their :PulseSource and :Person author. Native-ingest failures propagate to the
        caller. CONCEPT:AU-KG.ingest.enterprise-source-extractor
        """
        if ctx:
            ctx.info(
                f"pulse_ingest source={source!r} channel={channel!r} query={query!r}"
            )
        try:
            if channel:
                result = await asyncio.to_thread(
                    get_client().list_items, source, channel, None, limit
                )
            else:
                result = await asyncio.to_thread(
                    get_client().search, source, query, None, limit
                )
        except Exception:  # noqa: BLE001
            return {"error": "Operation failed", "source": source}

        docs = result.get("documents", [])
        from ..kg_ingest import ingest_pulse_documents

        ingested = await asyncio.to_thread(ingest_pulse_documents, source, docs)
        return {"source": source, "listed": len(docs), "ingested": ingested}
