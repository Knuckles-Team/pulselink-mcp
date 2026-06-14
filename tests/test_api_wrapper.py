from unittest.mock import MagicMock, patch

from pulselink_mcp.api import ApiClientBase


def test_request_returns_json():
    client = ApiClientBase(base_url="http://localhost", token="t")
    response = MagicMock()
    response.json.return_value = {"ok": True}
    with patch.object(client.session, "request", return_value=response):
        assert client.request("GET", "/health") == {"ok": True}
