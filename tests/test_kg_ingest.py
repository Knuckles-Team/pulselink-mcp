"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``ingest_entities`` / ``ingest_documents`` / ``ingest_pulse_documents``
seam with a fake engine client (no engine required), asserting the txn add_node/commit +
edge calls and the PulseDocument -> :Document/:PulseSource/:Person mapping.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

import pytest
from agent_utilities.knowledge_graph.memory.native_ingest import NativeIngestError

from pulselink_mcp.kg_ingest import (
    ingest_documents,
    ingest_entities,
    ingest_pulse_documents,
)


class _FakeTxn:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.committed = False

    def begin(self, graph=None):
        self.graph = graph
        return "txn-1"

    def add_node(self, txn, node_id, props):
        self.nodes[node_id] = props

    def add_edge(self, txn, source, target, props):
        self.edges.append((source, target, props))

    def commit(self, txn):
        self.committed = True
        return True


class _FakeClient:
    def __init__(self):
        self.txn = _FakeTxn()


def test_ingest_entities_writes_nodes_and_edges():
    c = _FakeClient()
    res = ingest_entities(
        [
            {"id": "a", "node_type": "Document", "text": "hi"},
            {"id": "b", "node_type": "PulseSource"},
        ],
        [{"source": "a", "target": "b", "relationship": "fromSource"}],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 2, "edges": 1}
    assert c.txn.committed is True
    assert set(c.txn.nodes) == {"a", "b"}
    # provenance is stamped
    assert c.txn.nodes["a"]["source"] == "pulselink-mcp"
    assert c.txn.nodes["a"]["domain"] == "pulselink"
    assert c.txn.edges == [("a", "b", {"relationship": "fromSource"})]


def test_ingest_documents_sets_type_and_keeps_text():
    c = _FakeClient()
    res = ingest_documents(
        [{"id": "d1", "text": "body", "title": "T"}],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 1, "edges": 0}
    assert c.txn.nodes["d1"]["node_type"] == "Document"
    assert c.txn.nodes["d1"]["text"] == "body"


def test_ingest_documents_rejects_textless_input():
    c = _FakeClient()
    with pytest.raises(NativeIngestError, match="at least one document"):
        ingest_documents([{"id": "d1", "title": "no text"}], client=c)


def test_ingest_pulse_documents_maps_source_person_and_links():
    c = _FakeClient()
    documents = [
        {
            "id": "42",
            "title": "Show HN: a thing",
            "text": "the body",
            "url": "https://news.ycombinator.com/item?id=42",
            "author": "pg",
            "created_at": "2026-01-01T00:00:00Z",
            "metrics": {"points": 100},
            "extra": {"backend": "hn-algolia"},
        }
    ]
    res = ingest_pulse_documents("hackernews", documents, client=c, graph="__commons__")
    # 3 nodes: PulseSource + Document + Person
    assert res == {"nodes": 3, "edges": 2}
    assert c.txn.nodes["pulselink:source:hackernews"]["node_type"] == "PulseSource"
    doc = c.txn.nodes["pulselink:document:hackernews:42"]
    assert doc["node_type"] == "Document"
    assert doc["text"] == "the body"
    assert doc["permalink"] == "https://news.ycombinator.com/item?id=42"
    assert doc["backendName"] == "hn-algolia"
    assert doc["engagement"] == '{"points": 100}'
    assert doc["externalToolId"] == "42"
    assert c.txn.nodes["pulselink:person:pg"]["node_type"] == "Person"
    assert (
        "pulselink:document:hackernews:42",
        "pulselink:source:hackernews",
        {"relationship": "fromSource"},
    ) in c.txn.edges
    assert (
        "pulselink:document:hackernews:42",
        "pulselink:person:pg",
        {"relationship": "authoredBy"},
    ) in c.txn.edges


def test_ingest_pulse_documents_dedupes_author_person():
    c = _FakeClient()
    documents = [
        {"id": "1", "text": "a", "author": "alice"},
        {"id": "2", "text": "b", "author": "alice"},
    ]
    res = ingest_pulse_documents("reddit", documents, client=c)
    # PulseSource + 2 Documents + 1 shared Person = 4 nodes; 2 fromSource + 2 authoredBy
    assert res == {"nodes": 4, "edges": 4}
    assert "pulselink:person:alice" in c.txn.nodes


def test_ingest_pulse_documents_rejects_unusable_documents():
    documents = [{"id": "", "text": "no id"}, {"id": "x", "text": ""}]
    with pytest.raises(NativeIngestError, match="at least one document"):
        ingest_pulse_documents("web", documents, client=_FakeClient())


def test_retired_node_type_alias_is_rejected():
    with pytest.raises(NativeIngestError, match="canonical node_type"):
        ingest_entities(
            [{"id": "retired", "type": "RetiredAlias"}],
            client=_FakeClient(),
        )


def test_empty_native_ingest_is_rejected():
    with pytest.raises(NativeIngestError, match="at least one entity"):
        ingest_entities([], client=_FakeClient())
