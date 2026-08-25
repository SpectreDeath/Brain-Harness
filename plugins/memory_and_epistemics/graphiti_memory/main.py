"""Graphiti Memory Plugin and HarnessPlugin Service Implementation."""

from __future__ import annotations

from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.graphiti import (
    EntityResult,
    EpisodeResult,
    FactResult,
    GRAPHITI_MEMORY_KEY,
    GraphitiService,
    GraphitiStatusResult,
    SearchResult,
)

from .engine import GraphitiMemoryEngine
from .models import EntityEdge, EntityNode

logger = structlog.get_logger(__name__)

# Global shared engine instance for standalone tool functions
_ENGINE_INSTANCE = GraphitiMemoryEngine()


def _get_engine() -> GraphitiMemoryEngine:
    return _ENGINE_INSTANCE


def graphiti_add_episode(
    content: str,
    group_id: str = "default",
    source_description: str | None = None,
) -> dict[str, Any]:
    """Ingest episodic interaction text into the temporal knowledge graph."""
    engine = _get_engine()
    episode, entities, edges, inv_count = engine.add_episode(
        content=content,
        group_id=group_id,
        source_description=source_description or "interaction",
    )
    return {
        "status": "ok",
        "episode_uuid": episode.uuid,
        "group_id": group_id,
        "extracted_nodes_count": len(entities),
        "extracted_edges_count": len(edges),
        "invalidated_edges_count": inv_count,
        "extracted_entities": [e.name for e in entities],
    }


def graphiti_search(
    query: str,
    group_id: str = "default",
    limit: int = 5,
    include_invalidated: bool = False,
) -> dict[str, Any]:
    """Execute tri-brid search (dense vector, BM25, BFS) with balanced merge reranking."""
    engine = _get_engine()
    ranked_edges = engine.search(
        query=query,
        group_id=group_id,
        limit=limit,
        include_invalidated=include_invalidated,
    )

    facts = []
    entity_names = set()
    for edge, score in ranked_edges:
        facts.append({
            "edge_uuid": edge.uuid,
            "source_entity": edge.source_name,
            "target_entity": edge.target_name,
            "relation_name": edge.relation_name,
            "fact": edge.fact,
            "valid_at": edge.valid_at.isoformat(),
            "invalid_at": edge.invalid_at.isoformat() if edge.invalid_at else None,
            "episodes": edge.episodes,
            "score": score,
        })
        entity_names.add(edge.source_name)
        entity_names.add(edge.target_name)

    entities = []
    for e_name in entity_names:
        node = engine.get_entity(e_name, group_id=group_id)
        if node:
            entities.append({
                "entity_uuid": node.uuid,
                "name": node.name,
                "entity_type": node.entity_type,
                "summary": node.summary,
                "attributes": node.attributes,
            })

    return {
        "status": "ok",
        "query": query,
        "group_id": group_id,
        "results_count": len(facts),
        "facts": facts,
        "entities": entities,
    }


def graphiti_get_entity(
    name_or_uuid: str,
    group_id: str = "default",
) -> dict[str, Any]:
    """Retrieve full entity node state, summaries, attributes, and relationships."""
    engine = _get_engine()
    node = engine.get_entity(name_or_uuid, group_id=group_id)
    if not node:
        return {"status": "not_found", "reason": f"Entity '{name_or_uuid}' not found."}

    edges = engine.get_entity_relations(node.uuid, group_id=group_id, include_invalidated=True)
    return {
        "status": "ok",
        "entity": {
            "entity_uuid": node.uuid,
            "name": node.name,
            "entity_type": node.entity_type,
            "summary": node.summary,
            "attributes": node.attributes,
            "created_at": node.created_at.isoformat(),
            "updated_at": node.updated_at.isoformat(),
            "relations": [
                {
                    "edge_uuid": e.uuid,
                    "source_entity": e.source_name,
                    "target_entity": e.target_name,
                    "relation_name": e.relation_name,
                    "fact": e.fact,
                    "valid_at": e.valid_at.isoformat(),
                    "invalid_at": e.invalid_at.isoformat() if e.invalid_at else None,
                }
                for e in edges
            ],
        },
    }


