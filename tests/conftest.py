from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_api_client():
    client = MagicMock()
    client.get_system_status.return_value = {"status": "OK"}
    return client
