"""Test suite for gemini-vercel-streaming-chatbot skill and Knowledge Vault items."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser


@pytest.mark.unit
class TestGeminiVercelStreamingChatbotSkill:
    """Validate gemini-vercel-streaming-chatbot against deep-module standards."""

    @pytest.fixture
    def repo_root(self) -> Path:
        return Path(__file__).parent.parent

    @pytest.fixture
    def skill_dir(self, repo_root: Path) -> Path:
        return repo_root / ".agents" / "skills" / "gemini-vercel-streaming-chatbot"

    @pytest.fixture
    def ki_dir(self, repo_root: Path) -> Path:
        return repo_root / ".harness" / "knowledge" / "ki_20260918_gemini_vercel_streaming"

    def test_skill_structure_and_files_exist(self, skill_dir: Path) -> None:
        assert skill_dir.exists(), "Skill directory missing"
        assert (skill_dir / "SKILL.md").exists(), "SKILL.md missing"
        assert (skill_dir / "CARD.md").exists(), "CARD.md missing"
        assert (skill_dir / "config.default.yaml").exists(), "config.default.yaml missing (Rule 44)"

    @pytest.mark.asyncio
    async def test_skill_validation_pipeline_passes(self, skill_dir: Path) -> None:
        report = await SkillValidator.validate_async(skill_dir)
        assert report.valid is True, f"Skill validation failed: {report.errors}"
        for check in report.checks:
            assert check.passed is True, f"Check failed: {check.name} - {check.message}"

    def test_card_parser_extraction(self, skill_dir: Path) -> None:
        node = SkillCardParser.parse_directory(skill_dir)
        assert node is not None, "Failed to parse skill directory"
        assert node.name == "gemini-vercel-streaming-chatbot"
        assert len(node.stages) >= 5, f"Expected >= 5 stages, found {len(node.stages)}"
        assert len(node.anti_patterns) >= 5, f"Expected >= 5 anti-patterns, found {len(node.anti_patterns)}"

    def test_zero_fork_config(self, skill_dir: Path) -> None:
        config_path = skill_dir / "config.default.yaml"
        assert config_path.exists(), "Missing config.default.yaml (Rule 44)"
        text = config_path.read_text(encoding="utf-8")
        assert "operational_budgets" in text
        assert "max_turns" in text
        assert "streaming_config" in text

    def test_knowledge_vault_dual_file_integrity(self, ki_dir: Path) -> None:
        assert ki_dir.exists(), "Knowledge vault directory missing"
        meta_file = ki_dir / "metadata.json"
        summary_file = ki_dir / "summary.md"
        assert meta_file.exists(), "metadata.json missing"
        assert summary_file.exists(), "summary.md missing"

        data = json.loads(meta_file.read_text(encoding="utf-8"))
        assert data["id"] == "ki_20260918_gemini_vercel_streaming"
        assert data["category"] == "integration_and_io"
        assert "isnad" in data
        assert len(data["isnad"]["claims"]) >= 3

        summary_text = summary_file.read_text(encoding="utf-8")
        assert "Plain-Text Chunk Streaming" in summary_text
        assert "Johnson Samuel" in summary_text

    def test_context_map_registration(self, repo_root: Path) -> None:
        context_map = repo_root / "CONTEXT-MAP.md"
        assert context_map.exists(), "CONTEXT-MAP.md missing"
        text = context_map.read_text(encoding="utf-8")
        assert "gemini-vercel-streaming-chatbot" in text
        assert ".agents/skills/gemini-vercel-streaming-chatbot/SKILL.md" in text
