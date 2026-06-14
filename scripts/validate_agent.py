#!/usr/bin/env python3
"""Smoke-validate the A2A agent server entry point."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from pulselink_mcp.agent_server import agent_server  # noqa: F401
except ImportError as e:
    print(f"Agent import failed: {e}")
    sys.exit(1)

print("Agent entry point import OK")
