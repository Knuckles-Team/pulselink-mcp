"""Native epistemic-graph ingestion for PulseLink documents (typed graph nodes).

CONCEPT:AU-KG.ingest.enterprise-source-extractor. PulseLink natively pushes the
open-web / social research it retrieves into the ONE epistemic-graph knowledge graph
as **typed OWL nodes** — the normalized items become shared :Document nodes (semantic
search fodder) linked to their :PulseSource and :Person author, matching the classes
``pulselink_mcp.ontology`` federates.

This is a thin mapper over the shared ingestion primitive
``agent_utilities.knowledge_graph.memory.native_ingest``. That import is GUARDED: when
the installed agent-utilities predates the primitive (or the KG stack / engine is
absent), a self-contained txn fallback over the lightweight engine client is used, and
if no engine is reachable every entry point **no-ops** (returns ``None``) — so PulseLink
keeps working with zero KG infrastructure. Node ids follow ``pulselink:<class>:<extId>``;
each entity's ``type`` matches a class in ``pulselink.ttl``.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("pulselink_mcp.kg")

_SOURCE = "pulselink-mcp"
_DOMAIN = "pulselink"
_DEFAULT_GRAPH = "__commons__"

# Prefer the shared fleet primitive; fall back to a self-contained txn path when the
# installed agent-utilities predates it.
try:  # pragma: no cover - exercised via integration, not unit fakes
    from agent_utilities.knowledge_graph.memory import native_ingest as _shared
except Exception:  # noqa: BLE001 — version skew / missing module → self-contained mode
    _shared = None  # type: ignore[assignment]


def _native_client() -> tuple[Any | None, str]:
    """Return ``(engine_client, graph_name)`` or ``(None, "")`` (self-contained fallback)."""
    try:
        from agent_utilities.knowledge_graph.core.graph_compute import (
            GraphComputeEngine,
        )
    except Exception as e:  # noqa: BLE001 — KG stack absent
        logger.debug("KG ingest unavailable (import): %s", e)
        return None, ""
    try:
        engine = GraphComputeEngine()
        client = getattr(engine, "_client", None)
        if client is None:
            return None, ""
        return client, (getattr(engine, "graph_name", None) or _DEFAULT_GRAPH)
    except Exception as e:  # noqa: BLE001 — engine unreachable
        logger.debug("KG ingest: engine unreachable: %s", e)
        return None, ""


def _write_nodes(
    client: Any,
    graph: str,
    nodes: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None,
    *,
    source: str,
    domain: str,
) -> dict[str, int] | None:
    """Self-contained txn fallback: stamp provenance, MERGE nodes, then add edges."""
    nodes = [n for n in nodes if n.get("id")]
    if not nodes:
        return None
    try:
        txn = client.txn.begin(graph=graph)
        for node in nodes:
            props = {k: v for k, v in node.items() if k != "id" and v is not None}
            props.setdefault("source", source)
            props.setdefault("domain", domain)
            client.txn.add_node(txn, node["id"], props)
        committed = client.txn.commit(txn)
    except Exception as e:  # noqa: BLE001 — engine/txn failure is non-fatal
        logger.warning("KG ingest: txn failed: %s", e)
        return None
    if not committed:
        logger.warning("KG ingest: txn not committed (conflict)")
        return None

    edges = 0
    for rel in relationships or []:
        try:
            client.edges.add(
                rel["source"], rel["target"], {"type": rel.get("type", "RELATED")}
            )
            edges += 1
        except Exception as e:  # noqa: BLE001 — pure edge link, best-effort
            logger.debug("KG ingest: edge skipped: %s", e)

    logger.info("KG ingest: wrote %d nodes, %d edges", len(nodes), edges)
    return {"nodes": len(nodes), "edges": edges}


def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Write typed OWL nodes (+ edges) into epistemic-graph.

    ``entities``: ``[{"id":..., "type":<owl:Class>, ...props}]``.
    ``relationships``: ``[{"source":id, "target":id, "type":<link>}]``.
    Returns ``{"nodes":n, "edges":m}`` or ``None``. ``client``/``graph`` may be
    injected (tests); otherwise the shared primitive (or self-contained fallback) is used.
    """
    entities = [e for e in (entities or []) if e.get("id")]
    if not entities:
        return None
    if client is None and _shared is not None:
        return _shared.ingest_entities(
            entities, relationships, source=source, domain=domain
        )
    if client is None:
        client, graph = _native_client()
    if client is None:
        return None
    return _write_nodes(
        client,
        graph or _DEFAULT_GRAPH,
        entities,
        relationships,
        source=source,
        domain=domain,
    )


def ingest_documents(
    docs: list[dict[str, Any]],
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Write text records as ``:Document`` nodes (semantic-search fodder).

    Each doc: ``{"id":..., "text":..., "title"?:..., "source_uri"?:..., ...props}``.
    Delegates to the shared primitive when available; otherwise self-contained txn.
    """
    docs = [
        d for d in (docs or []) if d.get("id") and (d.get("text") or d.get("content"))
    ]
    if not docs:
        return None
    if client is None and _shared is not None:
        return _shared.ingest_documents(docs, source=source, domain=domain)
    nodes: list[dict[str, Any]] = []
    for doc in docs:
        text = doc.get("text") or doc.get("content")
        node = {k: v for k, v in doc.items() if k != "content" and v is not None}
        node["type"] = "Document"
        node["text"] = text
        nodes.append(node)
    if client is None:
        client, graph = _native_client()
    if client is None:
        return None
    return _write_nodes(
        client, graph or _DEFAULT_GRAPH, nodes, None, source=source, domain=domain
    )


def media_store() -> Any | None:
    """Return a shared :class:`MediaStore` over a live engine, or ``None`` (no blobs → rarely used)."""
    if _shared is None:
        return None
    try:
        return _shared.media_store()
    except Exception as e:  # noqa: BLE001
        logger.debug("KG ingest: media_store unavailable: %s", e)
        return None


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
        {"id": src_id, "type": "PulseSource", "name": source, "sourceKey": source}
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
            "type": "Document",
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
        relationships.append({"source": doc_id, "target": src_id, "type": "fromSource"})

        author = (d.get("author") or "").strip()
        if author:
            pid = f"pulselink:person:{author}"
            if pid not in seen_people:
                seen_people.add(pid)
                nodes.append({"id": pid, "type": "Person", "name": author})
            relationships.append(
                {"source": doc_id, "target": pid, "type": "authoredBy"}
            )

    return nodes, relationships


def ingest_pulse_documents(
    source: str,
    documents: list[dict[str, Any]],
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Map PulseLink result documents → :Document/:PulseSource/:Person nodes and ingest.

    ``documents`` is the ``documents`` list of a ``pulse_search``/``pulse_list`` result
    (or a single fetched doc wrapped in a list). Best-effort: returns ``None`` when there
    is nothing to write or no engine is reachable.
    """
    nodes, relationships = _map_documents(source, documents)
    # Only the lone :PulseSource node means nothing usable was mapped.
    if len(nodes) <= 1:
        return None
    return ingest_entities(nodes, relationships, client=client, graph=graph)
