"""Architectural decomposition contract tests for temp_artifact_miner subpackage.

Verifies:
1. Subpackage modular structure and clean re-exports via __init__.py (Rule 49)
2. Slotted & frozen dataclass immutability across models (Rule 12, Rule 43)
3. Heavy topology parsing & context blowout bounding (Rule 48)
4. Ephemeral directory scanning with defensive batch exception handling (Rule 32, Rule 52)
5. Sandbox triage and ring-buffer log tailing (Rule 52, Rule 53)
6. Dual-lens cognitive bifurcation canonical Knowledge Vault dual-file format (Rule 40, Rule 41)
7. Documentation salvage and markdown summary generation
8. Single-seam resolver behavior with IoC context and fallback (Rule 58)
9. Rule 11 line count invariant (<200 lines across all submodules)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.kernel.context import ServiceContext
from harness.services.temp_artifact_miner import (
    BriefCatalog,
    BriefCatalogItem,
    CognitiveBifurcationReport,
    IsnadAttributionRecord,
    SandboxFixture,
    SandboxReport,
    StandardTempArtifactMinerService,
    TEMP_ARTIFACT_MINER_KEY,
    TempArtifactMinerService,
    VisualSalvageReport,
    compute_file_sha256,
    detect_brief_category,
    resolve_temp_artifact_miner,
)
from harness.services.temp_artifact_miner.bifurcation import bifurcate_brief
from harness.services.temp_artifact_miner.parser import parse_html_brief
from harness.services.temp_artifact_miner.salvage import (
    generate_salvage_markdown,
    salvage_diagrams,
)
from harness.services.temp_artifact_miner.sandbox import (
    tail_diagnostic_log,
    triage_sandbox,
)
from harness.services.temp_artifact_miner.scanner import scan_briefs


@pytest.mark.unit
class TestTempArtifactMinerDecomposition:
    """Contract tests for temp_artifact_miner decomposition."""

    def test_submodule_line_counts(self) -> None:
        """Verify all submodules in temp_artifact_miner are strictly < 200 lines (Rule 11)."""
        pkg_dir = Path(__file__).resolve().parent.parent / "src" / "harness" / "services" / "temp_artifact_miner"
        py_files = list(pkg_dir.glob("*.py"))
        assert len(py_files) >= 8, f"Expected at least 8 submodules, found {len(py_files)}"

        for file_path in py_files:
            lines = len(file_path.read_text(encoding="utf-8").splitlines())
            assert lines < 200, f"{file_path.name} exceeds 200 lines ({lines} lines)"

    def test_models_immutability_and_bounds(self) -> None:
        """Verify slotted/frozen dataclasses assert immutability and validate inputs (Rule 12, Rule 43)."""
        item = BriefCatalogItem(
            name="test-brief.html",
            path="/tmp/test-brief.html",
            category="architecture-review",
            title="Test Brief",
            size_bytes=1024,
            mtime=1700000000.0,
            has_mermaid=True,
            has_scorecard=True,
            has_antipatterns=False,
            is_heavy_topology=False,
            mermaid_dags=("graph TD\n  A --> B",),
            sha256="1234567890abcdef",
        )
        assert item.name == "test-brief.html"
        assert item.mermaid_dags == ("graph TD\n  A --> B",)

        with pytest.raises((AttributeError, TypeError)):
            item.title = "Mutated"  # type: ignore

        # Invalid negative count in BriefCatalog
        with pytest.raises(ValueError, match="negative"):
            BriefCatalog(total_scanned=-1, brief_count=0, total_bytes=0, heavy_count=0)

    def test_parser_and_heavy_bounding(self, tmp_path: Path) -> None:
        """Verify parse_html_brief parses titles, diagrams, and bounds heavy files (Rule 48)."""
        normal_file = tmp_path / "architecture-review-test.html"
        normal_file.write_text(
            "<!DOCTYPE html><html><head><title>Architecture Review Sample</title></head><body>"
            "<div class=\"mermaid\">graph TD\n  A --> B</div>"
            "<div>scorecard summary</div>"
            "<div>anti-pattern defense</div>"
            "</body></html>",
            encoding="utf-8",
        )
        item = parse_html_brief(normal_file, heavy_threshold=50000)
        assert item.title == "Architecture Review Sample"
        assert item.has_mermaid is True
        assert item.has_scorecard is True
        assert item.has_antipatterns is True
        assert item.is_heavy_topology is False
        assert len(item.mermaid_dags) == 1
        assert "A --> B" in item.mermaid_dags[0]

        # Heavy file
        heavy_file = tmp_path / "heavy-diagram.html"
        heavy_file.write_text("A" * 120000, encoding="utf-8")
        heavy_item = parse_html_brief(heavy_file, heavy_threshold=100000)
        assert heavy_item.is_heavy_topology is True
        assert heavy_item.mermaid_dags == ()  # heavy files do not parse deep dags

    def test_scanner_with_defensive_handling(self, tmp_path: Path) -> None:
        """Verify scan_briefs discovers HTML files and handles missing dirs defensively (Rule 32, Rule 52)."""
        # Non-existent directory returns empty catalog
        missing_catalog = scan_briefs(tmp_path / "non_existent")
        assert missing_catalog.total_scanned == 0
        assert missing_catalog.brief_count == 0

        # Directory with files
        (tmp_path / "book-to-skill-forge-01.html").write_text(
            "<html><head><title>Book to Skill</title></head><body></body></html>",
            encoding="utf-8",
        )
        (tmp_path / "random.txt").write_text("Not HTML", encoding="utf-8")

        catalog = scan_briefs(tmp_path)
        assert catalog.total_scanned == 1
        assert catalog.brief_count == 1
        assert "book-to-skill-forge" in catalog.items_by_category

    def test_sandbox_triage_and_log_tail(self, tmp_path: Path) -> None:
        """Verify triage_sandbox prunes noise and tail_diagnostic_log bounds lines (Rule 52, Rule 53)."""
        sandbox_dir = tmp_path / "pytest-of-spectre" / "pytest-101"
        (sandbox_dir / "fixture_a" / "skills" / "mock_skill").mkdir(parents=True)
        (sandbox_dir / ".git").mkdir()  # should be pruned

        report = triage_sandbox(tmp_path)
        assert report.total_runs == 1
        assert len(report.runs) == 1
        assert report.runs[0].fixture_count >= 1
        assert "mock_skill" in report.runs[0].mock_skills

        # Ring buffer log tail
        log_file = tmp_path / "test.log"
        log_file.write_text("\n".join(f"line_{i}" for i in range(100)), encoding="utf-8")
        tail = tail_diagnostic_log(log_file, max_lines=10)
        assert len(tail) == 10
        assert tail[-1] == "line_99"

    def test_dual_lens_cognitive_bifurcation(self, tmp_path: Path) -> None:
        """Verify bifurcate_brief writes canonical Knowledge Vault dual-files (Rule 40, Rule 41)."""
        brief_file = tmp_path / "architecture-review-cycle.html"
        brief_file.write_text(
            "<html><head><title>Cycle Architecture</title></head><body>"
            "<div class=\"mermaid\">graph LR\n  X --> Y</div>"
            "</body></html>",
            encoding="utf-8",
        )

        vault_dir = tmp_path / "vault"
        docs_dir = tmp_path / "docs"

        report = bifurcate_brief(
            brief_file,
            target_vault_dir=vault_dir,
            target_docs_dir=docs_dir,
        )

        assert Path(report.knowledge_vault_path).exists()
        assert Path(report.salvaged_doc_path).exists()

        # Check canonical dual-file format (Rule 40)
        meta_path = Path(report.knowledge_vault_path) / "metadata.json"
        summary_path = Path(report.knowledge_vault_path) / "summary.md"
        assert meta_path.exists()
        assert summary_path.exists()

        meta_data = json.loads(meta_path.read_text(encoding="utf-8"))
        assert meta_data["isnad"]["status"] == "VERIFIED"
        assert len(meta_data["isnad"]["claims"]) >= 1

        summary_text = summary_path.read_text(encoding="utf-8")
        assert "Knowledge Item: Cycle Architecture" in summary_text
        assert "X --> Y" in summary_text

    def test_salvage_diagrams_and_markdown(self, tmp_path: Path) -> None:
        """Verify salvage_diagrams and generate_salvage_markdown."""
        brief_file = tmp_path / "demo-review.html"
        brief_file.write_text(
            "<html><head><title>Demo</title></head><body>"
            "<div class=\"mermaid\">graph TD\n  Start --> Done</div>"
            "</body></html>",
            encoding="utf-8",
        )
        docs_dir = tmp_path / "docs"
        salvage_report = salvage_diagrams(brief_file, target_docs_dir=docs_dir)
        assert salvage_report.extracted_diagrams_count == 1
        assert Path(salvage_report.salvaged_doc_path).exists()

        catalog = scan_briefs(tmp_path)
        md = generate_salvage_markdown(catalog)
        assert "# Ephemeral Visual Brief Salvage Index" in md
        assert "Total Briefs Scanned" in md

    def test_single_seam_resolver(self) -> None:
        """Verify resolve_temp_artifact_miner single-seam resolver (Rule 58)."""
        # None context returns standard instance
        svc_fallback = resolve_temp_artifact_miner(None)
        assert isinstance(svc_fallback, StandardTempArtifactMinerService)
        assert isinstance(svc_fallback, TempArtifactMinerService)

        # Custom dir parameter
        custom_dir = Path("/custom/temp/dir")
        svc_custom = resolve_temp_artifact_miner(None, default_temp_dir=custom_dir)
        assert svc_custom._default_temp_dir == custom_dir

        # IoC context resolution
        ctx = ServiceContext()
        custom_svc = StandardTempArtifactMinerService(default_temp_dir=custom_dir)
        ctx.provide(TEMP_ARTIFACT_MINER_KEY, custom_svc)

        resolved = resolve_temp_artifact_miner(ctx)
        assert resolved is custom_svc
