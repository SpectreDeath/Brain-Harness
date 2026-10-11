"""Catalog scanning, edge indexing, cache invalidation, and vault linking operations."""

from __future__ import annotations

from pathlib import Path
import time
from typing import TYPE_CHECKING, Any

from harness.services.skill_graph.models import EdgeType, SkillEdge
from harness.services.skill_graph.scanner import (
    link_knowledge_vault_items,
    scan_skills_catalog,
)

if TYPE_CHECKING:
    from harness.services.skill_graph.service.registry import BuiltinSkillRegistryService


def add_edge(
    registry: BuiltinSkillRegistryService,
    source: str,
    target: str,
    relation: EdgeType,
    weight: float = 1.0,
) -> None:
    """Append directed edge and update bidirectional adjacency indices in O(1) time."""
    edge_key = (source, target, relation)
    if edge_key in registry._edge_keys:
        return
    registry._edge_keys.add(edge_key)
    edge = SkillEdge(source=source, target=target, relation=relation, weight=weight)
    registry._edges.append(edge)
    registry._adj_out[source].append(edge)
    registry._adj_in[target].append(edge)


def ensure_scanned(registry: BuiltinSkillRegistryService, root_dir: str) -> None:
    """Scan workspace directories if not yet populated or if 30s elapsed (Rule 52)."""
    now = time.time()
    if registry._skills_cache and (now - registry._last_scan_time) < 30.0:
        return

    with registry._scan_lock:
        if registry._skills_cache and (time.time() - registry._last_scan_time) < 30.0:
            return

        disc, cats, adj, synth, edges, idf = scan_skills_catalog(root_dir)

        registry._edges.clear()
        registry._edge_keys.clear()
        registry._adj_out.clear()
        registry._adj_in.clear()

        for edge in edges:
            add_edge(registry, edge.source, edge.target, edge.relation, edge.weight)

        registry._skills_cache = disc
        registry._categories = cats
        registry._adjacency = adj
        registry._synthetic_adjacency = synth
        registry._idf_table = idf
        registry._last_scan_time = now


def invalidate_cache(registry: BuiltinSkillRegistryService) -> None:
    """Invalidate scanned skills cache to force immediate re-scan on next query."""
    if getattr(registry, "_is_invalidating", False):
        return
    registry._is_invalidating = True
    try:
        registry._last_scan_time = 0.0
        registry._skills_cache.clear()
        registry._categories.clear()
        registry._adjacency.clear()
        registry._synthetic_adjacency.clear()
        registry._anti_pattern_map.clear()
        registry._edges.clear()
        registry._edge_keys.clear()
        registry._adj_out.clear()
        registry._adj_in.clear()
        registry._clustering_engine = None
        for listener in list(registry._invalidation_listeners):
            try:
                listener()
            except Exception:
                pass
    finally:
        registry._is_invalidating = False


def link_knowledge_vault(
    registry: BuiltinSkillRegistryService,
    vault_dir: Path | str = ".harness/knowledge",
) -> int:
    """Scan dual-file on-disk knowledge vault and link matching KIs to registered skills."""
    registry._ensure_scanned(registry._default_root)
    return link_knowledge_vault_items(registry._skills_cache, vault_dir=vault_dir)
