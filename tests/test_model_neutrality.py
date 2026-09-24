"""Repository-level regression proof for model-neutral configuration."""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_TEXT_SUFFIXES = {
    ".cfg",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".yaml",
    ".yml",
}


def _repository_text() -> dict[Path, str]:
    documents: dict[Path, str] = {}
    for path in _ROOT.rglob("*"):
        if not path.is_file() or path.name == "uv.lock":
            continue
        if path == Path(__file__).resolve():
            # This module includes one synthetic forbidden expression to prove
            # the structural detector itself fails closed.
            continue
        if any(
            part in {".git", ".pytest_cache", ".venv", "__pycache__"}
            for part in path.parts
        ):
            continue
        if path.suffix not in _TEXT_SUFFIXES and path.name not in {".env.example"}:
            continue
        documents[path.relative_to(_ROOT)] = path.read_text(
            encoding="utf-8", errors="replace"
        )
    return documents


_MODEL_SELECTION_DEFAULT = re.compile(
    r"\$\{(?P<variable>PROVIDER|MODEL_ID):-(?P<default>[^}]+)\}"
)
_EXPLICIT_MODEL_SELECTION = re.compile(
    r"\$\{(?P<variable>PROVIDER|MODEL_ID):\?(?P<message>[^}]+)\}"
)


def test_model_default_detector_rejects_any_structural_fallback() -> None:
    synthetic_compose = "MODEL_ID=${MODEL_ID:-fallback-capability}"

    assert _MODEL_SELECTION_DEFAULT.search(synthetic_compose) is not None


# agent_server + docker/agent.compose.yml were retired fleet-wide (operator
# ruling): the PROVIDER/MODEL_ID model-selection surface this test verified
# (no silent structural default; explicit-only via the agent compose file)
# no longer exists in this repo, so the check was removed with it.


def test_documented_model_selection_is_unset_until_operator_configuration() -> None:
    env_example = _repository_text()[Path(".env.example")]

    selections = {
        variable: re.search(rf"^# {variable}=\s*(?:#.*)?$", env_example, re.MULTILINE)
        for variable in ("PROVIDER", "MODEL_ID", "XAI_SEARCH_MODEL")
    }

    assert all(match is not None for match in selections.values())
