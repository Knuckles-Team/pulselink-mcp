#!/usr/bin/python
"""X (formerly Twitter) Search and Browsing Tools.

CONCEPT:PK-OS.governance.x-search-browse-tools — Social sources via an X live index

Externalized from agent-utilities (was ``agent_utilities/tools/x_search_tool.py``):
PulseLink is the home for X reach, so the X-specific search/browse tools and their
xAI credential resolution live here. agent-utilities imports these **optionally**
(``tool_registry`` try/except), so its core carries no X integration.

These are ``pydantic-ai`` agent tools (distinct from PulseLink's MCP source
backends): they reach X through the provider's native ``x_search`` index rather than
X's own API/cookies (PulseLink's ``x`` source ladder covers those paths). The xAI
provider auth itself (``XaiAuthManager``) remains general agent-utilities infra
and is imported from there.
"""

import json
import logging
import re
from datetime import UTC, date, datetime
from typing import Any, NamedTuple

import httpx
from agent_connector_sdk.config import setting
from agent_connector_sdk.tls.resolve import resolve_tls_profile
from agent_utilities.core.http_client import create_http_client
from agent_utilities.harness.tracing import trace
from agent_utilities.models import AgentDeps
from agent_utilities.orchestration.resilience import (
    ResiliencePolicy,
    run_with_resilience,
)
from agent_utilities.security.xai_auth import XaiAuthManager
from agent_utilities.tools.versioning import tool_version
from pydantic_ai import RunContext

logger = logging.getLogger(__name__)

# Constants
DEFAULT_XAI_BASE_URL = "https://api.x.ai/v1"
DEFAULT_X_SEARCH_TIMEOUT_SECONDS = 180
DEFAULT_X_SEARCH_RETRIES = 2
MAX_HANDLES = 10


def _normalize_handles(handles: list[Any] | None, field_name: str) -> list[str]:
    """Clean and validate X handles list."""
    if not handles:
        return []
    cleaned: list[str] = []
    for handle in handles:
        normalized = (handle or "").strip().lstrip("@")
        if normalized:
            cleaned.append(normalized)
    if len(cleaned) > MAX_HANDLES:
        raise ValueError(f"{field_name} supports at most {MAX_HANDLES} handles")
    return cleaned


def _parse_iso_date(value: str, field_name: str) -> date:
    """Parse a strict YYYY-MM-DD string into a ``date``."""
    raw = value.strip()
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{field_name} must be YYYY-MM-DD (got {raw!r})") from exc


def _validate_date_range(from_date: str, to_date: str) -> None:
    """Validate date ranges before sending to xAI.

    Rules:
      * Either field, if non-empty, must parse as ``YYYY-MM-DD``.
      * When both are set, ``from_date <= to_date``.
      * ``from_date`` must not be in the future.
    """
    parsed_from: date | None = None
    parsed_to: date | None = None
    if from_date.strip():
        parsed_from = _parse_iso_date(from_date, "from_date")
    if to_date.strip():
        parsed_to = _parse_iso_date(to_date, "to_date")
    if parsed_from and parsed_to and parsed_from > parsed_to:
        raise ValueError(
            f"from_date ({parsed_from.isoformat()}) must be on or before "
            f"to_date ({parsed_to.isoformat()})"
        )
    if parsed_from is not None:
        today_utc = datetime.now(UTC).date()
        if parsed_from > today_utc:
            raise ValueError(
                f"from_date ({parsed_from.isoformat()}) is in the future; "
                f"X Search only indexes past posts (today UTC is "
                f"{today_utc.isoformat()})"
            )


def _message_text_parts(item: dict[str, Any]) -> list[str]:
    """Extract text/output_text content parts from one ``message``-type output item."""
    parts: list[str] = []
    for content in item.get("content", []) or []:
        if content.get("type") in {"output_text", "text"}:
            text = str(content.get("text") or "").strip()
            if text:
                parts.append(text)
    return parts


def _extract_response_text(payload: dict[str, Any]) -> str:
    """Extract full synthesized text response from xAI Responses payload."""
    output_text = str(payload.get("output_text") or "").strip()
    if output_text:
        return output_text

    parts: list[str] = []
    for item in payload.get("output", []) or []:
        if item.get("type") != "message":
            continue
        parts.extend(_message_text_parts(item))
    return "\n\n".join(parts).strip()


