#!/usr/bin/python
# coding: utf-8

import os

from agent_utilities.core.exceptions import AuthError, UnauthorizedError

from .api import ApiClientSystem

_client = None


def get_client() -> ApiClientSystem:
    """Get or create a singleton API client instance."""
    global _client
    if _client is None:
        base_url = os.getenv("PULSELINK_MCP_URL", "http://localhost:8080")
        token = os.getenv("PULSELINK_MCP_TOKEN", "")
        verify = os.getenv("PULSELINK_MCP_SSL_VERIFY", "True").lower() in ("true", "1", "yes")

        try:
            _client = ApiClientSystem(
                base_url=base_url,
                token=token,
                verify=verify,
            )
        except (AuthError, UnauthorizedError) as e:
            raise RuntimeError(
                f"AUTHENTICATION ERROR: The credentials provided are not valid for '{base_url}'. "
                f"Please check your PULSELINK_MCP_TOKEN and PULSELINK_MCP_URL environment variables. "
                f"Error details: {str(e)}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"AUTHENTICATION ERROR: Failed to instantiate client. "
                f"Error details: {str(e)}"
            ) from e

    return _client
