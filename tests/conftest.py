import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_api_client():
    client = MagicMock()
    client.get_system_status.return_value = {"status": "OK"}
    return client