def _extract_inline_citations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract inline URL citations from xAI Responses payload."""
    citations: list[dict[str, Any]] = []
    for item in payload.get("output", []) or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content", []) or []:
            for annotation in content.get("annotations", []) or []:
                if annotation.get("type") != "url_citation":
                    continue
                citations.append(
                    {
                        "url": annotation.get("url", ""),
                        "title": annotation.get("title", ""),
                        "start_index": annotation.get("start_index"),
                        "end_index": annotation.get("end_index"),
                    }
                )
    return citations


class _XaiSearchConfig(NamedTuple):
    base_url: str
    model: str
    timeout: int
    max_retries: int


def _resolve_xai_api_key() -> str | None:
    """Resolve xAI credentials, triggering the auto-login flow if needed."""
    auth_manager = XaiAuthManager()
    return auth_manager.resolve_credentials(auto_login=True)  # type: ignore[call-arg]


def _resolve_xai_search_config(ctx: RunContext[AgentDeps]) -> _XaiSearchConfig:
    """Resolve base_url/model/timeout/retries from agent config, falling back to env/defaults."""
    config = getattr(ctx.deps, "config", {}) if ctx and ctx.deps else {}
    if not isinstance(config, dict):
        config = {}
    xai_config = config.get("xai", {}) or {}

    base_url = (
        str(xai_config.get("base_url") or setting("XAI_BASE_URL", DEFAULT_XAI_BASE_URL))
        .strip()
        .rstrip("/")
    )
    model = str(xai_config.get("model") or setting("XAI_SEARCH_MODEL", "")).strip()
    if not model:
        raise RuntimeError(
            "XAI_SEARCH_MODEL must be configured to use the X live-search capability"
        )
    timeout_val = xai_config.get("timeout_seconds") or setting(
        "XAI_SEARCH_TIMEOUT_SECONDS", DEFAULT_X_SEARCH_TIMEOUT_SECONDS
    )
    timeout = max(30, int(str(timeout_val)))

    retries_val = xai_config.get("retries") or setting(
        "XAI_SEARCH_RETRIES", DEFAULT_X_SEARCH_RETRIES
    )
    max_retries = max(0, int(str(retries_val)))

    return _XaiSearchConfig(
        base_url=base_url, model=model, timeout=timeout, max_retries=max_retries
    )


def _resolve_x_search_filters(
    allowed_x_handles: list[str] | None,
    excluded_x_handles: list[str] | None,
    from_date: str | None,
    to_date: str | None,
) -> tuple[list[str], list[str], str | None]:
    """Normalize + validate the handle/date filters.

    Returns ``(allowed, excluded, error)``; ``error`` is None on success, else
    the message to surface to the caller (mutual-exclusivity violation, or the
    generic message for an invalid handle list / date range).
    """
    try:
        allowed = _normalize_handles(allowed_x_handles, "allowed_x_handles")
        excluded = _normalize_handles(excluded_x_handles, "excluded_x_handles")
        if allowed and excluded:
            return (
                [],
                [],
                "allowed_x_handles and excluded_x_handles cannot be used together",
            )
        _validate_date_range(from_date or "", to_date or "")
    except ValueError:
        return [], [], "Operation failed"
    return allowed, excluded, None


def _build_x_search_tool_def(
    allowed: list[str],
    excluded: list[str],
    from_date: str | None,
    to_date: str | None,
) -> dict[str, Any]:
    """Build the xAI ``x_search`` tool constraint from the resolved filters."""
    tool_def: dict[str, Any] = {"type": "x_search"}
    if allowed:
        tool_def["allowed_x_handles"] = allowed
    if excluded:
        tool_def["excluded_x_handles"] = excluded
    if from_date and from_date.strip():
        tool_def["from_date"] = from_date.strip()
    if to_date and to_date.strip():
        tool_def["to_date"] = to_date.strip()
    return tool_def


def _is_retryable_x_search_error(exc: BaseException) -> bool:
    """CONCEPT:AU-ORCH.execution.retry-predicate-raised-treating: bounded delays retry
    connection errors and 5xx responses only."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return isinstance(exc, httpx.RequestError | httpx.TimeoutException)


