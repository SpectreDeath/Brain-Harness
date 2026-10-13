"""Entrypoint module and HarnessPlugin implementation for Skill Knowledge Graph & Registry."""

from __future__ import annotations

from plugins.memory_and_epistemics.skill_knowledge_graph.resolvers import (
    get_default_skill_graph_plugin,
    resolve_skill_knowledge_graph,
)
from plugins.memory_and_epistemics.skill_knowledge_graph.service import SkillGraphPlugin
from plugins.memory_and_epistemics.skill_knowledge_graph.tools import (
    _CLUSTERING_ENGINE,
    _GRAPH_INSTANCE,
    _ensure_indexed,
    _node_to_card_def,
    cluster_skill_graph,
    compile_execution_guidance,
    discover_emergent_capabilities,
    export_skill_graph_visual,
    find_skill_chain,
    get_clustering_engine,
    get_cross_cluster_bridges,
    get_prerequisite_closure,
    get_skill_topology,
    index_skill_catalog,
    invalidate_skill_catalog,
    intercept_skill_action,
    query_skill_router,
    select_skills_for_task,
)

# Authoritative instantiated plugin singleton (Rule 45)
plugin = SkillGraphPlugin()

__all__ = [
    "SkillGraphPlugin",
    "_CLUSTERING_ENGINE",
    "_GRAPH_INSTANCE",
    "_ensure_indexed",
    "_node_to_card_def",
    "cluster_skill_graph",
    "compile_execution_guidance",
    "discover_emergent_capabilities",
    "export_skill_graph_visual",
    "find_skill_chain",
    "get_clustering_engine",
    "get_cross_cluster_bridges",
    "get_default_skill_graph_plugin",
    "get_prerequisite_closure",
    "get_skill_topology",
    "index_skill_catalog",
    "intercept_skill_action",
    "invalidate_skill_catalog",
    "plugin",
    "query_skill_router",
    "resolve_skill_knowledge_graph",
    "select_skills_for_task",
]
