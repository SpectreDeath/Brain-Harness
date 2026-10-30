"""FastAPI routes for knowledge graph inspection, visualization, and contradiction resolution."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import structlog

from harness.services.storage.vault_graph import resolve_knowledge_graph_service
from harness.services.storage.sqlite import SQLiteStorageService
from harness.services.storage.vault_html_exporter import render_html

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class ResolveContradictionRequest(BaseModel):
    ki_a: str
    ki_b: str
    action: str  # supersede | contradict | dismiss
    reason: str = ""
    vault_dir: str = ".harness/knowledge"


def _generate_domain_mermaid(graph_dict: dict[str, Any], domain_filter: str | None = None) -> str:
    nodes, edges = graph_dict.get("nodes", []), graph_dict.get("edges", [])
    if domain_filter:
        lines = ["flowchart TD", f'subgraph DOMAIN["Domain: {domain_filter}"]']
        filtered = {n["id"] for n in nodes if n.get("domain") == domain_filter or n.get("category") == domain_filter}
        for n in nodes:
            if n["id"] in filtered:
                safe_label = n["label"].replace('"', "'")[:35]
                lines.append(f'  {n["id"]}["{safe_label}"]')
        lines.append("end")
        for e in edges:
            if e["source"] in filtered and e["target"] in filtered:
                arrow = "-->" if not e.get("derived") else f'-.->|{e["type"]}|'
                lines.append(f'  {e["source"]} {arrow} {e["target"]}')
        return "\n".join(lines[:60])

    counts: dict[str, int] = {}
    for n in nodes:
        d = n.get("domain") or "general"
        counts[d] = counts.get(d, 0) + 1
    lines = ["flowchart TD"] + [f'  {d.replace("/", "_").replace("-", "_")}["{d} ({cnt} KIs)"]' for d, cnt in sorted(counts.items())]
    node_dom = {n["id"]: (n.get("domain") or "general") for n in nodes}
    links: dict[tuple[str, str], int] = {}
    for e in edges:
        s_dom, t_dom = node_dom.get(e["source"]), node_dom.get(e["target"])
        if s_dom and t_dom and s_dom != t_dom:
            links[(s_dom, t_dom)] = links.get((s_dom, t_dom), 0) + 1
    lines.extend(f'  {s.replace("/", "_").replace("-", "_")} -->|{c} links| {t.replace("/", "_").replace("-", "_")}' for (s, t), c in sorted(links.items()))
    return "\n".join(lines[:50])


@router.get("/graph")
async def get_knowledge_graph_endpoint(
    include_derived: bool = Query(True),
    domain: str | None = Query(None),
    nodes: str = Query("all"),
    vault_dir: str = Query(".harness/knowledge"),
) -> dict[str, Any]:
    """Retrieve derived knowledge graph topology, summary metrics, and domain Mermaid."""
    storage = SQLiteStorageService(":memory:")
    try:
        await storage.sync_knowledge_vault(vault_dir)
        items = await storage.list_knowledge_items()
        graph = resolve_knowledge_graph_service().derive_graph(items, nodes_filter=nodes)
        graph_dict = graph.to_dict()
        if not include_derived:
            graph_dict["edges"] = [e for e in graph_dict["edges"] if not e.get("derived")]
        if domain:
            graph_dict["nodes"] = [n for n in graph_dict["nodes"] if n.get("domain") == domain or n.get("category") == domain]
            vids = {n["id"] for n in graph_dict["nodes"]}
            graph_dict["edges"] = [e for e in graph_dict["edges"] if e["source"] in vids and e["target"] in vids]
        return {
            "status": "ok",
            "summary": graph.summary.to_dict(),
            "graph": graph_dict,
            "mermaid": _generate_domain_mermaid(graph.to_dict(), domain_filter=domain),
        }
    except Exception as e:
        logger.error("Failed to generate knowledge graph", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        storage.close()


@router.get("/graph/html", response_class=HTMLResponse)
async def get_knowledge_graph_html_endpoint(vault_dir: str = Query(".harness/knowledge")) -> str:
    """Serve standalone interactive HTML visual brief for the knowledge graph."""
    storage = SQLiteStorageService(":memory:")
    try:
        await storage.sync_knowledge_vault(vault_dir)
        items = await storage.list_knowledge_items()
        return render_html(resolve_knowledge_graph_service().derive_graph(items))
    except Exception as e:
        logger.error("Failed to render knowledge graph HTML", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        storage.close()


@router.get("/contradictions")
async def get_knowledge_contradictions_endpoint(vault_dir: str = Query(".harness/knowledge")) -> dict[str, Any]:
    """Retrieve detected contradictions between Knowledge Items."""
    storage = SQLiteStorageService(":memory:")
    try:
        await storage.sync_knowledge_vault(vault_dir)
        conflicts = await storage.audit_contradictions()
        return {
            "status": "ok",
            "total": len(conflicts),
            "contradictions": [
                {
                    "conflict_type": c.conflict_type,
                    "ki_a": c.ki_a,
                    "ki_b": c.ki_b,
                    "reason": c.reason,
                    "confidence": c.confidence,
                    "suggested_edge": c.suggested_edge,
                }
                for c in conflicts
            ],
        }
    except Exception as e:
        logger.error("Failed to audit contradictions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        storage.close()


@router.post("/contradictions/resolve")
async def resolve_knowledge_contradiction_endpoint(req: ResolveContradictionRequest) -> dict[str, Any]:
    """Resolve a contradiction by superseding, marking mutual conflict, or dismissing."""
    storage = SQLiteStorageService(":memory:")
    try:
        await storage.sync_knowledge_vault(req.vault_dir)
        item_a = await storage.get_knowledge_item(req.ki_a)
        item_b = await storage.get_knowledge_item(req.ki_b)
        if not item_a or not item_b:
            raise HTTPException(status_code=404, detail="One or both Knowledge Items not found")

        act = req.action.lower()
        if act == "supersede":
            item_a.add_edge("supersedes", item_b.id, target_kind="ki", derived=False, confidence=1.0, description=req.reason or "UI resolution")
            item_b.status, item_b.superseded_by = "SUPERSEDED", item_a.id
        elif act == "contradict":
            item_a.add_edge("contradicts", item_b.id, target_kind="ki", derived=False, confidence=1.0, description=req.reason or "UI resolution")
            item_b.add_edge("contradicts", item_a.id, target_kind="ki", derived=False, confidence=1.0, description=req.reason or "UI resolution")
            item_a.status, item_b.status = "CHALLENGED", "CHALLENGED"

        if act in ("supersede", "contradict"):
            for item in (item_a, item_b):
                await storage.save_knowledge_item(item, vault_dir=req.vault_dir)
                await storage.export_single_item(item, vault_dir=req.vault_dir)

        return {"status": "ok", "action": act, "message": f"Successfully applied '{act}' resolution"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to resolve contradiction", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        storage.close()
