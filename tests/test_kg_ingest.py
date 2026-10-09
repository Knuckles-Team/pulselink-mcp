"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``ingest_entities`` / ``ingest_documents`` / ``ingest_pulse_documents``
seam against a fake ingest transport (no engine required), asserting the submitted
``SourceRecord``/``SourceRelationship`` wire objects and the PulseDocument ->
:Document/:PulseSource/:Person mapping.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from agent_connector_sdk.ingest import IngestError, KnowledgeIngest

from pulselink_mcp.kg_ingest import (
    ingest_documents,
    ingest_entities,
    ingest_pulse_documents,
)


class _FakeTransport:
    def __init__(self) -> None:
        self.requests: list[Any] = []

    async def source_status(self, connector: str, stream: str) -> Any:
        return SimpleNamespace(accepted_checkpoint=None)

    async def submit(self, request: Any) -> Any:
        self.requests.append(request)
        return SimpleNamespace(
            affected_count=len(request.records),
            relationship_count=len(request.relationships),
        )

    async def store_blob(self, data: bytes) -> str:
        raise AssertionError("this connector's ingestion carries no media")


@pytest.fixture
def ingest():
    transport = _FakeTransport()
    return KnowledgeIngest(transport, loop=None), transport


def _records_by_id(request: Any) -> dict[str, Any]:
    return {r.record_id: r for r in request.records}


def _node_type_of(record: Any) -> str:
    # mapping_reference: "manifest:<connector>#schema_mappings/<node_type>"
    return record.mapping_reference.rsplit("/", 1)[-1]


def _relationship_name_of(rel: Any) -> str:
    # relation_reference: "manifest:<connector>#resources/<type>/relations/<name>"
    return rel.relation_reference.rsplit("/", 1)[-1]


@pytest.mark.asyncio
async def test_ingest_entities_writes_nodes_and_edges(ingest):
    service, transport = ingest
    res = await ingest_entities(
        [
            {"id": "a", "node_type": "Document", "text": "hi"},
            {"id": "b", "node_type": "PulseSource"},
        ],
        [{"source": "a", "target": "b", "relationship": "fromSource"}],
        ingest=service,
    )
    assert res == {"nodes": 2, "edges": 1}
    request = transport.requests[0]
    assert set(_records_by_id(request)) == {"a", "b"}
    rel = request.relationships[0]
    assert rel.source.record_id == "a"
    assert rel.target.record_id == "b"
    assert _relationship_name_of(rel) == "fromSource"


@pytest.mark.asyncio
async def test_ingest_documents_sets_type_and_keeps_text(ingest):
    service, transport = ingest
    res = await ingest_documents(
        [{"id": "d1", "text": "body", "title": "T"}],
        ingest=service,
    )
    assert res == {"nodes": 1, "edges": 0}
    record = _records_by_id(transport.requests[0])["d1"]
    assert _node_type_of(record) == "Document"
    assert record.payload["text"] == "body"


@pytest.mark.asyncio
async def test_ingest_documents_rejects_textless_input(ingest):
    service, _transport = ingest
    with pytest.raises(IngestError, match="at least one document"):
        await ingest_documents([{"id": "d1", "title": "no text"}], ingest=service)


@pytest.mark.asyncio
async def test_ingest_pulse_documents_maps_source_person_and_links(ingest):
    service, transport = ingest
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
    res = await ingest_pulse_documents("hackernews", documents, ingest=service)
    # 3 nodes: PulseSource + Document + Person
    assert res == {"nodes": 3, "edges": 2}
    records = _records_by_id(transport.requests[0])
    assert _node_type_of(records["pulselink:source:hackernews"]) == "PulseSource"
    doc = records["pulselink:document:hackernews:42"]
    assert _node_type_of(doc) == "Document"
    assert doc.payload["text"] == "the body"
    assert doc.payload["permalink"] == "https://news.ycombinator.com/item?id=42"
    assert doc.payload["backendName"] == "hn-algolia"
    assert doc.payload["engagement"] == '{"points": 100}'
    assert doc.payload["externalToolId"] == "42"
    assert _node_type_of(records["pulselink:person:pg"]) == "Person"
    rels = {
        (rel.source.record_id, rel.target.record_id, _relationship_name_of(rel))
        for rel in transport.requests[0].relationships
    }
    assert (
        "pulselink:document:hackernews:42",
        "pulselink:source:hackernews",
        "fromSource",
    ) in rels
    assert (
        "pulselink:document:hackernews:42",
        "pulselink:person:pg",
        "authoredBy",
    ) in rels


@pytest.mark.asyncio
async def test_ingest_pulse_documents_dedupes_author_person(ingest):
    service, transport = ingest
    documents = [
        {"id": "1", "text": "a", "author": "alice"},
        {"id": "2", "text": "b", "author": "alice"},
    ]
    res = await ingest_pulse_documents("reddit", documents, ingest=service)
    # PulseSource + 2 Documents + 1 shared Person = 4 nodes; 2 fromSource + 2 authoredBy
    assert res == {"nodes": 4, "edges": 4}
    assert "pulselink:person:alice" in _records_by_id(transport.requests[0])


@pytest.mark.asyncio
async def test_ingest_pulse_documents_rejects_unusable_documents(ingest):
    service, _transport = ingest
    documents = [{"id": "", "text": "no id"}, {"id": "x", "text": ""}]
    with pytest.raises(IngestError, match="at least one document"):
        await ingest_pulse_documents("web", documents, ingest=service)


@pytest.mark.asyncio
async def test_empty_entities_is_rejected(ingest):
    service, _transport = ingest
    with pytest.raises(IngestError, match="at least one entity"):
        await ingest_entities([], ingest=service)
