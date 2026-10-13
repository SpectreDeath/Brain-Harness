"""Decomposition and contract verification tests for SkillKnowledgeGraph subsystem."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.services.skill_graph import (
    SKILL_CLUSTERING_KEY,
    SKILL_GRAPH_KEY,
    SKILL_INTELLIGENCE_KEY,
    SKILL_REGISTRY_KEY,
    SkillGraphService,
)
from plugins.memory_and_epistemics.skill_knowledge_graph.main import (
    SkillGraphPlugin,
    find_skill_chain,
    index_skill_catalog,
    plugin,
    query_skill_router,
    resolve_skill_knowledge_graph,
)
from plugins.memory_and_epistemics.skill_knowledge_graph.mixins import (
    ClusteringServiceMixin,
    GraphServiceMixin,
    IntelligenceServiceMixin,
    RegistryServiceMixin,
)


def test_submodule_line_counts_and_boundaries():
    """Verify all submodules in skill_knowledge_graph adhere strictly to <= 200 line limit (Rule 11)."""
    pkg_dir = Path("plugins/memory_and_epistemics/skill_knowledge_graph")
    py_files = list(pkg_dir.glob("*.py"))
    assert len(py_files) >= 8

    for py_file in py_files:
        lines = py_file.read_text(encoding="utf-8").splitlines()
        assert len(lines) <= 200, f"{py_file} exceeds 200 lines ({len(lines)})"


def test_single_seam_resolver_pattern():
    """Verify single-seam resolver resolve_skill_knowledge_graph adheres to Rule 58."""
    # 1. Fallback without context
    svc1 = resolve_skill_knowledge_graph(None)
    assert isinstance(svc1, SkillGraphService)

    # 2. Empty context fallback
    ctx = ServiceContext()
    svc2 = resolve_skill_knowledge_graph(ctx)
    assert isinstance(svc2, SkillGraphService)

    # 3. Context resolution when plugin provides service
    test_plugin = SkillGraphPlugin()
    ctx.provide(SKILL_GRAPH_KEY, test_plugin, provider="test")
    resolved = resolve_skill_knowledge_graph(ctx)
    assert resolved is test_plugin


def test_composite_plugin_mixin_inheritance():
    """Verify SkillGraphPlugin cleanly composes all 4 specialized mixins."""
    assert issubclass(SkillGraphPlugin, GraphServiceMixin)
    assert issubclass(SkillGraphPlugin, RegistryServiceMixin)
    assert issubclass(SkillGraphPlugin, ClusteringServiceMixin)
    assert issubclass(SkillGraphPlugin, IntelligenceServiceMixin)

    p = SkillGraphPlugin()
    assert callable(p.index)
    assert callable(p.find_chain)
    assert callable(p.query_router)
    assert callable(p.discover_all)
    assert callable(p.get_skill)
    assert callable(p.cluster_skills_sync)
    assert callable(p.compile_execution_guidance)


def test_plugin_module_singleton_export():
    """Verify main.py exports plugin module singleton per Rule 45."""
    assert isinstance(plugin, SkillGraphPlugin)
    assert plugin.name == "plugin.skill_knowledge_graph"
    assert SKILL_GRAPH_KEY in plugin.provides
    assert SKILL_REGISTRY_KEY in plugin.provides
    assert SKILL_CLUSTERING_KEY in plugin.provides
    assert SKILL_INTELLIGENCE_KEY in plugin.provides


def test_backward_compatible_tool_exports():
    """Verify top-level functional tools remain accessible and operative from main."""
    res_index = index_skill_catalog(".")
    assert res_index["status"] == "ok"
    assert res_index["total_nodes"] >= 4

    res_route = query_skill_router("Perform adversarial reflection", top_k=1)
    assert res_route["status"] == "ok"
    assert len(res_route["matches"]) >= 1

    res_chain = find_skill_chain("structured-data-scout", "data-topology-mapper")
    assert res_chain["status"] == "ok"
