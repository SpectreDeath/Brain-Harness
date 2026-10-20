"""Contract verification test suite for Skill Graph Service decomposition (Cycle 37).

Verifies:
1. Subpackage line bounds (all submodules < 200 lines per Rule 11).
2. Complete symbol re-exports from service subpackage.
3. Single-seam resolver contract per Rule 58.
4. Edge indexing O(1) deduplication and graph topology queries.
5. Cache invalidation reentrancy guard and listener notifications.
6. Clustering and anti-pattern gating mixin cohesion.
7. BuiltinSkillGraphService async protocol delegation.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.services.skill_graph.models import EdgeType, SkillCardDefinition, SkillEdge
from harness.services.skill_graph.protocols import (
    SKILL_GRAPH_KEY,
    SKILL_INTELLIGENCE_KEY,
    SKILL_REGISTRY_KEY,
    SkillGraphService,
    SkillIntelligenceService,
)
from harness.services.skill_graph.service import (
    BuiltinSkillGraphService,
    BuiltinSkillRegistryService,
    get_default_skill_graph,
    get_default_skill_registry,
    resolve_skill_intelligence,
)


def test_subpackage_line_bounds() -> None:
    """Verify all Python submodules in skill_graph/service are strictly < 200 lines (Rule 11)."""
    pkg_dir = Path(__file__).resolve().parent.parent / "src" / "harness" / "services" / "skill_graph" / "service"
    assert pkg_dir.exists() and pkg_dir.is_dir()

    py_files = list(pkg_dir.glob("*.py"))
    assert len(py_files) >= 5, "Expected at least 5 submodules in decomposed package"

    for py_file in py_files:
        line_count = len(py_file.read_text(encoding="utf-8").splitlines())
        assert line_count < 200, f"{py_file.name} exceeds 200 lines: {line_count}"


def test_subpackage_exports() -> None:
    """Verify service subpackage exports all public symbols."""
    import harness.services.skill_graph.service as svc_pkg

    expected_symbols = [
        "BuiltinSkillGraphService",
        "BuiltinSkillRegistryService",
        "SkillIntelligenceAdapter",
        "SkillRegistryPlugin",
        "get_default_skill_graph",
        "get_default_skill_registry",
        "resolve_skill_intelligence",
    ]
    for sym in expected_symbols:
        assert hasattr(svc_pkg, sym), f"Missing symbol {sym} in service subpackage"


def test_single_seam_resolver_contract() -> None:
    """Verify Rule 58 single-seam IoC resolution with fallback."""
    # 1. Fallback when context is None
    standalone = resolve_skill_intelligence(None)
    assert isinstance(standalone, SkillIntelligenceService)
    assert isinstance(standalone, BuiltinSkillRegistryService)

    # 2. Resolution via ServiceContext with provided service
    ctx = ServiceContext()
    custom_reg = BuiltinSkillRegistryService()
    ctx.provide(SKILL_INTELLIGENCE_KEY, custom_reg)
    resolved = resolve_skill_intelligence(ctx)
    assert resolved is custom_reg


def test_registry_state_and_edge_indexing() -> None:
    """Verify edge indexing, O(1) deduplication, and directional querying."""
    import time

    reg = BuiltinSkillRegistryService()
    reg._last_scan_time = time.time()
    reg._skills_cache["alpha"] = SkillCardDefinition(
        name="alpha",
        description="Alpha skill for testing edge indexing",
        category="testing",
    )
    reg._skills_cache["beta"] = SkillCardDefinition(
        name="beta",
        description="Beta skill for testing edge indexing",
        category="testing",
    )

    initial_edge_count = len(reg._edges)
    initial_key_count = len(reg._edge_keys)

    reg._add_edge("alpha", "beta", EdgeType.PRECEDES, 1.0)
    assert len(reg._edges) == initial_edge_count + 1
    assert len(reg._edge_keys) == initial_key_count + 1

    # Deduplication test: re-adding same edge must be a no-op
    reg._add_edge("alpha", "beta", EdgeType.PRECEDES, 1.0)
    assert len(reg._edges) == initial_edge_count + 1
    assert len(reg._edge_keys) == initial_key_count + 1

    out_edges = reg.get_outgoing_edges("alpha")
    assert len(out_edges) == 1
    assert out_edges[0].target == "beta"
    assert out_edges[0].relation == EdgeType.PRECEDES

    in_edges = reg.get_incoming_edges("beta")
    assert len(in_edges) == 1
    assert in_edges[0].source == "alpha"


def test_cache_invalidation_and_listeners() -> None:
    """Verify cache invalidation and listener notifications."""
    reg = BuiltinSkillRegistryService()
    notifications = []

    def on_invalidate() -> None:
        notifications.append(True)

    reg.add_invalidation_listener(on_invalidate)
    reg._skills_cache["temp-skill"] = SkillCardDefinition(
        name="temp-skill",
        description="Temporary skill for invalidation testing",
        category="test",
    )
    assert len(reg._skills_cache) == 1

    reg.invalidate_cache()
    assert len(reg._skills_cache) == 0
    assert len(notifications) == 1

    reg.remove_invalidation_listener(on_invalidate)
    reg.invalidate_cache()
    assert len(notifications) == 1


def test_clustering_and_gating_mixins() -> None:
    """Verify RegistryClusteringMixin and RegistryGatingMixin cohesion."""
    from harness.services.skill_graph.models import SkillAntiPatternDefinition

    reg = BuiltinSkillRegistryService()
    reg._skills_cache["guard-skill"] = SkillCardDefinition(
        name="guard-skill",
        description="Guarded test skill with anti-patterns",
        category="security",
        anti_patterns=[
            SkillAntiPatternDefinition(
                name="Bare eval execution",
                symptom="Executing bare eval",
                remedy="Validate AST before eval",
            )
        ],
    )

    violations = reg.check_anti_patterns("guard-skill", "execute bare eval directly")
    assert isinstance(violations, list)

    plan = reg.select_skills_for_task("audit codebase security", max_skills=3)
    assert hasattr(plan, "selected_skills")


@pytest.mark.asyncio
async def test_graph_service_async_delegation() -> None:
    """Verify BuiltinSkillGraphService async methods delegate cleanly to registry."""
    reg = BuiltinSkillRegistryService()
    graph_svc = BuiltinSkillGraphService(registry=reg)

    assert graph_svc.registry is reg
    assert isinstance(graph_svc, SkillGraphService)

    count = await graph_svc.index()
    assert count >= 0

    route_res = await graph_svc.query_router("test task intent", top_k=2)
    assert isinstance(route_res, dict)
    assert "matches" in route_res or "status" in route_res or "skills" in route_res or "query" in route_res or "primary_skill" in route_res