def graphiti_invalidate_fact(
    edge_uuid: str,
    reason: str = "Contradicted by newer evidence",
) -> dict[str, Any]:
    """Mark a fact relation edge as invalidated with a timestamped record."""
    engine = _get_engine()
    edge = engine.invalidate_fact(edge_uuid, reason=reason)
    if not edge:
        return {"status": "not_found", "reason": f"Fact edge '{edge_uuid}' not found."}

    return {
        "status": "ok",
        "edge_uuid": edge.uuid,
        "source_entity": edge.source_name,
        "target_entity": edge.target_name,
        "relation_name": edge.relation_name,
        "invalidated_at": edge.invalid_at.isoformat() if edge.invalid_at else None,
        "reason": reason,
    }


def graphiti_get_status(
    group_id: str = "default",
) -> dict[str, Any]:
    """Inspect knowledge graph memory statistics and driver backend health."""
    engine = _get_engine()
    return engine.get_status(group_id=group_id)


class GraphitiMemoryPlugin(HarnessPlugin, GraphitiService):
    """Harness Plugin implementing GraphitiService and registering GRAPHITI_MEMORY_KEY."""

    name = "plugin.graphiti_memory"
    version = "0.1.0"
    description = "Temporal knowledge graph engine with bi-temporal edge invalidation and tri-brid search reranking"
    trusted = True

    def __init__(self) -> None:
        self._engine = _get_engine()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [GRAPHITI_MEMORY_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(GRAPHITI_MEMORY_KEY, self)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # GraphitiService Protocol Implementation
    async def add_episode(
        self,
        content: str,
        group_id: str = "default",
        source_description: str | None = None,
    ) -> EpisodeResult:
        res = graphiti_add_episode(content, group_id, source_description)
        return EpisodeResult(**res)

    async def search(
        self,
        query: str,
        group_id: str = "default",
        limit: int = 5,
        include_invalidated: bool = False,
    ) -> SearchResult:
        res = graphiti_search(query, group_id, limit, include_invalidated)
        return SearchResult(
            status=res["status"],
            query=res["query"],
            group_id=res["group_id"],
            results_count=res["results_count"],
            facts=[FactResult(**f) for f in res["facts"]],
            entities=[EntityResult(**e) for e in res["entities"]],
        )

    async def get_entity(
        self,
        name_or_uuid: str,
        group_id: str = "default",
    ) -> EntityResult | None:
        res = graphiti_get_entity(name_or_uuid, group_id)
        if res.get("status") != "ok":
            return None
        ent_data = res["entity"]
        return EntityResult(
            entity_uuid=ent_data["entity_uuid"],
            name=ent_data["name"],
            entity_type=ent_data["entity_type"],
            summary=ent_data["summary"],
            attributes=ent_data["attributes"],
            created_at=ent_data["created_at"],
            updated_at=ent_data["updated_at"],
            relations=[FactResult(**r) for r in ent_data["relations"]],
        )

    async def invalidate_fact(
        self,
        edge_uuid: str,
        reason: str = "Contradicted by newer evidence",
    ) -> FactResult | None:
        res = graphiti_invalidate_fact(edge_uuid, reason)
        if res.get("status") != "ok":
            return None
        return FactResult(
            edge_uuid=res["edge_uuid"],
            source_entity=res["source_entity"],
            target_entity=res["target_entity"],
            relation_name=res["relation_name"],
            fact=f"Invalidated: {res['edge_uuid']}",
            valid_at=res["invalidated_at"],
            invalid_at=res["invalidated_at"],
        )

    async def get_status(
        self,
        group_id: str = "default",
    ) -> GraphitiStatusResult:
        res = graphiti_get_status(group_id)
        return GraphitiStatusResult(**res)
