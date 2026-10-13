"""Single-seam resolver for Skill Knowledge Graph services per AGENTS.md Rule 58."""

from __future__ import annotations

from typing import cast

from harness.kernel.context import ServiceContext
from harness.services.skill_graph import (
    SKILL_GRAPH_KEY,
    SkillGraphService,
)
from plugins.memory_and_epistemics.skill_knowledge_graph.service import SkillGraphPlugin

# Default process-level plugin singleton
_DEFAULT_SKILL_GRAPH_PLUGIN: SkillGraphPlugin | None = None


def get_default_skill_graph_plugin() -> SkillGraphPlugin:
    """Obtain or instantiate the process-level default SkillGraphPlugin singleton."""
    global _DEFAULT_SKILL_GRAPH_PLUGIN
    if _DEFAULT_SKILL_GRAPH_PLUGIN is None:
        _DEFAULT_SKILL_GRAPH_PLUGIN = SkillGraphPlugin()
    return _DEFAULT_SKILL_GRAPH_PLUGIN


def resolve_skill_knowledge_graph(
    context: ServiceContext | None = None,
) -> SkillGraphService:
    """Resolve SkillGraphService from ServiceContext or fallback to process default singleton."""
    if context is not None:
        resolved = context.optional(SKILL_GRAPH_KEY)
        if resolved is not None:
            return cast(SkillGraphService, resolved)
    return get_default_skill_graph_plugin()
