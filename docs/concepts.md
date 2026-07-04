# Concept Registry — pulselink-mcp

> **Prefix**: `CONCEPT:PULSE-*`
> **Version**: 0.1.0
> **Bridge**: [`CONCEPT:AU-ECO.messaging.native-backend-abstraction`](https://github.com/Knuckles-Team/agent-utilities/blob/main/docs/concepts.md) (Unified Toolkit Ingestion)

---

## Project-Specific Concepts

| Concept ID | Name | Description |
|------------|------|-------------|
| `CONCEPT:PK-OS.governance.search-fetch-list-transcribe` | Source-fallback ladder + doctor | Multi-backend ladder per source (keyless → cookie → official), `pulse_*` tools, `pulse_status` doctor |
| `CONCEPT:PK-OS.governance.web-syndication-sources` | Web & syndication sources | Generic web (Jina Reader), RSS/Atom, Google News — keyless |
| `CONCEPT:PK-OS.governance.community-discussion-sources` | Community & discussion sources | Hacker News, Reddit (public + OAuth), V2EX |
| `CONCEPT:PK-OS.governance.developer-semantic-search-sources` | Developer & semantic-search sources | GitHub (public + token), Exa |
| `CONCEPT:PK-OS.governance.audio-video-sources-transcript` | Audio/video transcript sources | YouTube (yt-dlp), podcasts (Whisper) |
| `CONCEPT:PK-OS.governance.x-search-browse-tools` | Social sources (auth-laddered) | X/Twitter (API + cookie), LinkedIn |
| `CONCEPT:PK-OS.governance.china-platform-sources` | China-platform sources | Bilibili, Xiaohongshu, Xueqiu |

## Cross-Project References (from agent-utilities)

| Concept ID | Name | Origin |
|------------|------|--------|
| `CONCEPT:AU-ECO.messaging.native-backend-abstraction` | Unified Toolkit Ingestion | agent-utilities |
| `CONCEPT:AU-ECO.connector.mcp-tool-connector` | PulseLink open-web/social source family | agent-utilities (mcp_tool presets) |
| `CONCEPT:AU-AHE.harness.overnight-loop-driver` | Multi-backend source-fallback ladder | agent-utilities |
| `CONCEPT:AU-OS.deployment.universal-outbound-credentialprovider` | Universal CredentialProvider | agent-utilities |
| `CONCEPT:AU-OS.config.source-credential-registry` | Typed source-credential registry | agent-utilities |
