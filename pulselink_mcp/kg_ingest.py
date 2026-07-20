"""Native epistemic-graph ingestion for PulseLink records.

CONCEPT:AU-KG.ingest.enterprise-source-extractor. Connector-specific mappers emit
canonical node_type nodes and relationship edges. The required agent-utilities
native-ingest primitive owns the transaction and raises NativeIngestError when the
authoritative engine cannot commit.
"""

from __future__ import annotations

import json
from typing import Any

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

    for d in documents or []:
        ext = str(d.get("id") or "").strip()
        if not ext:
            continue
        text = d.get("text") or d.get("title")
        if not text:
            continue
        doc_id = f"pulselink:document:{source}:{ext}"
        metrics = d.get("metrics") or {}
        node: dict[str, Any] = {
            "id": doc_id,
            "node_type": "Document",
            "title": d.get("title") or None,
            "text": text,
            "source_uri": d.get("url") or None,
            "permalink": d.get("url") or None,
            "author": d.get("author") or None,
            "created_at": d.get("created_at") or None,
            "sourceKey": source,
            "backendName": (d.get("extra") or {}).get("backend") or None,
            "externalToolId": ext,
        }
        if metrics:
            node["engagement"] = json.dumps(metrics, ensure_ascii=False, sort_keys=True)
        nodes.append({k: v for k, v in node.items() if v is not None})
        relationships.append({"source": doc_id, "target": src_id, "relationship": "fromSource"})

        author = (d.get("author") or "").strip()
        if author:
            pid = f"pulselink:person:{author}"
            if pid not in seen_people:
                seen_people.add(pid)
                nodes.append({"id": pid, "node_type": "Person", "name": author})
            relationships.append(
                {"source": doc_id, "target": pid, "relationship": "authoredBy"}
            )

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
