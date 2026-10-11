"""Single-seam IoC resolution and singleton factories for Skill Intelligence and Graph services."""

from __future__ import annotations

import threading
from typing import Any

from harness.services.skill_graph.adapter import SkillIntelligenceAdapter
from harness.services.skill_graph.protocols import (
    SKILL_INTELLIGENCE_KEY,
    SKILL_REGISTRY_KEY,
    SkillIntelligenceService,
)
from harness.services.skill_graph.service.graph import BuiltinSkillGraphService
from harness.services.skill_graph.service.registry import BuiltinSkillRegistryService

_DEFAULT_REGISTRY: BuiltinSkillRegistryService | None = None
_DEFAULT_GRAPH: BuiltinSkillGraphService | None = None
_INIT_LOCK = threading.Lock()


def get_default_skill_registry(root_dir: str = ".") -> BuiltinSkillRegistryService:
    """Retrieve or construct the process-level default BuiltinSkillRegistryService singleton."""
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        with _INIT_LOCK:
            if _DEFAULT_REGISTRY is None:
                _DEFAULT_REGISTRY = BuiltinSkillRegistryService(default_root=root_dir)
    return _DEFAULT_REGISTRY


def get_default_skill_graph(root_dir: str = ".") -> BuiltinSkillGraphService:
    """Retrieve or construct the process-level default BuiltinSkillGraphService singleton."""
    global _DEFAULT_GRAPH
    if _DEFAULT_GRAPH is None:
        with _INIT_LOCK:
            if _DEFAULT_GRAPH is None:
                reg = get_default_skill_registry(root_dir=root_dir)
                _DEFAULT_GRAPH = BuiltinSkillGraphService(registry=reg)
    return _DEFAULT_GRAPH


def resolve_skill_intelligence(context: Any = None, root_dir: str = ".") -> SkillIntelligenceService:
    """Authoritative single-source factory seam to resolve SkillIntelligenceService (Rule 58)."""
    if context is not None and hasattr(context, "optional"):
        intel = context.optional(SKILL_INTELLIGENCE_KEY)
        if intel is not None:
            return intel if isinstance(intel, SkillIntelligenceService) else SkillIntelligenceAdapter(intel)
        reg = context.optional(SKILL_REGISTRY_KEY)
        if reg is not None:
            return reg if isinstance(reg, SkillIntelligenceService) else SkillIntelligenceAdapter(reg)
        from harness.services.skill_clustering import SKILL_CLUSTERING_KEY

        clust = context.optional(SKILL_CLUSTERING_KEY)
        if clust is not None:
            return clust if isinstance(clust, SkillIntelligenceService) else SkillIntelligenceAdapter(clust)

    return get_default_skill_registry(root_dir=root_dir)
