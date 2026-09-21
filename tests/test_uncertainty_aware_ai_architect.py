"""Test suite for uncertainty-aware-ai-architect skill and Knowledge Vault item."""

from __future__ import annotations

import json
import math
from pathlib import Path
import pytest

from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser


@pytest.mark.unit
class TestUncertaintyAwareAiArchitectSkill:
    """Validate craft standards, frontmatter bounds, and card formatting."""

    @pytest.fixture
    def skill_dir(self) -> Path:
        p = Path(__file__).parent.parent / ".agents" / "skills" / "uncertainty-aware-ai-architect"
        assert p.exists(), f"Skill directory missing: {p}"
        return p

    @pytest.fixture
    def ki_dir(self) -> Path:
        p = Path(__file__).parent.parent / ".harness" / "knowledge" / "ki_njoku_uncertainty_aware_systems"
        assert p.exists(), f"Knowledge Item directory missing: {p}"
        return p

    def test_skill_validator_passes(self, skill_dir: Path) -> None:
        report = SkillValidator.validate_sync(skill_dir)
        assert report.valid is True, f"SkillValidator failed: {report.errors}"

    def test_frontmatter_description_bounds(self, skill_dir: Path) -> None:
        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        import re
        m = re.search(r"^description:\s*(.+)$", skill_text, re.MULTILINE)
        assert m is not None, "Missing description in frontmatter"
        desc = m.group(1).strip()
        assert 100 <= len(desc) <= 350, f"Description length {len(desc)} not in [100, 350] (Rule 44)"
        assert desc.startswith(("Architect", "Implement", "Audit", "Design")), "Description must start with action verb"
        assert "Do not use for" in desc, "Description must state explicit negative boundary (Rule 44)"

    def test_card_ascii_formatting_and_pillars(self, skill_dir: Path) -> None:
        card_text = (skill_dir / "CARD.md").read_text(encoding="utf-8")
        # Rule 37: Single-pipe borders, not double borders
        assert "│" in card_text, "CARD.md must use single-pipe borders (Rule 37)"
        assert "║" not in card_text, "CARD.md must not use double borders (Rule 37)"
        assert "SKILL:       uncertainty-aware-ai-architect" in card_text or "SKILL: uncertainty-aware-ai-architect" in card_text

        # Parse via SkillCardParser
        node = SkillCardParser.parse_directory(skill_dir)
        assert node is not None
        assert node.name == "uncertainty-aware-ai-architect"
        assert len(node.stages) >= 5, f"Expected 5 stages, found {len(node.stages)}"
        assert len(node.anti_patterns) >= 5, f"Expected >= 5 anti-patterns, found {len(node.anti_patterns)}"
        assert len(node.invariants) >= 1, "Expected invariants checklist in CARD.md"

    def test_knowledge_vault_dual_file_format(self, ki_dir: Path) -> None:
        meta_file = ki_dir / "metadata.json"
        summary_file = ki_dir / "summary.md"
        assert meta_file.exists(), "metadata.json missing (Rule 40)"
        assert summary_file.exists(), "summary.md missing (Rule 40)"

        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        assert meta["id"] == "ki_njoku_uncertainty_aware_systems"
        assert "njoku" in meta["tags"]
        assert meta["category"] == "agent_orchestration"

        summary_text = summary_file.read_text(encoding="utf-8")
        assert "Chidiebere Njoku" in summary_text
        assert "3-Layer Interception Lifecycle" in summary_text

    def test_entropy_and_perplexity_math(self) -> None:
        """Verify mathematical invariants for logprob entropy and perplexity."""
        # Simulated high confidence: logprobs close to 0 (p close to 1)
        confident_logprobs = [-0.05, -0.08, -0.02, -0.10]
        avg_conf = sum(confident_logprobs) / len(confident_logprobs)
        perp_conf = math.exp(-avg_conf)
        assert avg_conf >= -0.35, "High confidence avg logprob should pass threshold"
        assert 1.0 <= perp_conf <= 1.5, "High confidence perplexity should be low"

        # Simulated low confidence: logprobs significantly negative (high entropy)
        unconfident_logprobs = [-0.65, -1.20, -0.85, -0.90]
        avg_unconf = sum(unconfident_logprobs) / len(unconfident_logprobs)
        perp_unconf = math.exp(-avg_unconf)
        assert avg_unconf < -0.35, "Low confidence avg logprob should fail threshold"
        assert perp_unconf > 2.0, "Low confidence perplexity should be elevated"
