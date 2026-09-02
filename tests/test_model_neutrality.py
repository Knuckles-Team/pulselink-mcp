"""Repository-level regression proof for model-neutral configuration."""

from __future__ import annotations

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


def test_repository_has_no_concrete_model_names_or_model_provider_fallbacks() -> None:
    documents = _repository_text()
    concrete_models = (
        "gpt" + "-4o",
        "grok" + "-4.3",
        "son" + "net",
    )
    default_markers = ("${PROVIDER" + ":-", "${MODEL_ID" + ":-")

    violations = {
        path: token
        for path, content in documents.items()
        for token in (*concrete_models, *default_markers)
        if token.casefold() in content.casefold()
    }

    assert violations == {}
