"""CONN-PULSELINK-MCP-CONNECTOR-CONTENT-R003: the pack extends only the core ontology."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.spec("CONN-PULSELINK-MCP-CONNECTOR-CONTENT-R003")

TURTLE = Path(__file__).resolve().parents[1] / "pulselink_mcp/ontology/pulselink.ttl"
CORE_NAMES = ('SourceBackend', 'fromSource')
CORE_REFERENCES = ('core:SourceBackend',)


def test_pack_declares_no_core_term() -> None:
    text = TURTLE.read_text()
    for name in CORE_NAMES:
        assert not re.search(rf"^:{name}\s", text, re.M), f"pack redeclares core term {name}"
        assert not re.search(rf"(?<![\w:]):{name}(?![\w-])", text), f"pack references :{name}"
    for reference in CORE_REFERENCES:
        assert reference in text, f"pack does not reference {reference}"
