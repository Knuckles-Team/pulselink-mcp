---
name: pulselink-web-news
skill_type: skill
description: >-
  Keyless open-web, RSS, and news research over the pulselink-mcp MCP server — read a web page as clean text (via Jina reader), pull items from any RSS feed, search Google News, and query GitHub, with a backend ladder that needs no API keys. Use when the agent must fetch the readable body of a URL, monitor a feed, sweep news headlines on a topic, or search public GitHub.
license: MIT
tags: [pulselink, web, rss, news, github, research, mcp]
metadata:
  author: Knuckles-Team
  version: '0.1.0'
---
# PulseLink Open-Web & News Research

Scope: Keyless open-web, RSS, and news research over the pulselink-mcp MCP server — read a web page as clean text (via Jina reader), pull items from any RSS feed, search Google News, and query GitHub, with a backend ladder that needs no API keys. Use when the agent must fetch the readable body of a URL, monitor a feed, sweep news headlines on a topic, or search public GitHub. Do NOT use for social/community threads (pulselink-social-research) or video/audio transcripts (pulselink-media-transcripts).

Domain-typed, keyless reach into the **open web** (`web` via Jina reader), **RSS**
feeds, **Google News**, and public **GitHub**, through the pulselink-mcp source
ladder. Keyless backends serve everything by default; GitHub promotes to its token
backend automatically when a credential exists.

## When to use
- Fetch the clean readable text of a web page (`web` + a URL).
- Pull the latest items from an RSS/Atom feed (`rss` + the feed URL).
- Search news headlines on a topic (`news`).
- Search public GitHub repos/issues/code (`github`).
- Ingest any of the above into the KG for semantic search.

## When NOT to use
- Reddit/HN/X/LinkedIn/V2EX discussions → `pulselink-social-research`.
- YouTube/podcast/Bilibili transcripts → `pulselink-media-transcripts`.
- Authenticated private feeds/pages the keyless backend can't reach — supply a
  credential or use the source's own dedicated connector.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`pulselink-mcp`** MCP server. All
sources here are keyless; GitHub's token backend is optional.

| Variable | Required | Notes |
|----------|----------|-------|
| `SOURCE_CREDENTIALS` / provider store | optional | Promotes the GitHub token backend; keyless public GitHub works without it |

`feedparser` is a core dependency, so `rss` and `news` work on a base install.

## Steps

1. Check backend readiness by calling `pulse_status`. Verify `web`, `rss`, `news` and `github` each report a usable backend.
2. Discover items by calling `pulse_search` with `source` (`news`, `github`, `web`) and `query`, or `pulse_list` with `source` `rss` and the feed URL as `channel`. Verify the result has documents with a `url`.
3. Read a full page or item by calling `pulse_fetch` with `source` `web` and the item `url` as `target`. Verify the returned `text` is the readable article body.
4. Page further by passing `next_cursor` back to the same call. Verify new `id` values appear.
5. Optionally persist results by calling `pulse_ingest` with `source` and `query`. Verify `ingested` reports `{nodes, edges}` rather than `null`.

## Failure recovery

| Failure | Cause | Recovery |
|---------|-------|----------|
| RSS search returns nothing | The feed URL was sent as a `query` to `pulse_search` | Call `pulse_list` with `source` `rss` and the feed URL as `channel` |
| GitHub search is rate limited | Keyless public endpoint ceiling | Add a `github` entry to `SOURCE_CREDENTIALS` to promote the token backend, then re-run `pulse_status` |
| News items have only snippets | `news` returns headlines, not article bodies | Call `pulse_fetch` with `source` `web` and each item `url` as `target` |

## Tools
| Tool | What it does |
|------|--------------|
| `pulse_fetch` | Fetch a URL/id in full (readable web body, feed item, repo/file). |
| `pulse_search` | Search a `source` for a `query` (`news`, `github`, `web`). `web` search uses Jina when it answers and falls back to a keyless Bing RSS feed (the Jina search endpoint now requires an API key). |
| `pulse_list` | List a `channel` — for `rss`, the feed URL is the channel. |
| `pulse_status` | Per-source backend + credential health. |
| `pulse_ingest` | Search/list then push documents into the KG. |

The same operations are also served as client-method tools that take the same arguments:
`pulselink_search`, `pulselink_fetch`, `pulselink_list_items`, `pulselink_transcribe`,
`pulselink_status` and `pulselink_sources` (the list of source names).

Valid `source` values here: `web`, `rss`, `news`, `github`. Documents are flat:
`id`, `title`, `url`, `text`, `author`, `created_at`, plus `next_cursor`.

## Recipes
Fetch a page as clean text:
```json
{"source": "web", "target": "https://example.com/some-article"}
```
List an RSS feed's latest items:
```json
{"source": "rss", "channel": "https://hnrss.org/frontpage", "limit": 20}
```
Search Google News:
```json
{"source": "news", "query": "open source llm release", "limit": 25}
```
Search public GitHub:
```json
{"source": "github", "query": "medulla rust", "limit": 15}
```
Sweep news into the KG (via `pulse_ingest`):
```json
{"source": "news", "query": "knowledge graph", "limit": 25}
```

## Gotchas
- `web` fetch returns reader-extracted text, not raw HTML — good for LLM context,
  lossy for exact markup.
- `rss` uses `pulse_list` with the **feed URL as the `channel`**, not `pulse_search`.
- `news` is discovery (headlines + snippets); follow up with a `web` `pulse_fetch`
  of an item's `url` to get the full article body.
- Keyless GitHub search is rate-limited by the public endpoint; a `github`
  credential raises the ceiling via the token backend.
- Ingestion is best-effort: no engine → `pulse_ingest` returns `ingested: null`.

## Related
- `pulselink-social-research` — Reddit/HN/X/LinkedIn/V2EX over the same server.
- `pulselink-media-transcripts` — video/audio transcription.
- `pulse_ingest` maps documents to the `pulselink` ontology (`:Document` →
  `:fromSource` `:PulseSource`).
