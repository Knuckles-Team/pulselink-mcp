"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``ingest_entities`` / ``ingest_documents`` / ``ingest_pulse_documents``
seam with a fake engine client (no engine required), asserting the txn add_node/commit +
edge calls and the PulseDocument -> :Document/:PulseSource/:Person mapping.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from typing import Any

import msgpack
import pytest
from agent_utilities.knowledge_graph.memory.native_ingest import NativeIngestError
from agent_utilities.security.brain_context import ActorContext, use_actor
from agent_utilities.models.company_brain import ActorType
from agent_utilities.knowledge_graph.core.session import GraphSession, use_session

from pulselink_mcp.kg_ingest import (
    ingest_documents,
    ingest_entities,
    ingest_pulse_documents,
)


@pytest.fixture(autouse=True)
def _governed_session():
    actor = ActorContext(
        actor_id="subject:opaque:synthetic",
        actor_type=ActorType.AUTOMATED_SERVICE,
        roles=(),
        tenant_id="tenant:opaque:synthetic",
        authenticated=True,
    )
    session = GraphSession(
        actor=actor,
        tenant=actor.tenant_id,
        scopes=frozenset({"kg:write"}),
        graph="graph:opaque:synthetic",
        policy_version="policy:opaque:synthetic",
        audience="epistemic-graph",
    )
    with use_actor(actor), use_session(session):
        yield


class _FakeNodes:
    def __init__(self) -> None:
        self.values: dict[str, dict[str, Any]] = {}

    def properties(self, node_id: str) -> dict[str, Any] | None:
        return self.values.get(node_id)

    def list(self) -> list[tuple[str, dict[str, Any]]]:
        return list(self.values.items())


class _FakeChanges:
    def __init__(self, nodes: _FakeNodes) -> None:
        self.nodes = nodes
        self.edges: list[tuple[str, str, dict[str, Any]]] = []
        self.applied: list[dict[str, Any]] = []
        self.records: dict[str, dict[str, Any]] = {}
        self.versions: dict[str, dict[str, Any]] = {}

    def get(self, envelope_id: str) -> dict[str, Any] | None:
        return self.records.get(envelope_id)

    def content_version(self, object_id: str) -> dict[str, Any] | None:
        return self.versions.get(object_id)

    def cursor(self, _source: str, _partition: str = "") -> None:
        return None

    def apply(self, envelope: dict[str, Any]) -> dict[str, Any]:
        self.applied.append(envelope)
        mutation = envelope["mutation"]
        for operation in mutation["operations"]:
            method = operation["method"]
            params = method["params"]
            properties = msgpack.unpackb(params["properties_msgpack"], raw=False)
            if method["method"] == "AddNode":
                self.nodes.values[params["node_id"]] = properties
            elif method["method"] == "AddEdge":
                self.edges.append(
                    (params["source_id"], params["target_id"], properties)
                )
        version = envelope["content_version"]
        self.versions[version["object_id"]] = version
        self.records[envelope["envelope_id"]] = envelope
        return {
            "batch_id": mutation["batch_id"],
            "replayed": False,
            "projection_pending": False,
        }


class _FakeRdf:
    def validate_shacl(self, _shapes: str, _data_graph: str) -> dict[str, Any]:
        return {"conforms": True, "results": []}


class _FakeClient:
    def __init__(self) -> None:
        self.nodes = _FakeNodes()
        self.changes = _FakeChanges(self.nodes)
        self.rdf = _FakeRdf()

    @staticmethod
    def supports(operation: str) -> bool:
        return operation == "ApplyChangeEnvelope"


def test_ingest_entities_writes_nodes_and_edges():
    c = _FakeClient()
    res = ingest_entities(
        [
            {"id": "a", "node_type": "Document", "text": "hi"},
            {"id": "b", "node_type": "PulseSource"},
        ],
        [{"source": "a", "target": "b", "relationship": "fromSource"}],
        client=c,
    )
    assert res == {"nodes": 2, "edges": 1}
    assert len(c.changes.applied) == 1
    assert set(c.nodes.values) == {"a", "b"}
    # provenance is stamped
    assert c.nodes.values["a"]["source"] == "pulselink-mcp"
    assert c.nodes.values["a"]["domain"] == "pulselink"
    assert c.changes.edges == [("a", "b", {"relationship": "fromSource"})]


def test_ingest_documents_sets_type_and_keeps_text():
    c = _FakeClient()
    res = ingest_documents(
        [{"id": "d1", "text": "body", "title": "T"}],
        client=c,
    )
    assert res == {"nodes": 1, "edges": 0}
    assert c.nodes.values["d1"]["node_type"] == "Document"
    assert c.nodes.values["d1"]["text"] == "body"


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
    res = ingest_pulse_documents("hackernews", documents, client=c)
    # 3 nodes: PulseSource + Document + Person
    assert res == {"nodes": 3, "edges": 2}
    assert c.nodes.values["pulselink:source:hackernews"]["node_type"] == "PulseSource"
    doc = c.nodes.values["pulselink:document:hackernews:42"]
    assert doc["node_type"] == "Document"
    assert doc["text"] == "the body"
    assert doc["permalink"] == "https://news.ycombinator.com/item?id=42"
    assert doc["backendName"] == "hn-algolia"
    assert doc["engagement"] == '{"points": 100}'
    assert doc["externalToolId"] == "42"
    assert c.nodes.values["pulselink:person:pg"]["node_type"] == "Person"
    assert (
        "pulselink:document:hackernews:42",
        "pulselink:source:hackernews",
        {"relationship": "fromSource"},
    ) in c.changes.edges
    assert (
        "pulselink:document:hackernews:42",
        "pulselink:person:pg",
        {"relationship": "authoredBy"},
    ) in c.changes.edges


def test_ingest_pulse_documents_dedupes_author_person():
    c = _FakeClient()
    documents = [
        {"id": "1", "text": "a", "author": "alice"},
        {"id": "2", "text": "b", "author": "alice"},
    ]
    res = ingest_pulse_documents("reddit", documents, client=c)
    # PulseSource + 2 Documents + 1 shared Person = 4 nodes; 2 fromSource + 2 authoredBy
    assert res == {"nodes": 4, "edges": 4}
    assert "pulselink:person:alice" in c.nodes.values


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
