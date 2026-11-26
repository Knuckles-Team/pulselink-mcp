---
name: pulselink-social-research
skill_type: skill
description: >-
  Keyless social and community research over the pulselink-mcp MCP server: search, list and fetch posts and threads from Reddit, Hacker News, X, LinkedIn and V2EX with no API keys. Use to gauge sentiment, surface discussions or fetch one post in full. Not for web/RSS/news or video transcripts.
license: MIT
tags: [pulselink, social, reddit, hackernews, research, mcp]
metadata:
  author: Knuckles-Team
  version: '0.1.0'
---
# PulseLink Social & Community Research

Scope: Keyless social and community research over the pulselink-mcp MCP server — search, list, and fetch posts/threads/comments from Reddit, Hacker News, X, LinkedIn and V2EX with a domain-typed tool that falls back across a backend ladder (keyless public endpoint → cookie → official API). Use when the agent must gauge sentiment, surface discussion threads, pull a subreddit/HN front page, or fetch one post in full — with no API keys required. Do NOT use for open-web pages / RSS / news (pulselink-web-news) or for video/audio transcripts (pulselink-media-transcripts).

Domain-typed, keyless reach into social and community sources — **Reddit**,
**Hacker News**, **X**, **LinkedIn**, and **V2EX** — through the pulselink-mcp
source ladder. Each source tries its highest-fidelity eligible backend first (a
keyless public endpoint), then a cookie/official backend if a credential exists, so
these tools work out of the box with zero configuration.

## When to use
- Search a source for a topic (e.g. Reddit or HN posts about a project).
- List a channel/feed: a subreddit's hot posts, HN, or a V2EX node.
- Fetch one post/thread in full (selftext, comment tree, metrics).
- Pull results straight into the knowledge graph for later semantic search.

## When NOT to use
- Open-web pages, RSS feeds, Google News → `pulselink-web-news`.
- YouTube/podcast/Bilibili transcripts → `pulselink-media-transcripts`.
- A source needing a paid API you don't have — the ladder falls back to its keyless
  backend automatically; if none exists the call errors (check `pulse_status`).

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`pulselink-mcp`** MCP server. All
social sources are **keyless by default**. Cookie/official backends light up only
when a credential is present via the shared credential provider:

| Variable | Required | Notes |
|----------|----------|-------|
| `SOURCE_CREDENTIALS` / provider store | optional | Enables auth backends (reddit OAuth, X API/cookie, LinkedIn cookie); keyless works without it |

## Steps

1. Check which backends are live by calling `pulse_status`. Verify each wanted source (`reddit`, `hackernews`, `x`, `linkedin`, `v2ex`) lists a usable backend.
2. Discover content by calling `pulse_search` with `source` and `query`, or `pulse_list` with `source` and `channel`. Verify the result has documents with `id`, `title` and `url`.
3. Read one item in full by calling `pulse_fetch` with `source` and the `target` URL or id. Verify `text` and `metrics` are present.
4. Page further by passing the returned `next_cursor` to the same search or list call. Verify a different first `id` comes back.
5. Optionally persist results by calling `pulse_ingest` with `source` and `query`. Verify `ingested` reports `{nodes, edges}` rather than `null`.

## Failure recovery

| Failure | Cause | Recovery |
|---------|-------|----------|
| Reddit call returns 403 | Keyless endpoint blocked by anti-bot limits | Add a `reddit` entry to `SOURCE_CREDENTIALS` so the OAuth backend is used, then re-check `pulse_status` |
| `x` or `linkedin` returns nothing or errors | No cookie or API credential, so the auth backend stays dark | Supply the credential through `SOURCE_CREDENTIALS`, or switch to `reddit`/`hackernews` which work keyless |
| Search or list call is rejected | `query` was sent to `pulse_list` or `channel` to `pulse_search` | Use `pulse_search` with `query`, or `pulse_list` with `channel` (a subreddit is a channel) |

## Tools
| Tool | What it does |
|------|--------------|
| `pulse_search` | Search a `source` for a `query` (paginated by `cursor`, `limit`). |
| `pulse_list` | List a `channel` within a `source` (subreddit, HN, V2EX node). |
| `pulse_fetch` | Fetch one item in full by URL or source-native id. |
| `pulse_status` | Per-source backend + credential health (the doctor). |
| `pulse_ingest` | Search/list then push the documents into the KG as `:Document` nodes. |

The same operations are also served as client-method tools that take the same arguments:
`pulselink_search`, `pulselink_fetch`, `pulselink_list_items`, `pulselink_transcribe`,
`pulselink_status` and `pulselink_sources` (the list of source names).

Valid `source` values here: `reddit`, `hackernews`, `x`, `linkedin`, `v2ex`.
Returned documents are flat: `id`, `title`, `url`, `text`, `author`, `created_at`,
`metrics` (points/score/comments/replies), plus `next_cursor` for the next page.

## Recipes
Search Hacker News:
```json
{"source": "hackernews", "query": "rust async runtime", "limit": 20}
```
List a subreddit's hot posts:
```json
{"source": "reddit", "channel": "rust", "limit": 25}
```
Fetch one Reddit thread in full:
```json
{"source": "reddit", "target": "https://www.reddit.com/r/rust/comments/abc123/"}
```
Search + ingest into the KG in one step:
```json
{"source": "hackernews", "query": "vector database", "limit": 25}
```
(via `pulse_ingest`; `ingested` reports `{nodes, edges}` or `null` with no engine.)

## Gotchas
- `pulse_search` needs a `query`; `pulse_list` needs a `channel` — they are not
  interchangeable (a subreddit is a channel, not a query).
- Reddit's keyless `.json` endpoints can `403` under heavy anti-bot load; supply a
  `reddit` credential to promote the OAuth backend, or retry.
- `x`/`linkedin` keyless coverage is thin — check `pulse_status` before relying on
  them; without a cookie/API credential their auth backends stay dark.
- `created_at` shape varies by source (ISO string vs epoch) — treat it as opaque.
- Ingestion is best-effort: a missing engine makes `pulse_ingest` return
  `ingested: null`, never an error.

## Related
- `pulselink-web-news` — open web, RSS, and news over the same server.
- `pulselink-media-transcripts` — video/audio transcription.
- `pulse_ingest` maps documents to the `pulselink` ontology (`:Document` →
  `:fromSource` `:PulseSource`, `:authoredBy` `:Person`).
