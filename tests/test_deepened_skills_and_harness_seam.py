"""Adversarial test contract for Deepened Skill Registry, Graph, and Knowledge Vault seams."""

from __future__ import annotations

import pytest
from pathlib import Path

from harness.services.skill_graph import (
    BuiltinSkillRegistryService,
    BuiltinSkillGraphService,
    SkillCardDefinition,
)
from harness.services.storage import SQLiteStorageService


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
