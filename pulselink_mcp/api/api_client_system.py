from typing import Any, Dict

from .api_client_base import ApiClientBase


class ApiClientSystem(ApiClientBase):
    """System status and monitoring API operations."""

    def get_system_status(self) -> Dict[str, Any]:
        """Retrieve the status of the target system."""
        return self.request("GET", "/health")
