"""Surface contracts: tool use, links, data locations and business roles."""

from scion_sdk.surface_contracts import (
    BusinessRole,
    DataLocation,
    Refusal,
    SurfaceLink,
    ToolStep,
    ToolUseContract,
)

CONTRACTS = (
    ToolUseContract(
        "search-a-source",
        (
            ToolStep(
                "pulselink_sources",
                result=("sources",),
            ),
            ToolStep(
                "pulse_search",
                params=("source", "query", "cursor", "limit"),
                result=("documents", "next_cursor", "backend"),
                refusals=(
                    Refusal(
                        "UNKNOWN_SOURCE",
                        "the source is not one of the registered sources",
                    ),
                    Refusal(
                        "ALL_BACKENDS_FAILED",
                        "every backend of the source ladder failed the request",
                    ),
                    Refusal(
                        "CREDENTIAL_AUTHORITY_UNAVAILABLE",
                        "the runtime credential authority is not available to the server",
                    ),
                ),
            ),
            ToolStep(
                "pulselink_search",
                params=("source", "query", "cursor", "limit"),
                result=("documents", "next_cursor", "backend"),
                refusals=(
                    Refusal(
                        "UNKNOWN_SOURCE",
                        "the source is not one of the registered sources",
                    ),
                    Refusal(
                        "ALL_BACKENDS_FAILED",
                        "every backend of the source ladder failed the request",
                    ),
                    Refusal(
                        "CREDENTIAL_AUTHORITY_UNAVAILABLE",
                        "the runtime credential authority is not available to the server",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        "fetch-an-item",
        (
            ToolStep(
                "pulse_fetch",
                params=("source", "target"),
                result=("id", "url", "title", "text", "author", "created_at"),
                refusals=(
                    Refusal(
                        "UNKNOWN_SOURCE",
                        "the source is not one of the registered sources",
                    ),
                    Refusal(
                        "ALL_BACKENDS_FAILED",
                        "every backend of the source ladder failed the request",
                    ),
                    Refusal(
                        "CREDENTIAL_AUTHORITY_UNAVAILABLE",
                        "the runtime credential authority is not available to the server",
                    ),
                ),
            ),
            ToolStep(
                "pulselink_fetch",
                params=("source", "target"),
                result=("id", "url", "title", "text"),
                refusals=(
                    Refusal(
                        "UNKNOWN_SOURCE",
                        "the source is not one of the registered sources",
                    ),
                    Refusal(
                        "ALL_BACKENDS_FAILED",
                        "every backend of the source ladder failed the request",
                    ),
                    Refusal(
                        "CREDENTIAL_AUTHORITY_UNAVAILABLE",
                        "the runtime credential authority is not available to the server",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        "list-a-channel",
        (
            ToolStep(
                "pulse_list",
                params=("source", "channel", "cursor", "limit"),
                result=("documents", "next_cursor"),
                refusals=(
                    Refusal(
                        "UNKNOWN_SOURCE",
                        "the source is not one of the registered sources",
                    ),
                    Refusal(
                        "ALL_BACKENDS_FAILED",
                        "every backend of the source ladder failed the request",
                    ),
                    Refusal(
                        "CREDENTIAL_AUTHORITY_UNAVAILABLE",
                        "the runtime credential authority is not available to the server",
                    ),
                ),
            ),
            ToolStep(
                "pulselink_list_items",
                params=("source", "channel", "cursor", "limit"),
                result=("documents", "next_cursor"),
                refusals=(
                    Refusal(
                        "UNKNOWN_SOURCE",
                        "the source is not one of the registered sources",
                    ),
                    Refusal(
                        "ALL_BACKENDS_FAILED",
                        "every backend of the source ladder failed the request",
                    ),
                    Refusal(
                        "CREDENTIAL_AUTHORITY_UNAVAILABLE",
                        "the runtime credential authority is not available to the server",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        "transcribe-media",
        (
            ToolStep(
                "pulse_search",
                params=("source", "query", "limit"),
                result=("documents",),
                refusals=(
                    Refusal(
                        "UNKNOWN_SOURCE",
                        "the source is not one of the registered sources",
                    ),
                    Refusal(
                        "ALL_BACKENDS_FAILED",
                        "every backend of the source ladder failed the request",
                    ),
                ),
            ),
            ToolStep(
                "pulse_transcribe",
                params=("target", "source"),
                result=("id", "url", "text"),
                refusals=(
                    Refusal(
                        "TRANSCRIBER_UNAVAILABLE",
                        "yt-dlp or the Whisper extra is not installed",
                    ),
                    Refusal(
                        "ALL_BACKENDS_FAILED",
                        "every backend of the source ladder failed the request",
                    ),
                ),
            ),
            ToolStep(
                "pulselink_transcribe",
                params=("target", "source"),
                result=("id", "url", "text"),
                refusals=(
                    Refusal(
                        "TRANSCRIBER_UNAVAILABLE",
                        "yt-dlp or the Whisper extra is not installed",
                    ),
                    Refusal(
                        "ALL_BACKENDS_FAILED",
                        "every backend of the source ladder failed the request",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        "check-source-health",
        (
            ToolStep(
                "pulse_status",
                result=("source", "backend", "ok", "needs_auth", "detail"),
                refusals=(
                    Refusal(
                        "CREDENTIAL_AUTHORITY_UNAVAILABLE",
                        "the runtime credential authority is not available to the server",
                    ),
                ),
            ),
            ToolStep(
                "pulselink_status",
                result=("source", "backend", "ok", "needs_auth", "detail"),
                refusals=(
                    Refusal(
                        "CREDENTIAL_AUTHORITY_UNAVAILABLE",
                        "the runtime credential authority is not available to the server",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        "ingest-source-to-graph",
        (
            ToolStep(
                "pulse_ingest",
                params=("source", "query", "channel", "limit"),
                result=("source", "listed", "ingested"),
                refusals=(
                    Refusal(
                        "UNKNOWN_SOURCE",
                        "the source is not one of the registered sources",
                    ),
                    Refusal(
                        "NO_ENGINE",
                        "no knowledge-graph engine is reachable, ingested is null",
                    ),
                    Refusal(
                        "ALL_BACKENDS_FAILED",
                        "every backend of the source ladder failed the request",
                    ),
                ),
            ),
        ),
    ),
)

LINKS = (
    SurfaceLink(
        "search-a-source",
        tools=("pulselink_sources", "pulse_search", "pulselink_search"),
        prompts=("pulselink-operator", "pulselink-web-researcher"),
        skills=(
            "pulselink-web-news",
            "pulselink-social-research",
            "pulselink-media-transcripts",
        ),
    ),
    SurfaceLink(
        "fetch-an-item",
        tools=("pulse_fetch", "pulselink_fetch"),
        prompts=("pulselink-operator", "pulselink-web-researcher"),
        skills=(
            "pulselink-web-news",
            "pulselink-social-research",
            "pulselink-media-transcripts",
        ),
    ),
    SurfaceLink(
        "list-a-channel",
        tools=("pulse_list", "pulselink_list_items"),
        prompts=("pulselink-operator", "pulselink-web-researcher"),
        skills=("pulselink-web-news", "pulselink-social-research"),
    ),
    SurfaceLink(
        "transcribe-media",
        tools=("pulse_search", "pulse_transcribe", "pulselink_transcribe"),
        prompts=("pulselink-operator", "pulselink-media-analyst"),
        skills=("pulselink-media-transcripts",),
    ),
    SurfaceLink(
        "check-source-health",
        tools=("pulse_status", "pulselink_status"),
        prompts=("pulselink-operator", "pulselink-source-steward"),
        skills=(
            "pulselink-web-news",
            "pulselink-social-research",
            "pulselink-media-transcripts",
        ),
    ),
    SurfaceLink(
        "ingest-source-to-graph",
        tools=("pulse_ingest",),
        prompts=("pulselink-operator", "pulselink-source-steward"),
        skills=(
            "pulselink-web-news",
            "pulselink-social-research",
            "pulselink-media-transcripts",
        ),
    ),
    SurfaceLink(
        "pulselink-mcp-operations",
        tools=("pulse_search", "pulse_fetch", "pulse_status", "pulselink_sources"),
        skills=("pulselink-mcp-operations",),
    ),
)

LOCATIONS = (
    DataLocation(
        "pulselink-web-and-news",
        ("Document", "PulseSource"),
        "PULSELINK_WEB_SOURCES",
        "pulse_search",
        route_param="source",
        federation_key="url",
    ),
    DataLocation(
        "pulselink-social-and-dev",
        ("Document", "PulseSource"),
        "PULSELINK_SOCIAL_SOURCES",
        "pulse_list",
        route_param="source",
        federation_key="id",
    ),
    DataLocation(
        "pulselink-media",
        ("Document", "PulseSource"),
        "PULSELINK_MEDIA_SOURCES",
        "pulse_fetch",
        route_param="source",
        federation_key="url",
    ),
    DataLocation(
        "pulselink-source-health",
        ("SourceBackend",),
        "PULSELINK_SOURCE_REGISTRY",
        "pulse_status",
        federation_key="backend",
    ),
)

ROLES = (
    BusinessRole(
        "web-researcher", tasks=("search-a-source", "fetch-an-item", "list-a-channel")
    ),
    BusinessRole("media-analyst", tasks=("transcribe-media",)),
    BusinessRole(
        "source-steward", tasks=("check-source-health", "ingest-source-to-graph")
    ),
)
