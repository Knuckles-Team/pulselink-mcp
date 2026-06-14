#!/usr/bin/python
"""Pydantic input models for PulseLink MCP API request parameters."""


from pydantic import BaseModel, Field


class SystemStatusInput(BaseModel):
    """Input model for system status queries."""

    verbose: bool | None = Field(
        default=False, description="Return extended status details."
    )
