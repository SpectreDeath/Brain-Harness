"""Contract test suite for swarm-reflection-optimizer meta-skill."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser
from plugins.memory_and_epistemics.skill_knowledge_graph.models import SkillNode


@pytest.fixture
def skill_dir() -> Path:
    target = Path(__file__).parent.parent / ".agents" / "skills" / "swarm-reflection-optimizer"
    assert target.exists(), f"Skill directory missing: {target}"
    return target


@pytest.mark.unit
class TestSwarmReflectionOptimizerStructure:
    """Validate skill package structure, frontmatter, and AST parsing."""

    @pytest.mark.asyncio
    async def test_skill_validator_passes(self, skill_dir: Path) -> None:
        report = await SkillValidator.validate_async(skill_dir)
        assert report.valid is True, f"Skill validation failed: {report.errors}"

    def test_skill_card_and_pillar_parsing(self, skill_dir: Path) -> None:
        node = SkillCardParser.parse_directory(skill_dir)
        assert isinstance(node, SkillNode)
        assert node.name == "swarm-reflection-optimizer"
        assert len(node.stages) >= 5, f"Expected >= 5 stages, found {len(node.stages)}"
        assert len(node.anti_patterns) >= 5, f"Expected >= 5 anti-patterns, found {len(node.anti_patterns)}"
        assert len(node.invariants) >= 5, f"Expected >= 5 invariants, found {len(node.invariants)}"
        assert all(inv.is_blocking for inv in node.invariants), "All invariants must be blocking"

    def test_frontmatter_budget_and_negative_boundary(self, skill_dir: Path) -> None:
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists()
        text = skill_file.read_text(encoding="utf-8")

        # Rule 44: Description bounded between 100 and 350 chars with action verbs and negative boundary
        frontmatter, _ = SkillCardParser._extract_frontmatter(text)
        desc = frontmatter.get("description", "")
        assert 100 <= len(desc) <= 350, f"Description length {len(desc)} not in [100, 350]"
        assert "Do not use for" in desc, "Description must contain explicit negative boundary ('Do not use for...')"


@pytest.mark.unit
class TestSwarmOptimizerDriver:
    """Validate slotted domain entities, composite keying, Borda count, and Aquinas reflection."""

    def test_slotted_frozen_dataclass_immutability(self, skill_dir: Path) -> None:
        """Assert slotted and frozen dataclass invariants (Rule 12 & Rule 43)."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from swarm_optimizer_driver import (
            SwarmOptimizationReport,
            SwarmOptimizationStageResult,
            SwarmStrategyCandidate,
            TextualGradientNode,
        )

        grad = TextualGradientNode(
            composite_key="run_001_node_a",
            error_signal="timeout",
            gradient_directive="Scale timeout",
        )
        with pytest.raises((AttributeError, TypeError)):
            grad.momentum_beta = 0.5  # type: ignore

        strat = SwarmStrategyCandidate(
            strategy_id="s1",
            name="Retry with fallback",
            borda_score=10,
        )
        with pytest.raises((AttributeError, TypeError)):
            strat.selected = True  # type: ignore

        stage = SwarmOptimizationStageResult(
            stage_num=1,
            stage_name="Audit",
            passed=True,
            duration_ms=4.0,
            message="OK",
        )
        with pytest.raises((AttributeError, TypeError)):
            stage.passed = False  # type: ignore

        report = SwarmOptimizationReport(
            run_id="run_001",
            passed=True,
            winning_strategy="Retry",
            stages=(stage,),
        )
        with pytest.raises((AttributeError, TypeError)):
            report.passed = False  # type: ignore

    def test_composite_keying_rule_36(self, skill_dir: Path) -> None:
        """Assert composite keying uses {run_id}_{node_id} (Rule 36)."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from swarm_optimizer_driver import SwarmOptimizerDriver

        driver = SwarmOptimizerDriver("run_alpha")
        stage, comp_key = driver.localize_error_node("planner_agent", "SyntaxError on step 3")
        assert stage.passed is True
        assert comp_key == "run_alpha_planner_agent"
        assert "_" in comp_key

    def test_deliberation_borda_count_selection(self, skill_dir: Path) -> None:
        """Assert Borda count voting correctly ranks and picks winning strategy."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from swarm_optimizer_driver import SwarmOptimizerDriver

        driver = SwarmOptimizerDriver("run_beta")
        strategies = ["Option A", "Option B", "Option C"]
        # 3 voters:
        # Voter 1 ranks: B (idx 1), A (idx 0), C (idx 2) -> B:2, A:1, C:0
        # Voter 2 ranks: B (idx 1), C (idx 2), A (idx 0) -> B:2, C:1, A:0
        # Voter 3 ranks: A (idx 0), B (idx 1), C (idx 2) -> A:2, B:1, C:0
        # Totals: B = 2 + 2 + 1 = 5; A = 1 + 0 + 2 = 3; C = 0 + 1 + 0 = 1.
        rankings = [
            [1, 0, 2],
            [1, 2, 0],
            [0, 1, 2],
        ]

        stage, winner = driver.deliberate_borda_count(strategies, rankings)
        assert stage.passed is True
        assert winner.name == "Option B"
        assert winner.borda_score == 5

    def test_aquinas_reflection_verification(self, skill_dir: Path) -> None:
        """Assert Aquinas disputation format requires at least 2 objections and all parts."""
        sys.path.insert(0, str(skill_dir / "scripts"))
        from swarm_optimizer_driver import SwarmOptimizerDriver

        driver = SwarmOptimizerDriver("run_gamma")

        # Missing objections fails
        bad = driver.verify_aquinas_reflection(
            question="Utrum?",
            objections=["One objection"],
            sed_contra="Sed contra...",
            resolution="Respondeo...",
        )
        assert bad.passed is False

        # Complete passes
        good = driver.verify_aquinas_reflection(
            question="Whether to isolate tool execution?",
            objections=["Tool isolation adds IPC overhead", "Subprocesses complicate debugger attachment"],
            sed_contra="On the contrary, Rule 5 mandates subprocess isolation for external plugins",
            resolution="I answer that subprocess isolation prevents unhandled crashes from aborting the kernel",
        )
        assert good.passed is True
