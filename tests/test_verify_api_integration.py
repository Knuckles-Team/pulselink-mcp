"""Fail-closed proofs for the API-to-MCP inventory verifier."""

from __future__ import annotations

import runpy
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest

_SCRIPT_API = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts" / "verify_api_integration.py"),
    run_name="_pulselink_verify_api_integration_test",
)
_canonical_project_name = cast(
    Callable[[str], str], _SCRIPT_API["_canonical_project_name"]
)
_run_local_mode = cast(Callable[[str], None], _SCRIPT_API["_run_local_mode"])


def _pulselink_project(root: Path) -> None:
    root.joinpath("pyproject.toml").write_text(
        '[project]\nname = "pulselink-mcp"\nversion = "1.0.0"\n',
        encoding="utf-8",
    )


def test_project_identity_comes_from_canonical_metadata(tmp_path: Path) -> None:
    worktree = tmp_path / "arbitrary-worktree-name"
    worktree.mkdir()
    _pulselink_project(worktree)

    assert _canonical_project_name(str(worktree)) == "pulselink-mcp"


def test_pulselink_missing_api_discovery_fails_nonzero(tmp_path: Path) -> None:
    _pulselink_project(tmp_path)
    server = tmp_path / "pulselink_mcp" / "mcp_server.py"
    server.parent.mkdir(parents=True)
    server.write_text("def get_mcp_instance():\n    return None\n", encoding="utf-8")

    with pytest.raises(SystemExit) as stopped:
        _run_local_mode(str(tmp_path))

    assert stopped.value.code == 1


def test_pulselink_missing_canonical_client_module_fails_nonzero(
    tmp_path: Path,
) -> None:
    _pulselink_project(tmp_path)
    package = tmp_path / "pulselink_mcp"
    package.mkdir()
    package.joinpath("api_client.py").write_text(
        "class Client:\n    def search(self):\n        return None\n",
        encoding="utf-8",
    )
    package.joinpath("mcp_server.py").write_text(
        "def search_tool(client):\n    return client.search()\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as stopped:
        _run_local_mode(str(tmp_path))

    assert stopped.value.code == 1


def test_pulselink_zero_mcp_mappings_fails_positive_baseline(
    tmp_path: Path,
) -> None:
    _pulselink_project(tmp_path)
    package = tmp_path / "pulselink_mcp"
    client = package / "api" / "api_client_pulse.py"
    client.parent.mkdir(parents=True)
    methods = ("fetch", "list_items", "search", "sources", "status", "transcribe")
    client.write_text(
        "class PulseLinkClient:\n"
        + "".join(
            f"    def {method}(self):\n        return None\n" for method in methods
        ),
        encoding="utf-8",
    )
    package.joinpath("mcp_server.py").write_text(
        "def get_mcp_instance():\n    return None\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as stopped:
        _run_local_mode(str(tmp_path))

    assert stopped.value.code == 1
