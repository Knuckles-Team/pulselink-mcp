# Concept Registry — pulselink-mcp

> **Prefix**: `CONCEPT:PULSE-*`
> **Version**: 0.1.0
> **Bridge**: [`CONCEPT:ECO-4.0`](https://github.com/Knuckles-Team/agent-utilities/blob/main/docs/concepts.md) (Unified Toolkit Ingestion)

---

## Project-Specific Concepts

| Concept ID | Name | Description |
|------------|------|-------------|
| `CONCEPT:PULSE-001` | Source-fallback ladder + doctor | Multi-backend ladder per source (keyless → cookie → official), `pulse_*` tools, `pulse_status` doctor |
| `CONCEPT:PULSE-002` | Web & syndication sources | Generic web (Jina Reader), RSS/Atom, Google News — keyless |
| `CONCEPT:PULSE-003` | Community & discussion sources | Hacker News, Reddit (public + OAuth), V2EX |
| `CONCEPT:PULSE-004` | Developer & semantic-search sources | GitHub (public + token), Exa |
| `CONCEPT:PULSE-005` | Audio/video transcript sources | YouTube (yt-dlp), podcasts (Whisper) |
| `CONCEPT:PULSE-006` | Social sources (auth-laddered) | X/Twitter (API + cookie), LinkedIn |
| `CONCEPT:PULSE-007` | China-platform sources | Bilibili, Xiaohongshu, Xueqiu |

## Cross-Project References (from agent-utilities)

| Concept ID | Name | Origin |
|------------|------|--------|
| `CONCEPT:ECO-4.0` | Unified Toolkit Ingestion | agent-utilities |
| `CONCEPT:ECO-4.46` | PulseLink open-web/social source family | agent-utilities (mcp_tool presets) |
| `CONCEPT:ECO-4.47` | Multi-backend source-fallback ladder | agent-utilities |
| `CONCEPT:OS-5.38` | Universal CredentialProvider | agent-utilities |
| `CONCEPT:OS-5.39` | Typed source-credential registry | agent-utilities |
