"""Skills catalog, topology, routing, and clustering endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/api/skills")
async def get_skills_catalog_endpoint(path: str = ".") -> dict[str, Any]:
    from harness.commands.skills import index_skills_cmd

    return index_skills_cmd(path)


@router.get("/api/skills/route")
async def route_skills_endpoint(intent: str, top_k: int = 4) -> dict[str, Any]:
    from harness.commands.skills import route_skills_cmd

    return route_skills_cmd(intent, top_k=top_k)


@router.get("/api/skills/chain")
async def get_skill_chain_endpoint(start: str, target: str) -> dict[str, Any]:
    from harness.commands.skills import find_skill_chain_cmd

    return find_skill_chain_cmd(start, target)


@router.get("/api/skills/{skill_name}/topology")
async def get_skill_topology_endpoint(skill_name: str) -> dict[str, Any]:
    from harness.commands.skills import get_skill_topology_cmd

    return get_skill_topology_cmd(skill_name)


@router.get("/api/skills/clusters")
async def get_skill_clusters_endpoint(request: Request, min_cluster_size: int = 2) -> dict[str, Any]:
    adapter = request.app.state.adapter
    from harness.services.skill_clustering import SKILL_CLUSTERING_KEY
    from harness.services.skill_graph import resolve_skill_intelligence

    clustering_svc = adapter.context.optional(SKILL_CLUSTERING_KEY)
    if clustering_svc is None or not hasattr(clustering_svc, "cluster_skills"):
        clustering_svc = resolve_skill_intelligence(adapter.context)

    try:
        clusters = clustering_svc.cluster_skills(min_cluster_size=min_cluster_size)
        bridges = []
        if hasattr(clustering_svc, "get_cross_cluster_bridges"):
            bridges = clustering_svc.get_cross_cluster_bridges()
        return {
            "status": "ok",
            "total": len(clusters),
            "clusters": [
                c.model_dump() if hasattr(c, "model_dump") else c.dict()
                for c in clusters
            ],
            "bridges": [
                b.model_dump() if hasattr(b, "model_dump") else b.dict()
                for b in bridges
            ],
        }
    except Exception as e:
        logger.error("Failed to cluster skills from API", error=str(e))
        return {"status": "error", "error": str(e), "clusters": [], "bridges": []}


@router.get("/api/skills/clusters/mermaid")
async def get_skill_clusters_mermaid_endpoint(
    request: Request,
    min_cluster_size: int = 2,
) -> dict[str, Any]:
    adapter = request.app.state.adapter
    from harness.services.skill_clustering import (
        SKILL_CLUSTERING_KEY,
        generate_clustered_mermaid,
    )
    from harness.services.skill_graph import resolve_skill_intelligence

    clustering_svc = adapter.context.optional(SKILL_CLUSTERING_KEY)
    if clustering_svc is None or not hasattr(clustering_svc, "cluster_skills"):
        clustering_svc = resolve_skill_intelligence(adapter.context)

    try:
        clusters = clustering_svc.cluster_skills(min_cluster_size=min_cluster_size)
        bridges = []
        if hasattr(clustering_svc, "get_cross_cluster_bridges"):
            bridges = clustering_svc.get_cross_cluster_bridges()
        mermaid_code = generate_clustered_mermaid(clusters, bridges)
        return {"status": "ok", "mermaid": mermaid_code}
    except Exception as e:
        logger.error("Failed to generate skill cluster mermaid from API", error=str(e))
        return {
            "status": "error",
            "error": str(e),
            "mermaid": "graph TD\n  err[Failed to generate cluster graph]",
        }


__all__ = ["router"]
