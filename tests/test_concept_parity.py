from pathlib import Path

CONCEPTS_DOC = Path(__file__).resolve().parents[1] / "docs" / "concepts.md"


def test_concepts_doc_exists():
    assert CONCEPTS_DOC.is_file()


def test_eco_bridge_present():
    assert "AU-ECO.messaging.native-backend-abstraction" in CONCEPTS_DOC.read_text(encoding="utf-8")


def test_prefix_registered():
    assert "CONCEPT:PULSE-" in CONCEPTS_DOC.read_text(encoding="utf-8")
