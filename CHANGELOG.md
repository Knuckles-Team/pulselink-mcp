# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Hosted X (Twitter) search/browse tools (`integrations/x_search_tool.py`), externalized from agent-utilities, exposing keyless X reach over the source ladder.

## [2.3.7] - 2026-10-30

### Changed
- Require `scion-sdk>=0.6.4,<0.7.0`; `uv.lock` relocked.

## [2.3.5] - 2026-10-27

### Added
- Packaged `pulselink-mcp-development` skill documenting the connector's rapid-delivery, source-ladder, security, package, and release contracts.

## [0.1.0] - 2026-06-14

### Added
- Initial release.
- Modular subfolders for API wrappers (`api/`) and action-routed MCP tools (`mcp/`).
- Material-theme mkdocs documentation site (7 standard pages).
- Full pre-commit quality gate and flat `tests/` structure.
