"""Adversarial test contract for Deepened Skill Registry, Graph, and Knowledge Vault seams."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.services.skill_graph import BuiltinSkillRegistryService


@pytest.mark.unit
class TestDeepenedSkillsAndHarnessSeam:
    @pytest.fixture
    def workspace_root(self) -> str:
        return str(Path(__file__).parent.parent)

    def test_skill_registry_eliminates_self_loops(self, workspace_root: str) -> None:
        """Adversarial assertion: No skill may ever declare a dependency on itself (Seam S-01)."""
        registry = BuiltinSkillRegistryService(default_root=workspace_root)
        skills = registry.discover_all(workspace_root)
        assert len(skills) > 0

        for skill in skills:
            assert skill.name not in skill.dependencies, f"Self-loop detected in {skill.name}!"
            assert skill.name not in registry._adjacency.get(skill.name, set()), f"Self-loop in adjacency: {skill.name}"

    def test_skill_registry_extracts_all_slash_dependencies(self, workspace_root: str) -> None:
        """Adversarial assertion: Explicit /slash-commands in SKILL.md must be parsed as dependencies (Seam S-02)."""
        registry = BuiltinSkillRegistryService(default_root=workspace_root)
        auditor = registry.get_skill("deep-repo-auditor")
        assert auditor is not None

        # In deep-repo-auditor/SKILL.md, it explicitly references /repo-reader and /data-topology-mapper
        assert "repo-reader" in auditor.dependencies
        assert "data-topology-mapper" in auditor.dependencies

        forge = registry.get_skill("repo-to-plugin-forge")
        assert forge is not None
        assert "epistemic-isnad-audit" in forge.dependencies

    def test_skill_registry_links_knowledge_vault(self, workspace_root: str) -> None:
        """Adversarial assertion: Knowledge Vault KIs must cross-link into SkillCardDefinitions (Seam S-03)."""
        registry = BuiltinSkillRegistryService(default_root=workspace_root)
        registry.discover_all(workspace_root)

        # Connect knowledge vault
        kv_path = Path(workspace_root) / ".harness" / "knowledge"
        synced = registry.link_knowledge_vault(kv_path)
        assert synced > 0

        # Verify a skill now has linked knowledge items
        reflector = registry.get_skill("harness-reflector")
        assert reflector is not None
        assert hasattr(reflector, "knowledge_items")
        assert len(reflector.knowledge_items) > 0

    def test_ensure_scanned_avoids_crawling_venvs(self, workspace_root: str) -> None:
        """Adversarial assertion: Workspace scanning must ignore .harness/venvs and .venv (Seam S-04)."""
        registry = BuiltinSkillRegistryService(default_root=workspace_root)
        skills = registry.discover_all(workspace_root)

        for s in skills:
            assert "venvs" not in s.skill_path.lower()
            assert ".venv" not in s.skill_path.lower()

    def test_canonical_pipeline_precedence_single_sourced(self) -> None:
        """Adversarial assertion: Pipeline precedence must be single-sourced and shared across modules."""
        from harness.services import (
            CANONICAL_PIPELINE_PRECEDENCE as PRECEDENCE_SERVICES,
        )
        from harness.services.skill_graph import (
            CANONICAL_PIPELINE_PRECEDENCE as PRECEDENCE_CORE,
        )
        from plugins.memory_and_epistemics.skill_knowledge_graph.graph import (
            CANONICAL_PIPELINE_PRECEDENCE as PRECEDENCE_PLUGIN,
        )

        assert PRECEDENCE_CORE is PRECEDENCE_SERVICES
        assert PRECEDENCE_CORE is PRECEDENCE_PLUGIN
        assert len(PRECEDENCE_CORE) >= 11
        assert ("codebase-design", "deepen-architecture") in PRECEDENCE_CORE
        assert ("deepen-architecture", "crafting-skills") in PRECEDENCE_CORE

    def test_invalidation_listener_synchronization(self, workspace_root: str) -> None:
        """Adversarial assertion: Cache invalidation on registry triggers registered listeners."""
        registry = BuiltinSkillRegistryService(default_root=workspace_root)
        called = False

        def on_invalidate() -> None:
            nonlocal called
            called = True

        registry.add_invalidation_listener(on_invalidate)
        registry.discover_all(workspace_root)
        assert registry._skills_cache

        registry.invalidate_cache()
        assert called is True
        assert len(registry._skills_cache) == 0

        # Unregister listener
        called = False
        registry.remove_invalidation_listener(on_invalidate)
        registry.invalidate_cache()
        assert called is False

    @pytest.mark.asyncio
    async def test_swarm_coordinator_typed_skill_resolution(self, workspace_root: str) -> None:
        """Adversarial assertion: SwarmCoordinator resolves skills through typed ServiceKey contracts."""
        from harness.agent.swarm import SwarmCoordinator
        from harness.kernel.context import ServiceContext
        from harness.services.skill_clustering import SKILL_CLUSTERING_KEY
        from harness.services.skill_graph import (
            SKILL_REGISTRY_KEY,
            BuiltinSkillRegistryService,
        )

        ctx = ServiceContext()
        registry = BuiltinSkillRegistryService(default_root=workspace_root)
        ctx.provide(SKILL_REGISTRY_KEY, registry)
        ctx.provide(SKILL_CLUSTERING_KEY, registry)

        coordinator = SwarmCoordinator(context=ctx)
        dag = coordinator.decompose_with_skills(
            objective="Deepen codebase architecture and craft summary cards",
            top_k=3,
        )

        assert dag is not None
        assert len(dag.nodes) > 0
        node_roles = [node.role for node in dag.nodes.values()]
        assert len(node_roles) > 0

        # Also test explicit skill_names routing
        dag_explicit = coordinator.decompose_with_skills(
            objective="Deepen codebase architecture",
            skill_names=["deepen-architecture", "crafting-skills"],
        )
        assert dag_explicit is not None
        assert len(dag_explicit.nodes) > 0
        explicit_roles = [node.role for node in dag_explicit.nodes.values()]
        assert any("deepen-architecture" in r for r in explicit_roles)
        assert any("crafting-skills" in r for r in explicit_roles)

