"""Authoritative resolution seams and singleton factories for the skill subsystem."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from harness.services.skill_graph import (
    SKILL_GRAPH_KEY,
    SKILL_REGISTRY_KEY,
    BuiltinSkillGraphService,
    BuiltinSkillRegistryService,
    SkillIntelligenceService,
    get_default_skill_graph,
    get_default_skill_registry,
    resolve_skill_intelligence,
)


def get_skill_registry(
    root_path: str | Path = ".", context: Any = None
) -> BuiltinSkillRegistryService:
    """Authoritative single-source factory seam to resolve BuiltinSkillRegistryService.

    Resolves from active IoC container context when available, falling back to
    the process-level cached registry instance (Rule 2, Rule 19, Rule 58).
    """
    if context is not None and hasattr(context, "optional"):
        reg = context.optional(SKILL_REGISTRY_KEY)
        if reg is not None and isinstance(reg, BuiltinSkillRegistryService):
            return reg
    return get_default_skill_registry(root_dir=str(root_path))


def get_skill_graph(
    root_path: str | Path = ".", context: Any = None
) -> BuiltinSkillGraphService:
    """Authoritative single-source factory seam to resolve BuiltinSkillGraphService.

    Resolves from active IoC container context when available, falling back to
    the process-level cached graph facade instance (Rule 2, Rule 19, Rule 58).
    """
    if context is not None and hasattr(context, "optional"):
        graph = context.optional(SKILL_GRAPH_KEY)
        if graph is not None and isinstance(graph, BuiltinSkillGraphService):
            return graph
    return get_default_skill_graph(root_dir=str(root_path))


def get_skill_intelligence(
    root_path: str | Path = ".", context: Any = None
) -> SkillIntelligenceService:
    """Authoritative single-source factory seam to resolve SkillIntelligenceService (Rule 1.1)."""
    return resolve_skill_intelligence(context=context, root_dir=str(root_path))


# Global default registry and graph references for 100% backward compatibility
_DEFAULT_REGISTRY = get_default_skill_registry()
_DEFAULT_GRAPH = get_default_skill_graph()
