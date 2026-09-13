"""Tests for OKF Memory Governor Deep Skill (.agents/skills/okf-memory-governor).

Covers:
- Slotted and frozen dataclass immutability (Rule 12 & Rule 43)
- BM25Token, SearchCandidate, and OKFConceptNode construction assertions
- SkillCardParser parsing accuracy (stages, anti-patterns, invariants)
- SkillValidator craft standards compliance (report.valid is True)
- Dual-tier description budget (100-350 characters, Rule 44)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser

# Dynamic import from .agents/skills/okf-memory-governor/scripts/okf_engine.py
_ENGINE_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / ".agents"
    / "skills"
    / "okf-memory-governor"
    / "scripts"
    / "okf_engine.py"
)
_spec = importlib.util.spec_from_file_location("okf_engine", _ENGINE_SCRIPT)
assert _spec and _spec.loader, f"Failed to resolve spec for {_ENGINE_SCRIPT}"
_okf_engine_mod = importlib.util.module_from_spec(_spec)
sys.modules["okf_engine"] = _okf_engine_mod
_spec.loader.exec_module(_okf_engine_mod)

BM25Token = _okf_engine_mod.BM25Token
OKFConceptNode = _okf_engine_mod.OKFConceptNode
SearchCandidate = _okf_engine_mod.SearchCandidate


@pytest.mark.unit
class TestOKFEngineDataclasses:
    """Validate slotted and frozen dataclass architecture (Rule 12 & Rule 43)."""

    def test_bm25_token_immutability_and_validation(self) -> None:
        """Verify BM25Token is frozen and enforces valid constructor parameters."""
        tok = BM25Token(term="jwt", field="title", weight=2.0)
        assert tok.term == "jwt"
        assert tok.weight == 2.0

        # Rule 43: Direct attribute assignment inside pytest.raises((AttributeError, TypeError))
        with pytest.raises((AttributeError, TypeError)):
            tok.term = "modified"  # type: ignore[misc]

        # Validation assertions in __post_init__
        with pytest.raises(ValueError, match="term cannot be empty"):
            BM25Token(term="", field="title")

        with pytest.raises(ValueError, match="weight must be positive"):
            BM25Token(term="jwt", field="title", weight=-1.0)

    def test_search_candidate_immutability(self) -> None:
        """Verify SearchCandidate is slotted, frozen, and validates non-empty concept_id."""
        cand = SearchCandidate(
            concept_id="auth-jwt",
            title="JWT Auth",
            score=12.5,
            description="JWT session handling",
            governance=("Rule 1", "Rule 2"),
        )
        assert cand.concept_id == "auth-jwt"
        assert len(cand.governance) == 2

        with pytest.raises((AttributeError, TypeError)):
            cand.score = 99.0  # type: ignore[misc]

        with pytest.raises(ValueError, match="concept_id cannot be empty"):
            SearchCandidate(concept_id="", title="Title", score=1.0)

    def test_okf_concept_node_immutability_and_contract(self) -> None:
        """Verify OKFConceptNode is slotted, frozen, and asserts required fields."""
        node = OKFConceptNode(
            concept_id="arch-001",
            title="Modular Plugin Design",
            concept_type="architecture",
            description="All subsystems are registered as plugins.",
            body="Details",
            governance=("Invariant 1",),
            code_refs=("src/harness/kernel/",),
        )
        assert node.concept_id == "arch-001"
        assert node.generated_by == "agent:brain-harness"

        with pytest.raises((AttributeError, TypeError)):
            node.title = "Altered Title"  # type: ignore[misc]

        with pytest.raises(ValueError, match="concept_id cannot be empty"):
            OKFConceptNode(concept_id="", title="T", concept_type="c", description="D")

        with pytest.raises(ValueError, match="title cannot be empty"):
            OKFConceptNode(concept_id="id", title="", concept_type="c", description="D")

        with pytest.raises(ValueError, match="description cannot be empty"):
            OKFConceptNode(concept_id="id", title="T", concept_type="c", description="")


@pytest.mark.unit
class TestOKFSkillCardAndHygiene:
    """Validate skill files against craft standards, card parsing, and catalog budgets."""

    @pytest.fixture
    def skill_dir(self) -> Path:
        root = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "okf-memory-governor"
        assert root.exists(), f"Skill directory missing at: {root}"
        return root

    def test_skill_card_parser_extraction(self, skill_dir: Path) -> None:
        """Verify SkillCardParser extracts all pillars from CARD.md and SKILL.md."""
        node = SkillCardParser.parse_directory(skill_dir)
        assert node is not None
        assert node.name == "okf-memory-governor"
        assert node.category == "memory_and_epistemics"
        assert len(node.stages) >= 5, f"Expected 5 stages, found {len(node.stages)}"
        assert len(node.anti_patterns) >= 5, f"Expected 5 anti-patterns, found {len(node.anti_patterns)}"
        assert len(node.invariants) >= 5, f"Expected 5 invariants, found {len(node.invariants)}"
        assert all(inv.is_blocking for inv in node.invariants)

    @pytest.mark.asyncio
    async def test_skill_validator_craft_standards(self, skill_dir: Path) -> None:
        """Verify SkillValidator confirms valid craft standards (Rule 34)."""
        report = await SkillValidator.validate_async(skill_dir)
        assert report.valid is True, f"SkillValidator failed: {report.errors}"
        assert len(report.errors) == 0

    def test_dual_tier_catalog_budget(self, skill_dir: Path) -> None:
        """Verify frontmatter description length is bounded between 100 and 350 chars (Rule 44)."""
        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        assert len(parts) >= 3, "Missing frontmatter delimiters"
        frontmatter = yaml.safe_load(parts[1])
        desc = frontmatter.get("description", "")
        desc_len = len(desc)

        assert 100 <= desc_len <= 350, (
            f"Description length {desc_len} violates Rule 44 (must be 100-350 chars): '{desc}'"
        )
        assert "Do not use for" in desc, "Description missing explicit negative boundary (Rule 44)"

    def test_config_default_yaml_exists(self, skill_dir: Path) -> None:
        """Verify co-located config.default.yaml defines operational budgets (Rule 44)."""
        cfg_file = skill_dir / "config.default.yaml"
        assert cfg_file.exists(), "config.default.yaml missing in skill folder"
        cfg = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
        assert "bundle" in cfg
        assert "search" in cfg
        assert "governance" in cfg
        assert "validation" in cfg
        assert "execution" in cfg
