"""Tests for the BuiltinSkillRegistryService, BuiltinSkillGraphService, and SkillRegistryPlugin."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.services.skill_graph import (
    BuiltinSkillGraphService,
    BuiltinSkillRegistryService,
    SKILL_GRAPH_KEY,
    SKILL_REGISTRY_KEY,
    SkillCardDefinition,
    SkillChainResult,
    SkillRegistryPlugin,
)


@pytest.mark.unit
def test_builtin_skill_registry_discovery() -> None:
    """Test that BuiltinSkillRegistryService discovers all workspace skills."""
    registry = BuiltinSkillRegistryService()
    skills = registry.discover_all(".")
    assert len(skills) > 0

    skill_names = {s.name for s in skills}
    assert "deepen-architecture" in skill_names
    assert "crafting-skills" in skill_names


@pytest.mark.unit
def test_builtin_skill_registry_get_skill() -> None:
    """Test retrieving a single skill card definition."""
    registry = BuiltinSkillRegistryService()
    skill = registry.get_skill("deepen-architecture")
    assert skill is not None
    assert skill.name == "deepen-architecture"
    assert skill.invocation == "/deepen-architecture"
    assert len(skill.stages) > 0


@pytest.mark.unit
def test_builtin_skill_registry_route_intent() -> None:
    """Test intent routing to matching skills with confidence scores."""
    registry = BuiltinSkillRegistryService()
    res = registry.route_intent("refactor architecture seams and remove shallow modules", top_k=3)
    assert res["status"] == "ok"
    assert len(res["matches"]) > 0

    top_skill = res["matches"][0]
    assert top_skill["skill_name"] == "deepen-architecture"
    assert top_skill["confidence"] > 0.3
    assert len(res["recommended_chain"]) > 0


@pytest.mark.unit
def test_builtin_skill_registry_chain_calculation() -> None:
    """Test BFS topological chain calculation between skills."""
    registry = BuiltinSkillRegistryService()
    chain_res: SkillChainResult = registry.get_chain("mind-reader", "harness-reflector")
    assert chain_res.status == "ok"
    assert chain_res.start_skill == "mind-reader"
    assert chain_res.target_skill == "harness-reflector"
    assert len(chain_res.chain) >= 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_builtin_skill_graph_service_async() -> None:
    """Test BuiltinSkillGraphService async facade."""
    registry = BuiltinSkillRegistryService()
    graph_service = BuiltinSkillGraphService(registry=registry)

    count = await graph_service.index(".")
    assert count > 0

    chain = await graph_service.find_chain("deepen-architecture", "crafting-skills")
    assert isinstance(chain, list)
    assert len(chain) >= 2

    router_res = await graph_service.query_router("author agent instructions")
    assert router_res["status"] == "ok"

    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = Path(tmpdir) / "test_skill_graph.html"
        html_path = await graph_service.export_html_brief(str(out_file))
        assert Path(html_path).exists()
        assert Path(html_path).stat().st_size > 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_skill_registry_plugin_ioc_registration() -> None:
    """Test that SkillRegistryPlugin registers SKILL_REGISTRY_KEY and SKILL_GRAPH_KEY."""
    plugin = SkillRegistryPlugin()
    assert SKILL_REGISTRY_KEY in plugin.provides
    assert SKILL_GRAPH_KEY in plugin.provides

    ctx = ServiceContext()
    await plugin.on_load(ctx)

    reg = ctx.require(SKILL_REGISTRY_KEY)
    graph = ctx.require(SKILL_GRAPH_KEY)

    assert reg is not None
    assert graph is not None

    skills = reg.discover_all(".")
    assert len(skills) > 0
