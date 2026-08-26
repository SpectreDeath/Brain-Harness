"""Tests for HarnessReflectorEngine, history harvester, and skill hygiene."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from click.testing import CliRunner

from harness.cli import main as cli_main
from harness.creator.reflection import (
    EpisodicMemoryReflector,
    HarnessHistoryHarvester,
    HarnessReflectorEngine,
    ReportArtifact,
    TranscriptSession,
)
from harness.creator.skills import SkillValidator
from harness.services.storage import SQLiteStorageService


@pytest.mark.unit
class TestHarnessReflectorCore:
    """Test history harvesting, episodic reflection, and knowledge item creation."""

    def test_harvester_parses_html_reports(self, tmp_path: Path) -> None:
        temp_dir = tmp_path / "temp_reports"
        temp_dir.mkdir()

        # Create simulated architecture review HTML report
        html_file = temp_dir / "architecture-review-20260826.html"
        html_content = """<!DOCTYPE html>
<html>
<head><title>Architecture Review (Cycle 3)</title></head>
<body>
  <h1>Architecture Deepening Report</h1>
  <p>Friction: Eager subprocess venv provisioning causes 60s test timeouts on Windows.</p>
  <div class="mermaid">graph TD; A-->B;</div>
</body>
</html>"""
        html_file.write_text(html_content, encoding="utf-8")

        harvester = HarnessHistoryHarvester(temp_dir=temp_dir, app_data_dir=tmp_path / "app_data")
        reports = harvester.harvest_temp_reports()

        assert len(reports) == 1
        assert reports[0].title == "Architecture Review (Cycle 3)"
        assert reports[0].report_type == "architecture_review"
        assert len(reports[0].friction_points) >= 1
        assert len(reports[0].mermaid_diagrams) == 1

    def test_harvester_parses_transcripts(self, tmp_path: Path) -> None:
        app_data = tmp_path / "app_data"
        logs_dir = app_data / "brain" / "conv-1234" / ".system_generated" / "logs"
        logs_dir.mkdir(parents=True)

        transcript_file = logs_dir / "transcript.jsonl"
        steps = [
            {"type": "USER_INPUT", "content": "Reflect on past architecture decisions"},
            {"type": "PLANNER_RESPONSE", "tool_calls": [{"toolAction": "Viewing file", "toolSummary": "View logs"}]},
            {"type": "PLANNER_RESPONSE", "status": "ERROR", "content": "Tool execution timed out after 60s"},
        ]
        with transcript_file.open("w", encoding="utf-8") as f:
            for s in steps:
                f.write(json.dumps(s) + "\n")

        harvester = HarnessHistoryHarvester(temp_dir=tmp_path / "temp_empty", app_data_dir=app_data)
        transcripts = harvester.harvest_transcripts()

        assert len(transcripts) == 1
        assert transcripts[0].conversation_id == "conv-1234"
        assert len(transcripts[0].user_requests) == 1
        assert len(transcripts[0].errors_encountered) == 1

    def test_episodic_distillation_and_ki_conversion(self, tmp_path: Path) -> None:
        rep = ReportArtifact(
            file_path=tmp_path / "architecture-review-test.html",
            title="Review Test",
            created_at="2026-08-26T12:00:00Z",
            report_type="architecture_review",
            content_text="Friction: Lazy subprocess staging resolves test timeouts.",
            friction_points=["Friction: Lazy subprocess staging resolves test timeouts."],
        )
        tr = TranscriptSession(
            conversation_id="test_conv",
            log_path=tmp_path / "transcript.jsonl",
            total_steps=5,
            errors_encountered=["Timed out after 60s"],
        )

        heuristics = EpisodicMemoryReflector.distill([rep], [tr])
        assert len(heuristics) >= 1

        ki = EpisodicMemoryReflector.to_knowledge_item(heuristics[0], index=1)
        assert ki.id.startswith("ki_self_")
        assert "endogenous_memory" in ki.tags
        assert hasattr(ki.isnad, "claims") or "claims" in ki.isnad


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reflector_engine_end_to_end(tmp_path: Path) -> None:
    temp_dir = tmp_path / "temp_reports"
    temp_dir.mkdir()
    (temp_dir / "architecture-review-20260826.html").write_text(
        "<html><head><title>Review</title></head><body>Friction: subprocess venv timeout.</body></html>",
        encoding="utf-8",
    )

    vault_dir = tmp_path / "vault"
    storage = SQLiteStorageService(":memory:")

    engine = HarnessReflectorEngine(
        storage=storage,
        temp_dir=temp_dir,
        app_data_dir=tmp_path / "app_data",
    )

    report = await engine.reflect(
        commit_to_vault=True,
        generate_html_brief=True,
        vault_dir=vault_dir,
    )

    assert report.harvested_reports_count == 1
    assert len(report.heuristics) >= 1
    assert len(report.knowledge_items) >= 1
    assert report.html_brief_path is not None
    assert report.html_brief_path.exists()

    # Verify saved in SQLite storage
    saved_items = await storage.list_knowledge_items()
    assert len(saved_items) >= 1

    storage.close()


@pytest.mark.unit
def test_cli_reflect_command() -> None:
    runner = CliRunner()
    result = runner.invoke(cli_main, ["reflect", "--no-commit"])
    assert result.exit_code == 0
    assert "Endogenous Memory Reflection Report" in result.output
    assert "Harvested Reports" in result.output
    assert "Distilled Heuristics" in result.output


@pytest.mark.unit
def test_harness_reflector_skill_hygiene() -> None:
    skill_dir = Path(__file__).parent.parent / ".agents" / "skills" / "harness-reflector"
    assert skill_dir.exists(), f"Skill directory missing: {skill_dir}"
    assert (skill_dir / "SKILL.md").exists()
    assert (skill_dir / "CARD.md").exists()
    assert (skill_dir / "README.md").exists()

    report = SkillValidator.validate(skill_dir)
    assert report.valid is True, f"Skill validation failed: {report.errors}"
