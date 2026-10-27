"""PIPE-CONNSPEC-R155.4: PulseLink rapid-delivery skill contract."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "pulselink_mcp/skills/pulselink-mcp-development/SKILL.md"

pytestmark = pytest.mark.spec("PIPE-CONNSPEC-R155.4")


def test_development_skill_binds_pulselink_contract_and_package_data() -> None:
    text = SKILL.read_text()
    assert text.startswith("---\nname: pulselink-mcp-development\n")
    assert "## Rapid delivery: the 5-minute contract" in text
    assert "PIPE-CONNSPEC-R155.4" in text
    for reference in (
        "pulselink_mcp/mcp_server.py",
        "pulselink_mcp/connector_sources.py",
        "SOURCE_CREDENTIALS",
        "PULSELINK_TLS_PROFILE",
        "PULSETOOL",
        "legacy_profile: true",
        "render_connector: false",
    ):
        assert reference in text

    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    package_data = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"][
        "setuptools"
    ]["package-data"]["pulselink_mcp"]
    assert "skills/**" in package_data
    assert (ROOT / "pulselink_mcp/skills/pulselink-mcp-development/SKILL.md").is_file()
    assert not re.search(r"(?:sk-|ghp_|Bearer\s+)[A-Za-z0-9_./-]{12,}", text)
    assert project["name"] == "pulselink-mcp"
