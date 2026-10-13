"""Skill Knowledge Graph plugin package facade."""

from __future__ import annotations

from plugins.memory_and_epistemics.skill_knowledge_graph.graph import SkillKnowledgeGraph
from plugins.memory_and_epistemics.skill_knowledge_graph.main import (
    SkillGraphPlugin,
    plugin,
    resolve_skill_knowledge_graph,
)
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser

__all__ = [
    "SkillCardParser",
    "SkillGraphPlugin",
    "SkillKnowledgeGraph",
    "plugin",
    "resolve_skill_knowledge_graph",
]
