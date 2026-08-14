"""Free-first deterministic entity extraction wired into PulseLink ingestion.

CONCEPT:AU-KG.ingest.deterministic-social-entity-mining. A separate file from
``test_kg_ingest.py`` (that file is mid-migration to the ChangeEnvelope test
contract in a sibling session) so this coverage doesn't collide with it.

Exercises ``kg_ingest._map_documents`` mapping a document's platform-native
``entities`` metadata (hashtags/mentions/urls) — passed through in
``extra["entities"]`` by the social source backends — into ``:Hashtag``/
``:Mention``/``:Tool`` nodes and edges, BEFORE any LLM enrichment runs.
"""

from __future__ import annotations

from pulselink_mcp.kg_ingest import _map_documents


def _node(nodes: list[dict], node_id: str) -> dict:
    match = [n for n in nodes if n["id"] == node_id]
    assert match, f"expected node {node_id!r} in {[n['id'] for n in nodes]}"
    return match[0]


def test_map_documents_extracts_hashtags_mentions_tools_from_own_entities():
    documents = [
        {
            "id": "1001",
            "text": "Check out this new tool!",
            "url": "https://x.com/i/web/status/1001",
            "author": "alice",
            "extra": {
                "entities": {
                    "hashtags": [{"tag": "AI"}],
                    "user_mentions": [{"username": "openai"}],
                    "urls": [{"expanded_url": "https://github.com/openai/whatever"}],
                }
            },
        }
    ]

    nodes, edges = _map_documents("x", documents)

    hashtag = _node(nodes, "hashtag:ai")
    mention = _node(nodes, "mention:openai")
    tool = _node(nodes, "tool:github")
    assert hashtag["node_type"] == "Hashtag"
    assert mention["node_type"] == "Mention"
    assert tool["node_type"] == "Tool" and tool["name"] == "GitHub"

    # Deterministic, zero-LLM provenance — distinguishable from later enrichment.
    for n in (hashtag, mention, tool):
        assert n["extraction_stage"] == "deterministic"
        assert n["confidence"] == 1.0

    doc_id = "pulselink:document:x:1001"
    edge_rels = {(e["source"], e["target"], e["relationship"]) for e in edges}
    assert (doc_id, "hashtag:ai", "taggedWithHashtag") in edge_rels
    assert (doc_id, "mention:openai", "mentionsHandle") in edge_rels
    assert (doc_id, "tool:github", "referencesTool") in edge_rels


def test_map_documents_dedupes_shared_hashtag_across_documents():
    documents = [
        {"id": "1", "text": "post one", "extra": {"entities": {"hashtags": [{"tag": "AI"}]}}},
        {"id": "2", "text": "post two", "extra": {"entities": {"hashtags": [{"tag": "ai"}]}}},
    ]

    nodes, edges = _map_documents("x", documents)

    hashtag_nodes = [n for n in nodes if n["node_type"] == "Hashtag"]
    assert len(hashtag_nodes) == 1, "the same hashtag across documents must not duplicate the node"

    hashtag_edges = [e for e in edges if e["relationship"] == "taggedWithHashtag"]
    assert len(hashtag_edges) == 2, "each document still gets its own edge to the shared node"
    assert {e["source"] for e in hashtag_edges} == {
        "pulselink:document:x:1",
        "pulselink:document:x:2",
    }


def test_map_documents_without_entities_metadata_extracts_nothing_extra():
    """A document with no ``extra.entities`` (e.g. the cookie-ladder GraphQL
    path before this change, or a source that genuinely carries none) yields
    only the Document/Person/PulseSource nodes — no spurious entity nodes."""
    documents = [{"id": "1", "text": "no entities here", "author": "carol"}]

    nodes, edges = _map_documents("x", documents)

    node_types = {n["node_type"] for n in nodes}
    assert node_types == {"PulseSource", "Document", "Person"}
    assert not any(e["relationship"] == "taggedWithHashtag" for e in edges)