async def _execute_x_search_request(
    base_url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: int,
    max_retries: int,
) -> tuple[dict[str, Any] | None, str | None]:
    """POST to xAI's ``/responses`` with resilience retry. Returns (data, error_message)."""

    def _post_once() -> dict[str, Any]:
        profile = resolve_tls_profile("model")
        try:
            with create_http_client(
                timeout=float(timeout),
                **profile.httpx_kwargs(),
            ) as client:
                resp = client.post(
                    f"{base_url}/responses",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json()
        finally:
            profile.cleanup()

    policy = ResiliencePolicy(
        max_attempts=max_retries + 1,
        backoff_base_s=1.5,
        backoff_strategy="linear",
        max_backoff_s=5.0,
        jitter=False,
        retry_on=_is_retryable_x_search_error,
        name="x_search",
    )

    try:
        return await run_with_resilience(_post_once, policy), None
    except httpx.HTTPStatusError as exc:
        return None, f"HTTP {exc.response.status_code}"
    except (httpx.RequestError, httpx.TimeoutException) as exc:
        return None, f"Connection error: {type(exc).__name__}"


def _active_x_search_filters(
    allowed: list[str],
    excluded: list[str],
    from_date: str | None,
    to_date: str | None,
) -> list[str]:
    """List which filter kinds were actually supplied, for the degraded-result check."""
    active_filters = []
    if allowed:
        active_filters.append("allowed_x_handles")
    if excluded:
        active_filters.append("excluded_x_handles")
    if from_date and from_date.strip():
        active_filters.append("from_date")
    if to_date and to_date.strip():
        active_filters.append("to_date")
    return active_filters


def _x_search_success_payload(
    model: str,
    query: str,
    response_data: dict[str, Any],
    active_filters: list[str],
) -> dict[str, Any]:
    """Build the success response body: answer, citations, and degraded-result flag."""
    answer = _extract_response_text(response_data)
    citations = list(response_data.get("citations") or [])
    inline_citations = _extract_inline_citations(response_data)

    degraded = bool(active_filters) and not citations and not inline_citations
    degraded_reason = (
        f"No citations returned despite active filters: {', '.join(active_filters)}"
        if degraded
        else None
    )

    return {
        "success": True,
        "provider": "xai",
        "tool": "x_search",
        "model": model,
        "query": query.strip(),
        "answer": answer,
        "citations": citations,
        "inline_citations": inline_citations,
        "degraded": degraded,
        "degraded_reason": degraded_reason,
    }


@trace(name="x_search", trace_type="TOOL")
@tool_version("1.0.0")
async def x_search(
    ctx: RunContext[AgentDeps],
    query: str,
    allowed_x_handles: list[str] | None = None,
    excluded_x_handles: list[str] | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> str:
    """Search X posts, profiles, and threads using the configured live index.

    This leverages the live X search tool via xAI, returning detailed summaries and citations.
    Exactly one of allowed_x_handles or excluded_x_handles may be specified, but not both.

    Args:
        ctx: Run context containing agent dependencies and configuration.
        query: The search keywords, hashtags, or phrases to look for.
        allowed_x_handles: Optional list of specific X handles to restrict search results to.
        excluded_x_handles: Optional list of X handles to filter out of the results.
        from_date: Optional start date filter in YYYY-MM-DD format (UTC).
        to_date: Optional end date filter in YYYY-MM-DD format (UTC).

    Returns:
        A JSON string containing success status, resolved answer text, and citation sources.
    """
    if not query or not query.strip():
        return json.dumps({"success": False, "error": "query is required for x_search"})

    # 1. Resolve Credentials with Auto-Login enabled
    api_key = _resolve_xai_api_key()
    if not api_key:
        return json.dumps(
            {
                "success": False,
                "error": (
                    "xAI credentials are not configured. Please authorize by running "
                    "xai login flow or set XAI_API_KEY environment variable."
                ),
            }
        )

    # 2. Parse overrides from config or env
    search_config = _resolve_xai_search_config(ctx)

    # 3. Normalize & Validate Filters
    allowed, excluded, filter_error = _resolve_x_search_filters(
        allowed_x_handles, excluded_x_handles, from_date, to_date
    )
    if filter_error:
        return json.dumps({"success": False, "error": filter_error})

    # 4. Construct Tool Constraint
    tool_def = _build_x_search_tool_def(allowed, excluded, from_date, to_date)

    payload = {
        "model": search_config.model,
        "input": [
            {
                "role": "user",
                "content": query.strip(),
            }
        ],
        "tools": [tool_def],
        "store": False,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "pulselink-mcp/x_search_tool",
    }

    # 5. Execute HTTP Request with Retries
    response_data, last_error = await _execute_x_search_request(
        search_config.base_url,
        headers,
        payload,
        search_config.timeout,
        search_config.max_retries,
    )

    if not response_data:
        return json.dumps(
            {
                "success": False,
                "error": f"Request failed: {last_error or 'Unknown error'}",
            }
        )

    # 6. Extract Answers and Citations
    active_filters = _active_x_search_filters(allowed, excluded, from_date, to_date)
    result = _x_search_success_payload(
        search_config.model, query, response_data, active_filters
    )
    return json.dumps(result, ensure_ascii=False)


class _XPostRef(NamedTuple):
    cleaned_url: str
    post_id: str
    username: str | None


def _parse_x_post_url(url: str) -> _XPostRef | None:
    """Parse a post id + optional username out of an X/Twitter status URL.

    Supports ``https://x.com/username/status/12345``,
    ``https://twitter.com/username/status/12345``, and
    ``https://x.com/i/status/12345``. Returns None if the URL doesn't look
    like a status URL at all.
    """
    cleaned_url = url.strip()
    status_match = re.search(r"/status/(\d+)", cleaned_url)
    if not status_match:
        return None
    post_id = status_match.group(1)

    handle_match = re.search(r"(?:x|twitter)\.com/([A-Za-z0-9_]+)/status/", cleaned_url)
    username = handle_match.group(1) if handle_match else None
    if username == "i":
        username = None

    return _XPostRef(cleaned_url=cleaned_url, post_id=post_id, username=username)


def _build_x_post_lookup_query(ref: _XPostRef) -> str:
    """Build the query that guides a live-index lookup for one specific post."""
    query_parts = [
        f"Retrieve the exact text, author, timestamp, and engagement metrics of the X post status ID {ref.post_id}"
    ]
    if ref.username:
        query_parts.append(f"by user @{ref.username}")
    query_parts.append(f"canonical URL {ref.cleaned_url}.")
    query_parts.append(
        "CRITICAL: You MUST return the actual text content of the post, the author's handle, the date/time, and any metrics you can find. Do NOT return a generic summary."
    )
    return " ".join(query_parts)


def _annotate_browse_result(res: dict[str, Any], ref: _XPostRef) -> None:
    """Add direct metadata fields to the search result for first-class usability."""
    res["tool"] = "browse_x_post"
    res["post_id"] = ref.post_id
    if ref.username:
        res["username"] = ref.username
    res["url"] = ref.cleaned_url


async def _auto_ingest_x_post(
    ctx: RunContext[AgentDeps], res: dict[str, Any], post_id: str
) -> None:
    """Best-effort KG ingestion of a browsed post; never raises into the caller."""
    try:
        from agent_utilities.knowledge_graph.kb.x_ingestion import XIngestionBridge

        # Try to get graph from deps or create a minimal one
        graph = getattr(getattr(ctx, "deps", None), "graph", None)
        if graph is None:
            logger.debug("auto_ingest=True but no graph in ctx.deps; skipping")
            return
        bridge = XIngestionBridge(graph=graph)
        ingest_result = await bridge.ingest_browse_result(res)
        res["ingestion"] = ingest_result
        logger.info(
            "Auto-ingested post %s: action=%s",
            post_id,
            ingest_result.get("action"),
        )
    except Exception as e:
        logger.warning("Operation failed: error_type=%s", type(e).__name__)


@trace(name="browse_x_post", trace_type="TOOL")
@tool_version("1.0.0")
async def browse_x_post(
    ctx: RunContext[AgentDeps],
    url: str,
    auto_ingest: bool = False,
) -> str:
    """Retrieve and display the contents of a specific X (formerly Twitter) post.

    Accepts any X.com or Twitter.com status or post URLs and resolves the exact contents
    natively using the live X index query system.

    Args:
        ctx: Run context containing agent dependencies and configuration.
        url: The full web URL of the X post to retrieve.
        auto_ingest: If True, automatically classify and ingest the post into the
            Knowledge Graph via the Universal Knowledge Classifier pipeline.
            Creates SocialPostNode + concept edges + EvolutionCandidateNode
            if evolution potential is high. Requires KG graph in ctx.deps.

    Returns:
        A JSON string containing the detailed content, author, timestamps, engagement metrics,
        and citations extracted from the post.
    """
    if not url or not url.strip():
        return json.dumps(
            {"success": False, "error": "url is required for browse_x_post"}
        )

    # 1 & 2. Validate & Parse X / Twitter URL, extracting username/handle if present
    ref = _parse_x_post_url(url)
    if ref is None:
        return json.dumps(
            {
                "success": False,
                "error": f"Invalid X post URL format: {url!r}. Must contain '/status/<id>'.",
            }
        )

    # 3. Construct specific query optimized to retrieve the target post from the X index
    query = _build_x_post_lookup_query(ref)

    # 4. Delegate to x_search to perform the actual lookup and synthesis
    logger.info("Executing configured social-post lookup")
    search_result_str = await x_search(
        ctx=ctx,
        query=query,
        allowed_x_handles=[ref.username] if ref.username else None,
    )

    try:
        res = json.loads(search_result_str)
        if not res.get("success"):
            return search_result_str

        _annotate_browse_result(res, ref)

        # 5. Auto-ingest into KG if requested
        if auto_ingest:
            await _auto_ingest_x_post(ctx, res, ref.post_id)

        return json.dumps(res, ensure_ascii=False)

    except Exception:
        return json.dumps(
            {
                "success": False,
                "error": "Failed to parse browse result",
            }
        )


x_tools = [x_search, browse_x_post]
