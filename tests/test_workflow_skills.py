"""Comprehensive unit test suite for newly authored workflow skills.

Tests:
    1. context-anti-rot-sync (audit, clean, sync, lint)
    2. media-to-vault-pipeline (fetch, distill-seams, verify-isnad, commit-vault, scaffold-skill)
    3. Invariant validation: Rule 12 (frozen/slotted dataclasses), Rule 40 (canonical dual-file vault), Rule 44 (zero-fork config).
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser

# Import CLI modules directly
import sys

skills_root = Path(__file__).parent.parent / ".agents" / "skills"
sys.path.insert(0, str(skills_root / "context-anti-rot-sync" / "scripts"))
sys.path.insert(0, str(skills_root / "media-to-vault-pipeline" / "scripts"))

import context_sync_cli  # type: ignore
import media_pipeline_cli  # type: ignore


@pytest.mark.unit
class TestContextAntiRotSyncWorkflow:
    """Test suite for context-anti-rot-sync workflow skill."""

    def test_skill_craft_standards(self) -> None:
        skill_dir = skills_root / "context-anti-rot-sync"
        assert skill_dir.exists()

        # 1. Card parser
        node = SkillCardParser.parse_directory(skill_dir)
        assert node is not None
        assert node.name == "context-anti-rot-sync"
        assert len(node.stages) >= 4
        assert len(node.anti_patterns) >= 1
        assert len(node.invariants) >= 1

        # 2. Config
        cfg = skill_dir / "config.default.yaml"
        assert cfg.exists()
        assert "max_instruction_lines: 150" in cfg.read_text(encoding="utf-8")

    def test_audit_file_detection(self, tmp_path: Path) -> None:
        engine = context_sync_cli.ContextSyncEngine(workspace_root=tmp_path)

        # Create mock bloated instruction file with lint leaks
        bloated_file = tmp_path / "MOCK_AGENTS.md"
        content = ["# Rules"]
        for i in range(160):
            content.append(f"{i}. Rule {i}")
        content.append("Traceback (most recent call last):")
        bloated_file.write_text("\n".join(content) + "\n", encoding="utf-8")

        res = engine.audit_file(bloated_file, max_lines=150)
        assert res.passed is False
        assert res.total_lines > 150
        rule_ids = [v.rule_id for v in res.violations]
        assert "RULE11_LINE_BUDGET_OVERFLOW" in rule_ids
        assert "RULE11_LINT_LEAKAGE" in rule_ids
        assert "RULE11_MISSING_NEGATIVE_BOUNDARIES" in rule_ids

    def test_clean_file_deduplication(self, tmp_path: Path) -> None:
        engine = context_sync_cli.ContextSyncEngine(workspace_root=tmp_path)
        dirty_file = tmp_path / "DIRTY.md"
        dirty_file.write_text("Line 1\n\n\n\nLine 2   \n\nLine 3\n", encoding="utf-8")

        out_file = tmp_path / "CLEAN.md"
        res = engine.clean_file(dirty_file, out_file)
        assert res["cleaned_lines"] < res["original_lines"]
        cleaned_text = out_file.read_text(encoding="utf-8")
        assert "Line 2" in cleaned_text
        assert "\n\n\n" not in cleaned_text

    def test_sync_projections(self, tmp_path: Path) -> None:
        engine = context_sync_cli.ContextSyncEngine(workspace_root=tmp_path)
        src = tmp_path / "AGENTS.md"
        src.write_text("## Architecture Rules\n\n1. **Plugin Rule** All code is plugins.\n2. **Type Rule** Use typed keys.\n", encoding="utf-8")

        res = engine.sync_projections(src, target_paths=["CLAUDE.md"])
        assert res["total_rules_extracted"] >= 2
        claude_md = tmp_path / "CLAUDE.md"
        assert claude_md.exists()
        assert "Derived Agent Rules" in claude_md.read_text(encoding="utf-8")

    def test_frozen_dataclass_invariants(self) -> None:
        v = context_sync_cli.ContextViolation(
            rule_id="TEST_01",
            file_path="foo.md",
            line_number=10,
            message="Test error",
        )
        # Verify frozen immutability (Rule 12 & Rule 43)
        with pytest.raises((AttributeError, TypeError)):
            v.line_number = 20  # type: ignore

        clean_res = context_sync_cli.CleanResult(
            source_file="src.md",
            output_file="out.md",
            original_lines=10,
            cleaned_lines=8,
            saved_lines=2,
        )
        with pytest.raises((AttributeError, TypeError)):
            clean_res.saved_lines = 5  # type: ignore

    def test_end_to_end_context_pipeline(self, tmp_path: Path) -> None:
        engine = context_sync_cli.ContextSyncEngine(workspace_root=tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(
            "# Architecture Rules\n\n"
            "Negative boundaries: Do not touch production databases.\n"
            "Testing seams: Run pytest -v for verification.\n\n"
            "1. **Plugin Rule** All code is plugins.\n"
            "2. **Type Rule** Typed keys are required.\n",
            encoding="utf-8",
        )

        cleaned_md = tmp_path / "AGENTS_CLEANED.md"
        report = engine.execute_pipeline(
            target_file=agents_md,
            sync_targets=["CLAUDE.md"],
            scan_root=tmp_path,
            clean_output=cleaned_md,
        )

        assert report.success is True
        assert report.audit_result.passed is True
        assert report.clean_result is not None
        assert report.clean_result.saved_lines >= 0
        assert report.sync_result is not None
        assert len(report.sync_result.targets_synchronized) == 1
        assert (tmp_path / "CLAUDE.md").exists()
        assert report.lint_report.total_checks >= 1


@pytest.mark.unit
class TestMediaToVaultPipelineWorkflow:
    """Test suite for media-to-vault-pipeline workflow skill."""

    def test_skill_craft_standards(self) -> None:
        skill_dir = skills_root / "media-to-vault-pipeline"
        assert skill_dir.exists()

        # 1. Card parser
        node = SkillCardParser.parse_directory(skill_dir)
        assert node is not None
        assert node.name == "media-to-vault-pipeline"
        assert len(node.stages) >= 4
        assert len(node.anti_patterns) >= 1
        assert len(node.invariants) >= 1

        # 2. Config
        cfg = skill_dir / "config.default.yaml"
        assert cfg.exists()
        assert "min_isnad_confidence" in cfg.read_text(encoding="utf-8")

    def test_transcript_fetch_and_distill(self, tmp_path: Path) -> None:
        engine = media_pipeline_cli.MediaPipelineEngine(workspace_root=tmp_path)

        # 1. Fetch
        res_fetch = engine.fetch_transcript("https://www.youtube.com/watch?v=mock123")
        assert res_fetch["total_segments"] >= 3
        assert "full_text" in res_fetch

        # 2. Distill dual-lens seams (Rule 41)
        res_distill = engine.distill_seams(res_fetch)
        assert res_distill["claims_count"] >= 1
        assert res_distill["steps_count"] >= 4
        assert len(res_distill["seam_epistemic_claims"]) >= 1
        assert len(res_distill["seam_procedural_steps"]) >= 1

    def test_isnad_verification(self, tmp_path: Path) -> None:
        engine = media_pipeline_cli.MediaPipelineEngine(workspace_root=tmp_path)
        mock_distilled = {
            "seam_epistemic_claims": [
                {
                    "claim_id": "c01",
                    "assertion": "Slotted dataclasses improve performance",
                    "timestamp_start": 10.0,
                    "timestamp_end": 25.0,
                    "evidence_quote": "We recommend slotted dataclasses",
                    "isnad_confidence": 0.95,
                }
            ]
        }
        res_isnad = engine.verify_isnad(mock_distilled)
        assert res_isnad["all_verified"] is True
        assert res_isnad["verified_count"] == 1

    def test_canonical_dual_file_vault_commit(self, tmp_path: Path) -> None:
        vault_dir = tmp_path / "knowledge"
        engine = media_pipeline_cli.MediaPipelineEngine(workspace_root=tmp_path)

        mock_distilled = {
            "source": "https://www.youtube.com/watch?v=test",
            "seam_epistemic_claims": [
                {
                    "claim_id": "c01",
                    "assertion": "Invariants must be verified pre-flight",
                    "timestamp_start": 5.0,
                    "timestamp_end": 15.0,
                }
            ],
        }

        res = engine.commit_vault(mock_distilled, ki_id="ki_test_01", vault_root=vault_dir)
        assert res["status"] == "COMMITTED_CANONICAL_DUAL_FILE"

        # Assert canonical dual-file directory format (Rule 40)
        ki_dir = vault_dir / "ki_test_01"
        assert ki_dir.is_dir()
        meta_file = ki_dir / "metadata.json"
        summary_file = ki_dir / "summary.md"
        assert meta_file.exists(), "metadata.json missing in KI directory"
        assert summary_file.exists(), "summary.md missing in KI directory"

        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        assert meta["id"] == "ki_test_01"
        assert meta["claims_count"] == 1

    def test_scaffold_skill(self, tmp_path: Path) -> None:
        skills_target = tmp_path / "skills"
        engine = media_pipeline_cli.MediaPipelineEngine(workspace_root=tmp_path)

        mock_distilled = {
            "seam_procedural_steps": [
                {
                    "step_num": 1,
                    "title": "Analyze Code",
                    "action_directive": "Inspect AST",
                    "completion_criterion": "AST mapped",
                },
                {
                    "step_num": 2,
                    "title": "Verify Test",
                    "action_directive": "Run pytest",
                    "completion_criterion": "100% pass",
                },
            ]
        }

        res = engine.scaffold_skill(mock_distilled, skill_name="test-scaffold-skill", skills_root=skills_target)
        assert res["status"] == "SCAFFOLDED_COMPLIANT"

        skill_dir = skills_target / "test-scaffold-skill"
        assert (skill_dir / "SKILL.md").exists()
        assert (skill_dir / "CARD.md").exists()
        assert (skill_dir / "config.default.yaml").exists()

        card_node = SkillCardParser.parse_directory(skill_dir)
        assert card_node is not None
        assert card_node.name == "test-scaffold-skill"
        assert len(card_node.stages) >= 2

    def test_end_to_end_execute_pipeline(self, tmp_path: Path) -> None:
        vault_root = tmp_path / "knowledge"
        skills_root = tmp_path / "skills"
        engine = media_pipeline_cli.MediaPipelineEngine(workspace_root=tmp_path)

        # One-shot composite pipeline execution (Rule 41 & 40)
        report = engine.execute_pipeline(
            source="https://www.youtube.com/watch?v=deepen_123",
            ki_id="ki_deepen_test",
            skill_name="deepened-agent-skill",
            vault_root=vault_root,
            skills_root=skills_root,
        )

        assert report.success is True
        assert report.isnad_verified is True
        assert report.claims_count >= 1
        assert report.steps_count >= 4
        assert report.vault_result.status == "COMMITTED_CANONICAL_DUAL_FILE"
        assert report.skill_result.status == "SCAFFOLDED_COMPLIANT"

        # Check files exist
        assert (vault_root / "ki_deepen_test" / "metadata.json").exists()
        assert (vault_root / "ki_deepen_test" / "summary.md").exists()
        assert (skills_root / "deepened-agent-skill" / "SKILL.md").exists()
        assert (skills_root / "deepened-agent-skill" / "CARD.md").exists()

    def test_frozen_pipeline_models(self) -> None:
        step = media_pipeline_cli.ProceduralStep(
            step_num=1,
            title="Step 1",
            action_directive="Run",
            completion_criterion="Done",
        )
        with pytest.raises((AttributeError, TypeError)):
            step.title = "Mutated"  # type: ignore
