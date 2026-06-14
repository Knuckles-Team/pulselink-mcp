import pytest
from unittest.mock import patch

import pulselink_mcp.auth as auth_module
from pulselink_mcp.auth import get_client


def test_get_client_auth_error():
    auth_module._client = None
    with patch("pulselink_mcp.auth.ApiClientSystem") as mock_client_cls:
        mock_client_cls.side_effect = Exception("Auth Failure")
        with pytest.raises(RuntimeError) as exc_info:
            get_client()
        assert "AUTHENTICATION ERROR" in str(exc_info.value)
    auth_module._client = None
