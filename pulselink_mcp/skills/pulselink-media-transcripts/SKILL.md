---
name: pulselink-media-transcripts
description: >-
  Keyless video & audio research over the pulselink-mcp MCP server — search YouTube,
  Bilibili and podcasts, and turn a video/episode into a text transcript (yt-dlp
  captions, Whisper fallback) with no API keys. Use when the agent must find talks on
  a topic, pull a video's metadata, or extract the spoken content of a YouTube video
  or podcast episode as text for summarization or KG ingestion. Do NOT use for
  social/community threads (pulselink-social-research) or web/RSS/news pages
  (pulselink-web-news).
license: MIT
tags: [pulselink, youtube, podcast, transcript, whisper, mcp]
metadata:
  author: Genius
  version: '0.1.0'
---
# PulseLink Video & Audio Transcripts

Domain-typed, keyless reach into **YouTube**, **Bilibili**, and **podcasts** through
the pulselink-mcp source ladder, plus transcript extraction — captions via `yt-dlp`
when present, Whisper transcription as the fallback. Search and metadata are keyless;
transcription needs the media extras installed.

## When to use
- Search YouTube/Bilibili for videos on a topic (`pulse_search`).
- Pull a video's metadata + best available caption text (`pulse_fetch`).
- Transcribe a video/episode URL to plain text (`pulse_transcribe`).
- Ingest transcripts into the KG as `:Document` nodes for semantic search.

## When NOT to use
- Reddit/HN/X/LinkedIn/V2EX discussions → `pulselink-social-research`.
- Open-web pages / RSS / news → `pulselink-web-news`.
- Bulk media *downloading* (not transcription) → the `media-downloader` package.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`pulselink-mcp`** MCP server.
Transcription requires optional extras:

| Variable / extra | Required | Notes |
|------------------|----------|-------|
| `pulselink-mcp[youtube]` (`yt-dlp`) | for YouTube search/fetch/captions | Used as a library, no external binary |
| `pulselink-mcp[audio]` (`faster-whisper`) | for Whisper fallback transcription | Only when no caption track exists |
| `MCP_TOOL_MODE` | optional | `condensed` \| `verbose` \| `both` |

## Tools & actions
| Tool | What it does |
|------|--------------|
| `pulse_search` | Search a `source` (`youtube`, `bilibili`, `podcast`) for a `query`. |
| `pulse_fetch` | Fetch one video/episode: metadata + caption text if available. |
| `pulse_transcribe` | Transcribe a `target` URL/id to text (`source` default `youtube`). |
| `pulse_status` | Per-source backend health (flags missing `yt-dlp`/Whisper). |
| `pulse_ingest` | Search then push documents into the KG. |

## Recipes
Search YouTube:
```json
{"source": "youtube", "query": "epistemic graph database talk", "limit": 10}
```
Fetch a video's metadata + captions:
```json
{"source": "youtube", "target": "https://www.youtube.com/watch?v=VIDEOID"}
```
Transcribe a video to text:
```json
{"target": "https://www.youtube.com/watch?v=VIDEOID", "source": "youtube"}
```
Transcribe a podcast episode audio URL:
```json
{"target": "https://example.com/episode-42.mp3", "source": "podcast"}
```

## Gotchas
- Transcription is heavy: prefer `pulse_fetch` (existing caption track) and fall back
  to `pulse_transcribe` (Whisper) only when no captions exist.
- Without the `[youtube]` extra, YouTube tools raise "yt-dlp not installed"; without
  `[audio]`, Whisper transcription is unavailable — check `pulse_status`.
- Long videos/episodes take real time and CPU/GPU to transcribe — scope with search
  first, transcribe deliberately.
- `pulse_transcribe` defaults `source` to `youtube`; set it explicitly for podcasts.
- Ingestion is best-effort: no engine → `pulse_ingest` returns `ingested: null`.

## Related
- `pulselink-social-research` and `pulselink-web-news` — the other pulselink sources.
- `pulse_ingest` maps transcripts to the `pulselink` ontology (`:Document` →
  `:fromSource` `:PulseSource`).
