"""Test suite for pre-commit-security-guard skill and Knowledge Vault item."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser


@pytest.mark.unit
class TestPreCommitSecurityGuardSkill:
    """Validate craft standards, frontmatter bounds, card formatting, and knowledge items."""

    @pytest.fixture
    def skill_dir(self) -> Path:
        p = (
            Path(__file__).parent.parent
            / ".agents"
            / "skills"
            / "pre-commit-security-guard"
        )
        assert p.exists(), f"Skill directory missing: {p}"
        return p

    @pytest.fixture
    def ki_dir(self) -> Path:
        p = (
            Path(__file__).parent.parent
            / ".harness"
            / "knowledge"
            / "ki_umairmirza_precommit_security"
        )
        assert p.exists(), f"Knowledge Item directory missing: {p}"
        return p

    def test_skill_validator_passes(self, skill_dir: Path) -> None:
        report = SkillValidator.validate_sync(skill_dir)
        assert report.valid is True, f"SkillValidator failed: {report.errors}"
        assert len(report.warnings) == 0, (
            f"Unexpected warnings in report: {report.warnings}"
        )

    def test_frontmatter_description_bounds(self, skill_dir: Path) -> None:
        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        m = re.search(r"^description:\s*(.+)$", skill_text, re.MULTILINE)
        assert m is not None, "Missing description in frontmatter"
        desc = m.group(1).strip()
        assert 100 <= len(desc) <= 350, (
            f"Description length {len(desc)} not in [100, 350] (Rule 44)"
        )
        assert desc.startswith(("Shift", "Intercept", "Architect", "Implement")), (
            "Description must start with an action verb"
        )
        assert "Do not use for" in desc, (
            "Description must state explicit negative boundary (Rule 44)"
        )

    def test_card_ascii_formatting_and_pillars(self, skill_dir: Path) -> None:
        card_text = (skill_dir / "CARD.md").read_text(encoding="utf-8")
        assert "│" in card_text, "CARD.md must use single-pipe borders (Rule 37)"
        assert "║" not in card_text, "CARD.md must not use double borders (Rule 37)"
        assert "SKILL:       pre-commit-security-guard" in card_text or "SKILL: pre-commit-security-guard" in card_text

        node = SkillCardParser.parse_directory(skill_dir)
        assert node is not None
        assert node.name == "pre-commit-security-guard"
        assert len(node.stages) == 5, f"Expected 5 stages, found {len(node.stages)}"
        assert len(node.anti_patterns) >= 5, (
            f"Expected >= 5 anti-patterns, found {len(node.anti_patterns)}"
        )

    def test_zero_fork_config(self, skill_dir: Path) -> None:
        config_path = skill_dir / "config.default.yaml"
        assert config_path.exists(), "Missing config.default.yaml (Rule 44)"
        text = config_path.read_text(encoding="utf-8")
        assert "operational_budgets" in text
        assert "max_staged_files" in text
        assert "scanner_policy" in text
        assert "disallow_blanket_directory_exclusions" in text

    def test_dispatcher_script_syntax(self, skill_dir: Path) -> None:
        script_path = skill_dir / "scripts" / "run-devskim.py"
        assert script_path.exists(), "Missing scripts/run-devskim.py"
        code = script_path.read_text(encoding="utf-8")
        tree = ast.parse(code)
        func_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        assert "main" in func_names, "Missing main() in run-devskim.py"

    def test_knowledge_vault_dual_file_format(self, ki_dir: Path) -> None:
        meta_file = ki_dir / "metadata.json"
        summary_file = ki_dir / "summary.md"
        assert meta_file.exists(), "Missing metadata.json (Rule 40)"
        assert summary_file.exists(), "Missing summary.md (Rule 40)"

        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        assert meta["id"] == "ki_umairmirza_precommit_security"
        assert meta["category"] == "security_and_forensics"
        assert "isnad" in meta
        assert "claims" in meta["isnad"]
        assert len(meta["isnad"]["claims"]) >= 4
        for claim in meta["isnad"]["claims"]:
            assert "assertion" in claim
            assert "source" in claim
            assert claim.get("verified") is True

        summary_text = summary_file.read_text(encoding="utf-8")
        assert "Multi-Engine Division of Labor" in summary_text
        assert "Execution Dispatcher" in summary_text
        assert "Deliberate Synthetic Failure Verification" in summary_text
        assert "Dual-Gate CI Defense" in summary_text
