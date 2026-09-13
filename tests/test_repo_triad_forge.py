"""Test suite for repo-triad-forge skill adhering to Craft standards and Rule 43."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

# Ensure skill scripts directory is on sys.path
_SKILL_SCRIPTS = Path(__file__).parent.parent / ".agents" / "skills" / "repo-triad-forge" / "scripts"
if str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))

from triad_pipeline import (  # type: ignore
    KiCandidate,
    RepoInspectionResult,
    RepoTriadPipelineEngine,
    TriadExecutionResult,
)


@pytest.mark.unit
class TestRepoTriadForgeEngine:
    """Validate triad pipeline engine, slotted/frozen immutability, and inspection logic."""

    def test_slotted_frozen_dataclasses_immutability(self) -> None:
        """Verify slotted/frozen dataclass immutability using direct assignment per Rule 43."""
        inspection = RepoInspectionResult(
            repo_path="/path/to/repo",
            repo_name="sample-repo",
            languages=("Python", "TypeScript"),
            packages=("pkg-a", "pkg-b"),
            has_git=True,
            compute_tier="High",
            composite_complexity=0.82,
            total_files=150,
        )
        ki = KiCandidate(
            id="ki_sample_01",
            title="Sample Knowledge",
            domain="software_engineering",
            claims_count=2,
            citations=("file.py#L1-L10",),
        )
        stage_res = TriadExecutionResult(
            success=True,
            stage="Audit",
            artifacts=("/temp/brief.html",),
            message="Done",
        )

        # Direct attribute assignment must raise AttributeError/TypeError (Rule 43)
        with pytest.raises((AttributeError, TypeError)):
            inspection.repo_name = "mutated"  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            ki.title = "mutated"  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            stage_res.success = False  # type: ignore

    def test_inspect_repository_workspace_root(self) -> None:
        """Verify repository inspection runs against current workspace root."""
        root = Path(__file__).parent.parent
        res = RepoTriadPipelineEngine.inspect_repository(root)

        assert res.repo_name == "Brain Harness"
        assert "Python" in res.languages
        assert res.total_files > 10
        assert res.compute_tier in ("High", "Medium", "Low")
        assert 0.0 <= res.composite_complexity <= 1.0

    def test_scaffold_visual_briefs(self, tmp_path: Path) -> None:
        """Verify HTML visual briefs are generated with dark-mode styling and metrics."""
        inspection = RepoInspectionResult(
            repo_path="/path/to/repo",
            repo_name="test-repo",
            languages=("Python",),
            packages=(),
            has_git=True,
            compute_tier="Medium",
            composite_complexity=0.65,
            total_files=42,
        )

        briefs = RepoTriadPipelineEngine.scaffold_visual_briefs(inspection, output_dir=tmp_path)
        assert len(briefs) == 5
        for b in briefs:
            assert b.exists()
            content = b.read_text(encoding="utf-8")
            assert "background: #0d1117" in content
            assert "test-repo" in content
            assert "Medium" in content

    def test_extract_ki_candidates(self) -> None:
        """Verify extraction of candidate Knowledge Items with isnad citations."""
        inspection = RepoInspectionResult(
            repo_path="/path/to/sample",
            repo_name="pr_lens",
            languages=("TypeScript",),
            packages=("packages/schema", "packages/renderer"),
            has_git=True,
            compute_tier="High",
            composite_complexity=0.85,
            total_files=95,
        )

        candidates = RepoTriadPipelineEngine.extract_ki_candidates(inspection)
        assert len(candidates) >= 3
        for c in candidates:
            assert c.id.startswith("ki_pr_lens_")
            assert len(c.citations) >= 1
            assert c.confidence >= 0.85

    def test_synthesize_plan(self) -> None:
        """Verify plan synthesis generates structured 5-stage markdown plan."""
        inspection = RepoInspectionResult(
            repo_path="/path/to/repo",
            repo_name="demo-repo",
            languages=("Python",),
            packages=(),
            has_git=True,
            compute_tier="Medium",
            composite_complexity=0.7,
            total_files=50,
        )
        plan = RepoTriadPipelineEngine.synthesize_plan(inspection, "demo-skill", "demo_plugin")
        assert "Implementation Plan" in plan
        assert "demo-repo" in plan
        assert "demo-skill" in plan
        assert "demo_plugin" in plan

    def test_commit_vault_kis(self, tmp_path: Path) -> None:
        """Verify committing KIs adheres to canonical dual-file format (Rule 40)."""
        kis_data = [
            {
                "id": "ki_test_rule_40",
                "title": "Dual-File Directory Invariant",
                "assertion": "Knowledge Items must use dual-file format",
                "citations": ["src/rule.py#L1-L20"],
            }
        ]
        committed = RepoTriadPipelineEngine.commit_vault_kis(kis_data, vault_root=tmp_path)
        assert len(committed) == 1
        assert committed[0] == "ki_test_rule_40"

        ki_dir = tmp_path / "ki_test_rule_40"
        assert ki_dir.is_dir()
        assert (ki_dir / "metadata.json").exists()
        assert (ki_dir / "summary.md").exists()

    def test_run_bounded_verification(self) -> None:
        """Verify bounded verification runs successfully on valid python check."""
        commands = [[sys.executable, "-c", "import sys; sys.exit(0)"]]
        res = RepoTriadPipelineEngine.run_bounded_verification(commands, max_attempts=2)
        assert res.success is True
        assert len(res.artifacts) == 1
        assert "PASSED" in res.artifacts[0]

    def test_synthesize_plan_data_and_structure(self) -> None:
        """Verify structured plan data synthesis with operational budgets."""
        inspection = RepoInspectionResult(
            repo_path="/path/to/repo",
            repo_name="demo-repo",
            languages=("Python",),
            packages=(),
            has_git=True,
            compute_tier="High",
            composite_complexity=0.85,
            total_files=250,
        )
        data = RepoTriadPipelineEngine.synthesize_plan_data(inspection, "demo-skill", "demo_plugin")
        assert data["stages_count"] == 5
        assert data["estimated_duration_seconds"] == 300
        assert "Implementation Plan" in data["plan_markdown"]

    def test_extract_ki_candidates_authentic_citations(self) -> None:
        """Verify candidate Knowledge Items generate verifiable line-coordinate isnad citations."""
        inspection = RepoInspectionResult(
            repo_path="/path/to/repo",
            repo_name="sample-repo",
            languages=("Python",),
            packages=("pkg-core",),
            has_git=True,
            compute_tier="Medium",
            composite_complexity=0.6,
            total_files=40,
            blast_radius_roots=("src/models.py", "src/service.py", "main.py"),
        )
        candidates = RepoTriadPipelineEngine.extract_ki_candidates(inspection)
        assert len(candidates) >= 3
        for c in candidates:
            assert len(c.citations) >= 1
            assert any("#L" in cite for cite in c.citations)

    def test_cli_subcommands_execution(self) -> None:
        """Verify CLI subcommands (inspect, plan, ki-candidates) execute cleanly via subprocess."""
        script_path = _SKILL_SCRIPTS / "triad_pipeline.py"
        workspace_root = str(Path(__file__).parent.parent)

        p_ins = subprocess.run(
            [sys.executable, str(script_path), "inspect", "--repo", workspace_root],
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Brain Harness" in p_ins.stdout

        p_plan = subprocess.run(
            [sys.executable, str(script_path), "plan", "--repo", workspace_root],
            capture_output=True,
            text=True,
            check=True,
        )
        assert "stages_count" in p_plan.stdout

