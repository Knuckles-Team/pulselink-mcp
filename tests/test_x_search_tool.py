"""Tests for X Search & Browsing Tools (externalized from agent-utilities).

CONCEPT:PULSE-006 — Social sources (X via xAI/Grok index)
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic_ai import RunContext

from pulselink_mcp.integrations.x_search_tool import (
    _normalize_handles,
    _parse_iso_date,
    _validate_date_range,
    browse_x_post,
    x_search,
)

_AUTH = "pulselink_mcp.integrations.x_search_tool.XaiAuthManager"


class TestXSearchToolHelpers:
    """Tests for helper functions within x_search_tool."""

    def test_normalize_handles(self):
        """Should clean and normalize X handles and enforce limits."""
        handles = ["@gkisokay", "elonmusk ", None, " @jack"]
        cleaned = _normalize_handles(handles, "test_field")
        assert cleaned == ["gkisokay", "elonmusk", "jack"]

        many_handles = [f"user{i}" for i in range(11)]
        with pytest.raises(ValueError) as exc_info:
            _normalize_handles(many_handles, "test_field")
        assert "supports at most 10 handles" in str(exc_info.value)

    def test_parse_iso_date(self):
        """Should parse valid date string or raise ValueError."""
        d = _parse_iso_date("2026-05-21", "test_date")
        assert (d.year, d.month, d.day) == (2026, 5, 21)
        with pytest.raises(ValueError) as exc_info:
            _parse_iso_date("invalid-date", "test_date")
        assert "must be YYYY-MM-DD" in str(exc_info.value)

    def test_validate_date_range(self):
        """Should validate standard chronological date ranges."""
        _validate_date_range("2026-05-01", "2026-05-21")
        with pytest.raises(ValueError) as exc_info:
            _validate_date_range("2026-05-21", "2026-05-01")
        assert "must be on or before" in str(exc_info.value)


class TestXSearchToolsExecution:
    """Tests for tools execution logic under simulated run context."""

    @pytest.fixture
    def mock_context(self):
        ctx = MagicMock(spec=RunContext)
        ctx.deps = MagicMock()
        return ctx

    @patch(_AUTH)
    @patch("httpx.Client")
    @pytest.mark.asyncio
    async def test_x_search_missing_credentials(
        self, mock_client_cls, mock_auth_cls, mock_context
    ):
        mock_auth = MagicMock()
        mock_auth.resolve_credentials.return_value = None
        mock_auth_cls.return_value = mock_auth

        result = await x_search(mock_context, query="AI agents")
        payload = json.loads(result)
        assert payload["success"] is False
        assert "xAI credentials are not configured" in payload["error"]
        mock_auth.resolve_credentials.assert_called_once_with(auto_login=True)

    @patch(_AUTH)
    @patch("httpx.Client")
    @pytest.mark.asyncio
    async def test_x_search_success(self, mock_client_cls, mock_auth_cls, mock_context):
        mock_auth = MagicMock()
        mock_auth.resolve_credentials.return_value = "mock_token_123"
        mock_auth_cls.return_value = mock_auth

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output_text": "Grok result text: This is content retrieved from X search.",
            "citations": [],
        }
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = await x_search(mock_context, query="Grok")
        payload = json.loads(result)
        assert payload["success"] is True
        assert "Grok result text" in payload["answer"]

    @patch(_AUTH)
    @patch("httpx.Client")
    @pytest.mark.asyncio
    async def test_browse_x_post_success(
        self, mock_client_cls, mock_auth_cls, mock_context
    ):
        mock_auth = MagicMock()
        mock_auth.resolve_credentials.return_value = "mock_token_123"
        mock_auth_cls.return_value = mock_auth

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output_text": "Detailed post content: Grok search for this post status 123456789.",
            "citations": [],
        }
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = await browse_x_post(
            mock_context, url="https://x.com/i/status/123456789"
        )
        payload = json.loads(result)
        assert payload["success"] is True
        assert "Detailed post content" in payload["answer"]

    @pytest.mark.asyncio
    async def test_browse_x_post_invalid_url(self, mock_context):
        result = await browse_x_post(mock_context, url="https://x.com/username")
        payload = json.loads(result)
        assert payload["success"] is False
        assert "Invalid X post URL format" in payload["error"]

    @patch(_AUTH)
    @patch("httpx.Client")
    @pytest.mark.asyncio
    async def test_x_search_auto_login_success(
        self, mock_client_cls, mock_auth_cls, mock_context
    ):
        mock_auth = MagicMock()
        mock_auth.resolve_credentials.side_effect = lambda auto_login=False: (
            "auto_login_key" if auto_login else None
        )
        mock_auth_cls.return_value = mock_auth

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output_text": "AI agents are revolutionary.",
            "citations": [],
        }
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = await x_search(mock_context, query="AI agents")
        payload = json.loads(result)
        assert payload["success"] is True
        assert "AI agents are revolutionary." in payload["answer"]
        mock_auth.resolve_credentials.assert_called_once_with(auto_login=True)
