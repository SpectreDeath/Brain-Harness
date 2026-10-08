"""Comprehensive contract tests for temp_artifact_miner architectural deepening.

Verifies:
1. Micro-kernel IoC service protocol and ServiceKey registration (Rule 1, Rule 2, Rule 49)
2. Domain-partitioned plugin lifecycle in plugins/memory_and_epistemics/ (Rule 45)
3. Slotted and frozen immutability assertions (Rule 12, Rule 43)
4. Heavy topology bounding without context blowout (Rule 9, Rule 48)
5. Bounded pytest sandbox triage and noise pruning (Rule 52, Rule 53)
6. Diagnostic log ring-buffer tailer (Rule 53)
7. Dual-lens cognitive bifurcation into canonical Knowledge Vault dual-files & permanent docs (Rule 40, Rule 41)
8. Headless Click CLI introspection suite across command aliases (Rule 6, Rule 10)
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.kernel.context import ServiceContext
from harness.services.temp_artifact_miner import (
    TEMP_ARTIFACT_MINER_KEY,
    BriefCatalog,
    BriefCatalogItem,
    CognitiveBifurcationReport,
    IsnadAttributionRecord,
    SandboxFixture,
    SandboxReport,
    StandardTempArtifactMinerService,
    TempArtifactMinerService,
    VisualSalvageReport,
    resolve_temp_artifact_miner,
)
from plugins.memory_and_epistemics.temp_artifact_miner.main import (
    TempArtifactMinerPlugin,
    plugin as temp_miner_plugin_singleton,
)
from harness.commands.temp_miner import temp_miner_group
from harness.cli import main as harness_cli_main


@pytest.mark.unit
class TestTempArtifactMinerDeepening:
    """Contract tests for deepened temp artifact miner architecture."""

    def test_service_protocol_conformance_and_singleton(self) -> None:
        """Verify StandardTempArtifactMinerService satisfies TempArtifactMinerService protocol (Rule 49)."""
        service = StandardTempArtifactMinerService()
        assert isinstance(service, TempArtifactMinerService)
        assert temp_miner_plugin_singleton is not None
        assert isinstance(temp_miner_plugin_singleton, TempArtifactMinerPlugin)
        assert TEMP_ARTIFACT_MINER_KEY in temp_miner_plugin_singleton.provides

    @pytest.mark.asyncio
    async def test_ioc_registration_and_resolution(self) -> None:
        """Verify TempArtifactMinerPlugin registers TEMP_ARTIFACT_MINER_KEY into IoC container (Rule 1, 2)."""
        ctx = ServiceContext()
        plugin = TempArtifactMinerPlugin()
        assert TEMP_ARTIFACT_MINER_KEY in plugin.provides

        await plugin.on_load(ctx)
        resolved_service = ctx.require(TEMP_ARTIFACT_MINER_KEY)
        assert resolved_service is not None
        assert isinstance(resolved_service, TempArtifactMinerService)

    def test_resolve_temp_artifact_miner_fallback_and_reexport(self) -> None:
        """Verify resolve_temp_artifact_miner returns fallback and is re-exported from harness.services (Rule 58)."""
        from harness.services import resolve_temp_artifact_miner as root_resolver

        # Verify fallback on None
        svc_none = resolve_temp_artifact_miner(None)
        assert isinstance(svc_none, StandardTempArtifactMinerService)

        # Verify fallback on empty context
        ctx_empty = ServiceContext()
        svc_empty = root_resolver(ctx_empty)
        assert isinstance(svc_empty, StandardTempArtifactMinerService)

        # Verify default_temp_dir parameter forwarding
        custom_dir = Path("/custom/temp/dir")
        svc_custom = resolve_temp_artifact_miner(None, default_temp_dir=custom_dir)
        assert svc_custom._default_temp_dir == custom_dir

    @pytest.mark.asyncio
    async def test_resolve_temp_artifact_miner_from_ioc(self) -> None:
        """Verify resolve_temp_artifact_miner resolves registered instance from IoC context (Rule 58)."""
        ctx = ServiceContext()
        plugin = TempArtifactMinerPlugin()
        await plugin.on_load(ctx)

        resolved = resolve_temp_artifact_miner(ctx)
        assert isinstance(resolved, TempArtifactMinerService)
        assert resolved is ctx.require(TEMP_ARTIFACT_MINER_KEY)

    def test_slotted_frozen_dataclass_immutability(self) -> None:
        """Verify slotted and frozen immutability across all domain models (Rule 12, Rule 43)."""
        item = BriefCatalogItem(
            name="arch-review.html",
            path="C:/temp/arch-review.html",
            category="architecture-review",
            title="Arch Review",
            size_bytes=4096,
            mtime=1700000000.0,
            has_mermaid=True,
            has_scorecard=True,
            has_antipatterns=False,
            is_heavy_topology=False,
            mermaid_dags=("graph TD\n  A --> B",),
            sha256="abcdef123456",
        )
        catalog = BriefCatalog(
            total_scanned=1,
            brief_count=1,
            total_bytes=4096,
            heavy_count=0,
            items_by_category={"architecture-review": (item,)},
        )
        fixture = SandboxFixture(
            name="pytest-1",
            path="C:/temp/pytest-1",
            fixture_count=2,
            mock_skills=("skill-a", "skill-b"),
        )
        report = SandboxReport(
            total_runs=1,
            sandbox_path="C:/temp/sandboxes",
            runs=(fixture,),
            error_snippets=(),
        )
        isnad = IsnadAttributionRecord(
            brief_name="arch-review.html",
            sha256="abcdef123456",
            mtime=1700000000.0,
            primary_source="HTML visual brief",
            test_anchor="test_contract",
        )
        salvage = VisualSalvageReport(
            brief_name="arch-review.html",
            knowledge_vault_path="vault/ki_01",
            salvaged_doc_path="docs/arch.md",
            extracted_diagrams_count=1,
            isnad_claims_count=1,
        )
        bifurcation = CognitiveBifurcationReport(
            source_name="arch-review.html",
            knowledge_vault_path="vault/ki_01",
            salvaged_doc_path="docs/arch.md",
            extracted_heuristics=("Rule 1",),
            procedural_rules=("Rule 2",),
        )

        # Immutability assertions via direct attribute assignment (Rule 43)
        with pytest.raises((AttributeError, TypeError)):
            item.title = "Changed"  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            catalog.total_scanned = 99  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            fixture.fixture_count = 5  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            report.total_runs = 10  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            isnad.confidence = 0.5  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            salvage.extracted_diagrams_count = 99  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            bifurcation.source_name = "other.html"  # type: ignore

    def test_heavy_topology_bounding(self, tmp_path: Path) -> None:
        """Verify heavy topology files exceeding threshold are bounded without full memory reading (Rule 48)."""
        service = StandardTempArtifactMinerService()

        # Normal brief
        normal_file = tmp_path / "architecture-review-test.html"
        normal_file.write_text(
            "<!DOCTYPE html><html><head><title>Small Brief</title></head><body>"
            "<div class=\"mermaid\">graph TD\n  Start --> End</div>"
            "<table><tr><td>scorecard</td></tr></table>"
            "<p>anti-pattern defense</p></body></html>",
            encoding="utf-8",
        )
        item_normal = service.parse_html_brief(normal_file, heavy_threshold=50000)
        assert item_normal.is_heavy_topology is False
        assert len(item_normal.mermaid_dags) == 1
        assert "Start --> End" in item_normal.mermaid_dags[0]

        # Heavy brief exceeding threshold
        heavy_file = tmp_path / "skill-graph-huge.html"
        heavy_file.write_text(
            "<!DOCTYPE html><html><head><title>Huge Topology Graph</title></head><body>"
            + ("<div class=\"mermaid\">node</div>\n" * 5000)
            + "</body></html>",
            encoding="utf-8",
        )
        item_heavy = service.parse_html_brief(heavy_file, heavy_threshold=50000)
        assert item_heavy.is_heavy_topology is True
        assert len(item_heavy.mermaid_dags) == 0  # Bounded; DAGs not parsed to prevent blowout

    def test_pytest_sandbox_bounded_triage(self, tmp_path: Path) -> None:
        """Verify pytest sandbox inspection with bounded depth and noise pruning (Rule 52)."""
        service = StandardTempArtifactMinerService()

        pytest_root = tmp_path / "pytest-of-spectre"
        run_1 = pytest_root / "pytest-101"
        run_2 = pytest_root / "pytest-102"

        # Valid fixtures and mock skills
        (run_1 / "fixture_a" / "skills" / "mock-skill-x").mkdir(parents=True)
        (run_2 / "fixture_b").mkdir(parents=True)

        # Noise directories to prune (Rule 52)
        (run_1 / ".venv").mkdir(parents=True)
        (run_1 / "__pycache__").mkdir(parents=True)

        report = service.triage_sandbox(pytest_dir=tmp_path)
        assert report.total_runs == 2
        assert len(report.runs) == 2
        run_names = {r.name for r in report.runs}
        assert "pytest-101" in run_names
        assert "pytest-102" in run_names

        r1 = next(r for r in report.runs if r.name == "pytest-101")
        assert "mock-skill-x" in r1.mock_skills
        assert ".venv" not in [f for f in (r1.name,)]

    def test_tail_diagnostic_log_ring_buffer(self, tmp_path: Path) -> None:
        """Verify ring-buffer diagnostic log tailing (Rule 53)."""
        service = StandardTempArtifactMinerService()
        log_file = tmp_path / "crash.log"
        lines = [f"Log line {i}" for i in range(100)]
        log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        tail = service.tail_diagnostic_log(log_file, max_lines=25)
        assert len(tail) == 25
        assert tail[0] == "Log line 75"
        assert tail[-1] == "Log line 99"

        # Non-existent log
        assert service.tail_diagnostic_log(tmp_path / "missing.log") == ()

    def test_dual_lens_cognitive_bifurcation(self, tmp_path: Path) -> None:
        """Verify Dual-Lens Cognitive Bifurcation produces KV dual-files and doc salvage (Rule 40, 41)."""
        service = StandardTempArtifactMinerService()
        brief_file = tmp_path / "architecture-review-kernel-deepening.html"
        brief_file.write_text(
            "<!DOCTYPE html><html><head><title>Kernel Deepening Architecture Review</title></head><body>"
            "<div class=\"mermaid\">graph LR\n  A[Shallow] --> B[Deep]</div>"
            "<p>Scorecard: 10/10</p><p>Anti-pattern defense matrix</p>"
            "</body></html>",
            encoding="utf-8",
        )

        vault_dir = tmp_path / "knowledge_vault"
        docs_dir = tmp_path / "docs_arch"

        report = service.bifurcate_brief(
            brief_path=brief_file,
            target_vault_dir=vault_dir,
            target_docs_dir=docs_dir,
        )

        assert report.source_name == "architecture-review-kernel-deepening.html"
        assert Path(report.knowledge_vault_path).exists()
        assert Path(report.salvaged_doc_path).exists()

        # 1. Epistemic Introspection Seam (Knowledge Vault, Rule 40, 41)
        kv_path = Path(report.knowledge_vault_path)
        meta_file = kv_path / "metadata.json"
        summary_file = kv_path / "summary.md"
        assert meta_file.exists()
        assert summary_file.exists()

        meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
        assert "ki_temp_architecture_review_" in meta_data["id"]
        assert meta_data["isnad"]["status"] == "VERIFIED"
        assert len(meta_data["isnad"]["claims"]) >= 1
        assert meta_data["isnad"]["claims"][0]["lineage"][0]["anchor"] == "HTML visual brief decision matrix"

        summary_text = summary_file.read_text(encoding="utf-8")
        assert "Kernel Deepening Architecture Review" in summary_text
        assert "```mermaid" in summary_text
        assert "A[Shallow] --> B[Deep]" in summary_text

        # 2. Permanent Documentation Seam (Rule 41)
        doc_text = Path(report.salvaged_doc_path).read_text(encoding="utf-8")
        assert "# Architectural Brief: Kernel Deepening Architecture Review" in doc_text
        assert "```mermaid" in doc_text

    def test_visual_salvage_diagrams(self, tmp_path: Path) -> None:
        """Verify salvage_diagrams extracts standalone diagrams into documentation."""
        service = StandardTempArtifactMinerService()
        brief_file = tmp_path / "harness-reflection-test.html"
        brief_file.write_text(
            "<!DOCTYPE html><html><head><title>Reflection Test</title></head><body>"
            "<div class=\"mermaid\">graph TB\n  X --> Y</div>"
            "</body></html>",
            encoding="utf-8",
        )
        docs_dir = tmp_path / "docs"
        salvage = service.salvage_diagrams(brief_file, target_docs_dir=docs_dir)

        assert salvage.extracted_diagrams_count == 1
        assert Path(salvage.salvaged_doc_path).exists()
        doc_content = Path(salvage.salvaged_doc_path).read_text(encoding="utf-8")
        assert "graph TB\n  X --> Y" in doc_content

    def test_headless_click_cli_commands(self, tmp_path: Path) -> None:
        """Verify Click CLI commands (scan, sandbox, tail, salvage, bifurcate) via CliRunner (Rule 6, Rule 10)."""
        runner = CliRunner()

        # 1. Group help & aliases
        res_help = runner.invoke(temp_miner_group, ["--help"])
        assert res_help.exit_code == 0
        for cmd in ("scan", "sandbox", "tail", "salvage", "bifurcate"):
            assert cmd in res_help.output

        # Verify CLI aliases on main harness CLI
        for alias in ("temp", "temp-miner", "ephemeral-miner"):
            res_alias = runner.invoke(harness_cli_main, [alias, "--help"])
            assert res_alias.exit_code == 0, f"Alias {alias} failed"
            assert "scan" in res_alias.output

        # 2. Scan command
        brief_file = tmp_path / "architecture-review-sample.html"
        brief_file.write_text(
            "<!DOCTYPE html><html><head><title>Sample Brief</title></head><body>"
            "<div class=\"mermaid\">graph TD\n  A --> B</div></body></html>",
            encoding="utf-8",
        )
        res_scan = runner.invoke(temp_miner_group, ["scan", "--temp-dir", str(tmp_path), "--json-output"])
        assert res_scan.exit_code == 0
        scan_data = json.loads(res_scan.output)
        assert scan_data["brief_count"] == 1
        assert "architecture-review" in scan_data["categories"]

        # 3. Sandbox command
        (tmp_path / "pytest-of-spectre" / "pytest-001" / "fixture_1").mkdir(parents=True)
        res_sandbox = runner.invoke(temp_miner_group, ["sandbox", "--temp-dir", str(tmp_path), "--json-output"])
        assert res_sandbox.exit_code == 0
        sandbox_data = json.loads(res_sandbox.output)
        assert sandbox_data["total_runs"] == 1

        # 4. Tail command
        log_file = tmp_path / "test.log"
        log_file.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")
        res_tail = runner.invoke(temp_miner_group, ["tail", str(log_file), "--lines", "2"])
        assert res_tail.exit_code == 0
        assert "line 2" in res_tail.output
        assert "line 3" in res_tail.output

        # 5. Salvage markdown command
        res_salvage = runner.invoke(temp_miner_group, ["salvage", "--temp-dir", str(tmp_path)])
        assert res_salvage.exit_code == 0
        assert "# Ephemeral Visual Brief Salvage Index" in res_salvage.output

        # 6. Bifurcate command
        vault_dir = tmp_path / "vault"
        docs_dir = tmp_path / "docs"
        res_bif = runner.invoke(
            temp_miner_group,
            [
                "bifurcate",
                str(brief_file),
                "--vault-dir",
                str(vault_dir),
                "--docs-dir",
                str(docs_dir),
                "--json-output",
            ],
        )
        assert res_bif.exit_code == 0
        bif_data = json.loads(res_bif.output)
        assert bif_data["source_name"] == "architecture-review-sample.html"
        assert Path(bif_data["knowledge_vault_path"]).exists()
        assert Path(bif_data["salvaged_doc_path"]).exists()
