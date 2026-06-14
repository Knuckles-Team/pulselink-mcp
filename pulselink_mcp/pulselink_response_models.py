#!/usr/bin/python
# coding: utf-8
"""Pydantic response models for PulseLink MCP API payloads."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class SystemStatusResponse(BaseModel):
    """Response model for system status queries."""

    status: Optional[str] = Field(default=None, description="Service status string.")
    raw: Optional[Dict[str, Any]] = Field(
        default=None, description="Raw response payload."
    )
