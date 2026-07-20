# Pulselink Web News

Keyless open-web, RSS, and news research over the pulselink-mcp MCP server — read a web page as clean text (via Jina), pull items from any RSS feed, search Google News, and query GitHub, with a backend ladder that needs no API keys. Use when the agent must fetch the readable body of a URL, monitor a feed, sweep news headlines on a topic, or search public GitHub. Do NOT use for social/community threads (pulselink-social-research) or video/audio transcripts (pulselink-media-transcripts).

# PulseLink Open-Web & News Research

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
| `MCP_TOOL_MODE` | optional | `condensed` \| `verbose` \| `both` |

The `feeds` extra (`feedparser`) improves RSS parsing when installed.

## Tools & actions
| Tool | What it does |
|------|--------------|
| `pulse_fetch` | Fetch a URL/id in full (readable web body, feed item, repo/file). |
| `pulse_search` | Search a `source` for a `query` (`news`, `github`, `web`). |
| `pulse_list` | List a `channel` — for `rss`, the feed URL is the channel. |
| `pulse_status` | Per-source backend + credential health. |
| `pulse_ingest` | Search/list then push documents into the KG. |

Valid `source` values here: `web`, `rss`, `news`, `github`. Documents are flat:
`id`, `title`, `url`, `text`, `author`, `created_at`, plus `next_cursor`.

## Recipes
Fetch a page as clean text:
```json
{"source": "web", "target": "[configured-endpoint]
```
List an RSS feed's latest items:
```json
{"source": "rss", "channel": "[configured-endpoint] "limit": 20}
```
Search Google News:
```json
{"source": "news", "query": "open source llm release", "limit": 25}
```
Search public GitHub:
```json
{"source": "github", "query": "epistemic graph rust", "limit": 15}
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
- Ingestion is authoritative: an unavailable engine makes `pulse_ingest` fail explicitly.

## Related
- `pulselink-social-research` — Reddit/HN/X/LinkedIn/V2EX over the same server.
- `pulselink-media-transcripts` — video/audio transcription.
- `pulse_ingest` maps documents to the `pulselink` ontology (`:Document` →
  `:fromSource` `:PulseSource`).
