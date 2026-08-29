"""Native epistemic-graph ingestion for PulseLink records.

CONCEPT:AU-KG.ingest.enterprise-source-extractor. Connector-specific mappers emit
canonical node_type nodes and relationship edges. The required agent-utilities
native-ingest primitive owns the transaction and raises NativeIngestError when the
authoritative engine cannot commit.
"""

from __future__ import annotations

import json
from typing import Any

from agent_utilities.knowledge_graph.enrichment.extractors.social import (
    extract_structured_entities,
    to_kg_rows,
)
from agent_utilities.knowledge_graph.memory.native_ingest import (
    NativeIngestError,
)
from agent_utilities.knowledge_graph.memory.native_ingest import (
    ingest_documents as _native_ingest_documents,
)
from agent_utilities.knowledge_graph.memory.native_ingest import (
    ingest_entities as _native_ingest_entities,
)
from agent_utilities.knowledge_graph.memory.native_ingest import (
    media_store as _native_media_store,
)

_SOURCE = "pulselink-mcp"
_DOMAIN = "pulselink"


def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Write canonical typed nodes and relationships through agent-utilities."""
    return _native_ingest_entities(
        entities,
        relationships,
        source=source,
        domain=domain,
        client=client,
        graph=graph,
    )


def ingest_documents(
    documents: list[dict[str, Any]],
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Write searchable documents through the authoritative native-ingest path."""
    return _native_ingest_documents(
        documents,
        source=source,
        domain=domain,
        client=client,
        graph=graph,
    )


def media_store() -> Any:
    """Return the authoritative native media store."""
    return _native_media_store()


def _present(value: Any) -> Any:
    """Pass a value through, or None if it's falsy (empty string/dict/etc.)."""
    return value or None


def _drop_none_values(d: dict[str, Any]) -> dict[str, Any]:
    """Filter out keys whose value is None, so absent fields aren't written."""
    return {k: v for k, v in d.items() if v is not None}


def _document_node(
    source: str, doc_id: str, ext: str, text: str, d: dict[str, Any]
) -> dict[str, Any]:
    """Build the :Document node payload for one mapped document."""
    metrics = d.get("metrics") or {}
    extra = d.get("extra") or {}
    node: dict[str, Any] = {
        "id": doc_id,
        "node_type": "Document",
        "title": _present(d.get("title")),
        "text": text,
        "source_uri": _present(d.get("url")),
        "permalink": _present(d.get("url")),
        "author": _present(d.get("author")),
        "created_at": _present(d.get("created_at")),
        "sourceKey": source,
        "backendName": _present(extra.get("backend")),
        "externalToolId": ext,
    }
    if metrics:
        node["engagement"] = json.dumps(metrics, ensure_ascii=False, sort_keys=True)
    return _drop_none_values(node)


def _document_entity_nodes(
    d: dict[str, Any], doc_id: str, seen_entities: set[str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Free-first deterministic entity extraction (CONCEPT:AU-KG.ingest.deterministic-social-entity-mining):
    mine the platform's OWN structured entities.hashtags/user_mentions/urls
    (passed through by the social backends' ``extra["entities"]``) into
    :Hashtag/:Mention/:Tool nodes, before any LLM enrichment runs on this
    document. Zero-cost, deterministic, reproducible, auditable. Dedupes new
    node ids against ``seen_entities`` (shared across the whole mapping call).
    """
    raw_entities = (d.get("extra") or {}).get("entities")
    if not raw_entities:
        return [], []
    structured = extract_structured_entities({"entities": raw_entities})
    if structured.is_empty():
        return [], []
    extra_nodes, extra_edges = to_kg_rows(structured, document_id=doc_id)
    nodes = []
    for n in extra_nodes:
        if n["id"] not in seen_entities:
            seen_entities.add(n["id"])
            nodes.append(n)
    return nodes, extra_edges


def _author_contribution(
    doc_id: str, d: dict[str, Any], seen_people: set[str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build the :Person node (deduped against ``seen_people``) + :authoredBy link, if any."""
    author = (d.get("author") or "").strip()
    if not author:
        return [], []
    pid = f"pulselink:person:{author}"
    nodes: list[dict[str, Any]] = []
    if pid not in seen_people:
        seen_people.add(pid)
        nodes.append({"id": pid, "node_type": "Person", "name": author})
    relationships = [{"source": doc_id, "target": pid, "relationship": "authoredBy"}]
    return nodes, relationships


def _map_one_document(
    source: str,
    src_id: str,
    d: dict[str, Any],
    seen_people: set[str],
    seen_entities: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Map one PulseDocument dict → (nodes, relationships); ([], []) to skip it."""
    ext = str(d.get("id") or "").strip()
    if not ext:
        return [], []
    text = d.get("text") or d.get("title")
    if not text:
        return [], []
    doc_id = f"pulselink:document:{source}:{ext}"

    nodes = [_document_node(source, doc_id, ext, text, d)]
    relationships = [
        {"source": doc_id, "target": src_id, "relationship": "fromSource"}
    ]

    entity_nodes, entity_edges = _document_entity_nodes(d, doc_id, seen_entities)
    nodes.extend(entity_nodes)
    relationships.extend(entity_edges)

    author_nodes, author_edges = _author_contribution(doc_id, d, seen_people)
    nodes.extend(author_nodes)
    relationships.extend(author_edges)

    return nodes, relationships


def _map_documents(
    source: str, documents: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Map PulseDocument dicts → (typed entity nodes, relationships).

    Emits one :PulseSource node for ``source`` plus, per document, a :Document node (text +
    provenance, linked ``:fromSource``) and — when an author is present — a :Person node
    (linked ``:authoredBy``). :Document nodes keep their type so hub-side enrichment
    chunks/embeds them.
    """
    src_id = f"pulselink:source:{source}"
    nodes: list[dict[str, Any]] = [
        {"id": src_id, "node_type": "PulseSource", "name": source, "sourceKey": source}
    ]
    relationships: list[dict[str, Any]] = []
    seen_people: set[str] = set()
    seen_entities: set[str] = set()

    for d in documents or []:
        doc_nodes, doc_relationships = _map_one_document(
            source, src_id, d, seen_people, seen_entities
        )
        nodes.extend(doc_nodes)
        relationships.extend(doc_relationships)

    return nodes, relationships


def ingest_pulse_documents(
    source: str,
    documents: list[dict[str, Any]],
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Map PulseLink result documents → :Document/:PulseSource/:Person nodes and ingest.

    ``documents`` is the ``documents`` list of a ``pulse_search``/``pulse_list`` result
    (or a single fetched doc wrapped in a list).
    """
    nodes, relationships = _map_documents(source, documents)
    # Only the lone :PulseSource node means nothing usable was mapped.
    if len(nodes) <= 1:
        raise NativeIngestError("PulseLink ingest requires at least one document")
    return ingest_entities(nodes, relationships, client=client, graph=graph)
