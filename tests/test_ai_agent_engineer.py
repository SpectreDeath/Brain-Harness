"""Comprehensive unit and integration tests for ai-agent-engineer skill and knowledge vault items."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.main import (
    index_skill_catalog,
    query_skill_router,
)


@pytest.mark.unit
class TestAiAgentEngineerSkillStructure:
    """Validate skill files against deep-module craft standards and invariants."""

    @property
    def skill_dir(self) -> Path:
        return Path(__file__).parent.parent / ".agents" / "skills" / "ai-agent-engineer"

    def test_skill_validator_passes_zero_warnings(self) -> None:
        """Assert SkillValidator passes cleanly with report.valid is True."""
        assert self.skill_dir.exists(), "Skill directory does not exist"
        report = SkillValidator.validate(self.skill_dir)
        assert report.valid is True
        # Check all checks passed
        for check in report.checks:
            assert check.passed is True, f"Check failed: {check.name} - {check.message}"

    def test_card_md_single_pipe_ascii_and_schema(self) -> None:
        """Assert CARD.md satisfies Rule 37 single-pipe borders and header tags."""
        card_file = self.skill_dir / "CARD.md"
        assert card_file.exists()
        text = card_file.read_text(encoding="utf-8")

        # Must have SKILL: ai-agent-engineer
        assert "SKILL:       ai-agent-engineer" in text
        # Must have single-pipe border characters (Rule 37)
        assert "│" in text
        assert "║" not in text, "CARD.md should use single-pipe border '│' per Rule 37"
        # Must have stage progression table
        assert "| Stage | Objective |" in text

    def test_skill_md_anti_patterns_and_pillars(self) -> None:
        """Assert SKILL.md has exact anti-patterns formatting and core pillars."""
        skill_file = self.skill_dir / "SKILL.md"
        assert skill_file.exists()
        text = skill_file.read_text(encoding="utf-8")

        # Frontmatter
        assert "name: ai-agent-engineer" in text
        # Exact Anti-Patterns heading
        assert "## Anti-Patterns" in text
        # Anti-pattern list format: - **Name** — Description
        assert "- **Agent-as-Marketing** —" in text
        assert "- **Multi-Agent Swarm Vanity** —" in text
        assert "- **Missing Off-Switch** —" in text

        # Visual Brief and Mandatory Checkpoint pillars
        assert "## The Visual Brief Specification" in text
        assert "## Mandatory Checkpoint Gate" in text

    def test_patterns_catalog_reference(self) -> None:
        """Assert patterns-catalog.md lists all 60 patterns across 8 capabilities."""
        catalog_file = self.skill_dir / "references" / "patterns-catalog.md"
        assert catalog_file.exists()
        text = catalog_file.read_text(encoding="utf-8")

        # Check all 8 capabilities present
        capabilities = [
            "Perception", "Reasoning", "Planning", "Memory",
            "Tool Use", "Coordination", "Learning", "Alignment"
        ]
        for cap in capabilities:
            assert cap in text, f"Missing capability: {cap}"

        # Check sample patterns
        assert "1. **Multimodal Grounding**" in text
        assert "17. **ReAct Loop**" in text
        assert "25. **Working-Memory Manager**" in text
        assert "38. **Router/Dispatcher**" in text
        assert "53. **Constitution-Bound**" in text
        assert "60. **Off-Switch-Compatible**" in text


@pytest.mark.unit
class TestAiAgentEngineerKnowledgeVault:
    """Validate canonical dual-file Knowledge Vault items (Rule 40)."""

    @property
    def vault_dir(self) -> Path:
        return Path(__file__).parent.parent / ".harness" / "knowledge"

    @pytest.mark.parametrize("ki_id", [
        "ki_aslanyan_four_level_ladder",
        "ki_aslanyan_sixty_agent_patterns",
        "ki_aslanyan_canonical_failures_antidotes",
        "ki_njoku_dynamic_model_routing",
    ])
    def test_canonical_dual_file_ki_format(self, ki_id: str) -> None:
        """Assert each KI strictly adheres to metadata.json + summary.md (Rule 40)."""
        ki_path = self.vault_dir / ki_id
        assert ki_path.exists() and ki_path.is_dir()

        meta_path = ki_path / "metadata.json"
        summary_path = ki_path / "summary.md"
        assert meta_path.exists(), f"Missing metadata.json in {ki_id}"
        assert summary_path.exists(), f"Missing summary.md in {ki_id}"

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        assert meta["id"] == ki_id
        assert bool(meta.get("title"))
        assert bool(meta.get("category"))
        assert isinstance(meta.get("tags"), list) and len(meta["tags"]) > 0
        assert isinstance(meta.get("provenance"), list) and len(meta["provenance"]) > 0
        assert bool(meta.get("source_repo"))

        summary_text = summary_path.read_text(encoding="utf-8")
        assert f"**ID:** `{ki_id}`" in summary_text
        assert "## Executive Summary" in summary_text
        assert len(summary_text) > 500


@pytest.mark.integration
class TestAiAgentEngineerSkillRouter:
    """Test skill knowledge graph indexing and semantic routing (Rule 35)."""

    def test_semantic_router_matches_agent_engineering(self) -> None:
        skills_dir = Path(__file__).parent.parent / ".agents" / "skills"
        summary = index_skill_catalog(str(skills_dir))
        assert summary.get("status") == "ok"

        query = "How do I choose between a workflow and an agent using the 4-level ladder?"
        res = query_skill_router(query, top_k=3)
        assert res.get("status") == "ok"
        matches = res.get("matches", [])
        assert len(matches) > 0

        # Rule 35: access via match["skill_name"]
        top_skill_names = [m["skill_name"] for m in matches]
        assert "ai-agent-engineer" in top_skill_names
