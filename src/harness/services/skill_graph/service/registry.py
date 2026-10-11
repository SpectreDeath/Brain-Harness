"""Authoritative in-memory caching Skill Registry and Knowledge Graph coordinator."""

from __future__ import annotations

import collections
from pathlib import Path
import threading
from typing import Any

from harness.services.skill_graph.models import (
    EdgeType,
    SkillCardDefinition,
    SkillChainResult,
    SkillEdge,
    SkillTopologyReport,
)
from harness.services.skill_graph.protocols import SkillIntelligenceService
from harness.services.skill_graph.service import scanner_ops
from harness.services.skill_graph.service.clustering import RegistryClusteringMixin
from harness.services.skill_graph.service.gating import RegistryGatingMixin
from harness.services.skill_graph.topology import (
    compute_skill_chain,
    compute_topology_report,
    evaluate_chain_feasibility as _eval_feasibility,
)


class BuiltinSkillRegistryService(RegistryClusteringMixin, RegistryGatingMixin, SkillIntelligenceService):
    """Authoritative in-memory caching Skill Registry and Knowledge Graph engine."""

    def __init__(self, default_root: str = ".") -> None:
        self._default_root = default_root
        self._skills_cache: dict[str, SkillCardDefinition] = {}
        self._adjacency: dict[str, set[str]] = collections.defaultdict(set)
        self._synthetic_adjacency: dict[str, set[str]] = collections.defaultdict(set)
        self._categories: set[str] = set()
        self._anti_pattern_map: dict[str, list[Any]] = collections.defaultdict(list)
        self._edges: list[SkillEdge] = []
        self._edge_keys: set[tuple[str, str, EdgeType]] = set()
        self._adj_out: dict[str, list[SkillEdge]] = collections.defaultdict(list)
        self._adj_in: dict[str, list[SkillEdge]] = collections.defaultdict(list)
        self._last_scan_time: float = 0.0
        self._clustering_engine: Any = None
        self._invalidation_listeners: list[Any] = []
        self._is_invalidating: bool = False
        self._scan_lock = threading.Lock()
        self._idf_table: dict[str, float] = {}

    @property
    def edges(self) -> list[SkillEdge]:
        self._ensure_scanned(self._default_root)
        return list(self._edges)

    def _add_edge(self, source: str, target: str, relation: EdgeType, weight: float = 1.0) -> None:
        scanner_ops.add_edge(self, source, target, relation, weight)

    def discover_all(self, root_dir: str = ".") -> list[SkillCardDefinition]:
        self._ensure_scanned(root_dir)
        return list(self._skills_cache.values())

    def get_skill(self, name: str) -> SkillCardDefinition | None:
        self._ensure_scanned(self._default_root)
        return self._skills_cache.get(name.strip().lower().replace("_", "-"))

    def get_nodes(self) -> dict[str, SkillCardDefinition]:
        self._ensure_scanned(self._default_root)
        return dict(self._skills_cache)

    def get_categories(self) -> set[str]:
        self._ensure_scanned(self._default_root)
        return set(self._categories)

    def get_outgoing_edges(self, skill_name: str) -> list[SkillEdge]:
        self._ensure_scanned(self._default_root)
        return list(self._adj_out.get(skill_name.strip().lower().replace("_", "-"), []))

    def get_incoming_edges(self, skill_name: str) -> list[SkillEdge]:
        self._ensure_scanned(self._default_root)
        return list(self._adj_in.get(skill_name.strip().lower().replace("_", "-"), []))

    def add_invalidation_listener(self, callback: Any) -> None:
        if callback not in self._invalidation_listeners:
            self._invalidation_listeners.append(callback)

    def register_invalidation_listener(self, callback: Any) -> None:
        self.add_invalidation_listener(callback)

    def remove_invalidation_listener(self, callback: Any) -> None:
        if callback in self._invalidation_listeners:
            self._invalidation_listeners.remove(callback)

    def invalidate_cache(self) -> None:
        scanner_ops.invalidate_cache(self)

    def _get_neighbors(self, node: str, *, include_synthetic: bool = False) -> set[str]:
        neighbors = set(self._adjacency.get(node, set()))
        if include_synthetic:
            neighbors.update(self._synthetic_adjacency.get(node, set()))
        return neighbors

    def evaluate_chain_feasibility(
        self, chain: list[str], context: Any = None, *, verify_prerequisites: bool = False
    ) -> tuple[bool, list[str]]:
        self._ensure_scanned(self._default_root)
        return _eval_feasibility(
            chain=chain,
            skills_cache=self._skills_cache,
            prereq_closure_fn=self.get_prerequisite_closure,
            context=context,
            verify_prerequisites=verify_prerequisites,
        )

    def get_topology(self, skill_name: str) -> SkillTopologyReport:
        self._ensure_scanned(self._default_root)
        return compute_topology_report(
            skill_name=skill_name, skills_cache=self._skills_cache, adj_out=self._adj_out, adj_in=self._adj_in
        )

    def route_intent(self, intent: str, top_k: int = 3, min_confidence: float = 0.20) -> dict[str, Any]:
        from harness.services.skill_graph.intent import route_skill_intent

        self._ensure_scanned(self._default_root)
        return route_skill_intent(
            intent=intent,
            skills_cache=self._skills_cache,
            idf_table=self._idf_table,
            chain_fn=self.get_chain,
            top_k=top_k,
            min_confidence=min_confidence,
        )

    def get_chain(
        self, start_skill: str, target_skill: str, *, fallback_direct: bool = False, include_synthetic: bool = False
    ) -> SkillChainResult:
        self._ensure_scanned(self._default_root)
        return compute_skill_chain(
            start_skill=start_skill,
            target_skill=target_skill,
            skills_cache=self._skills_cache,
            neighbors_fn=self._get_neighbors,
            fallback_direct=fallback_direct,
            include_synthetic=include_synthetic,
        )

    def _ensure_scanned(self, root_dir: str) -> None:
        scanner_ops.ensure_scanned(self, root_dir)

    def _parse_skill_directory(self, skill_dir: Path) -> SkillCardDefinition | None:
        from harness.services.skill_parser import SkillCardParser

        return SkillCardParser.parse_directory(skill_dir)

    def link_knowledge_vault(self, vault_dir: Path | str = ".harness/knowledge") -> int:
        return scanner_ops.link_knowledge_vault(self, vault_dir=vault_dir)
