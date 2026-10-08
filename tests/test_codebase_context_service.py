"""Unit and contract tests for CodebaseContextService and IoC micro-kernel seams.

Tests:
    1. Slotted and frozen dataclass immutability (Rule 12 & Rule 43)
    2. SemanticPathClassifier route and archetype discrimination
    3. IoC ServiceKey registration and resolution (Rule 1, Rule 2, Rule 49)
    4. Single-seam factory resolve_codebase_context (Rule 58)
    5. 5-Stage context governance pipeline & 5D compute tier assessment (Rule 25)
    6. Click CLI context govern command execution (Rule 10)
    7. CodebaseContextPlugin tool entrypoints
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.cli import main
from harness.kernel.context import ServiceContext
from harness.services.codebase_context import (
    CODEBASE_CONTEXT_SERVICE_KEY,
    CodebaseContextService,
    ContextGovernanceReport,
    ContextLintReport,
    ContextSmellViolation,
    DefaultCodebaseContextService,
    GovernanceStageResult,
    PathIntegrityCheck,
    ScriptIntegrityCheck,
    SemanticPathClassifier,
    SyncDriftCheck,
    SyncResult,
    TokenBudgetCheck,
    resolve_codebase_context,
)
from plugins.developer_tooling.codebase_context.main import (
    CodebaseContextPlugin,
    context_govern,
    context_lint,
    context_sync,
)


@pytest.mark.unit
class TestCodebaseContextDataclassImmutability:
    """Assert slotted and frozen dataclass invariants (Rule 12 & Rule 43)."""

    def test_token_budget_check_immutability(self) -> None:
        check = TokenBudgetCheck(
            file_path="AGENTS.md",
            token_count=100,
            token_ceiling=800,
            passed=True,
            message="OK",
        )
        with pytest.raises((AttributeError, TypeError)):
            check.passed = False  # type: ignore

    def test_path_integrity_check_immutability(self) -> None:
        check = PathIntegrityCheck(
            file_path="README.md",
            target_path="src/main.py",
            resolved_path="/abs/src/main.py",
            passed=True,
            message="OK",
        )
        with pytest.raises((AttributeError, TypeError)):
            check.target_path = "other.py"  # type: ignore

    def test_governance_report_immutability(self) -> None:
        stage = GovernanceStageResult(
            stage_num=1,
            stage_name="Test Stage",
            passed=True,
            duration_ms=2.5,
            message="Passed",
        )
        report = ContextGovernanceReport(
            workspace_root="/tmp/repo",
            passed=True,
            recommended_tier="High",
            stages=(stage,),
            violations=(),
        )
        with pytest.raises((AttributeError, TypeError)):
            report.passed = False  # type: ignore


@pytest.mark.unit
class TestSemanticPathClassifier:
    """Assert semantic classification distinguishes filesystem paths from API routes and archetypes."""

    def test_identifies_api_and_websocket_routes(self) -> None:
        assert SemanticPathClassifier.is_api_route("/api/health") is True
        assert SemanticPathClassifier.is_api_route("/api/plugins") is True
        assert SemanticPathClassifier.is_api_route("/ws/events") is True
        assert SemanticPathClassifier.is_api_route("/v1/chat") is True
        assert SemanticPathClassifier.is_api_route("/") is True
        assert SemanticPathClassifier.is_api_route("/metrics") is True

        # Non-API paths
        assert SemanticPathClassifier.is_api_route("src/harness/cli.py") is False
        assert SemanticPathClassifier.is_api_route("docs/HOWTO.md") is False

    def test_identifies_manifest_and_template_archetypes(self) -> None:
        assert SemanticPathClassifier.is_archetype_template("requirements.txt") is True
        assert SemanticPathClassifier.is_archetype_template("package.json") is True
        assert SemanticPathClassifier.is_archetype_template("main.py") is True
        assert SemanticPathClassifier.is_archetype_template("Makefile") is True
        assert SemanticPathClassifier.is_archetype_template("CARD.md") is True
        assert SemanticPathClassifier.is_archetype_template("SKILL.md") is True

        # Non-archetypes
        assert SemanticPathClassifier.is_archetype_template("src/custom_engine.py") is False


@pytest.mark.unit
class TestIoCRegistrationAndResolution:
    """Assert micro-kernel IoC service registration and fallback resolution (Rule 1, Rule 2, Rule 58)."""

    @pytest.mark.asyncio
    async def test_plugin_registers_into_ioc_context(self) -> None:
        ctx = ServiceContext()
        plugin = CodebaseContextPlugin()
        await plugin.on_load(ctx)

        resolved = ctx.require(CODEBASE_CONTEXT_SERVICE_KEY)
        assert isinstance(resolved, CodebaseContextService)

    def test_resolve_codebase_context_with_empty_context(self) -> None:
        ctx = ServiceContext()
        resolved = resolve_codebase_context(ctx)
        assert isinstance(resolved, CodebaseContextService)
        assert isinstance(resolved, DefaultCodebaseContextService)

    def test_resolve_codebase_context_without_context(self) -> None:
        resolved = resolve_codebase_context(None)
        assert isinstance(resolved, CodebaseContextService)


@pytest.mark.unit
class TestFiveStageContextGovernancePipeline:
    """Validate 5-stage context governance pipeline execution and 5D compute tier assessment."""

    def test_governance_pipeline_on_clean_repo(self, tmp_path: Path) -> None:
        (tmp_path / "AGENTS.md").write_text("# Root\nCommands: `npm test`\n", encoding="utf-8")
        service = DefaultCodebaseContextService(root=tmp_path)
        # Sync vendor files first so Stage 3 has zero drift
        service.sync(root=tmp_path, dry_run=False)

        report = service.govern(root=tmp_path, complexity_score=0.82)

        assert report.total_stages == 5
        assert report.passed == True
        assert report.recommended_tier == "High"

    def test_governance_pipeline_flags_bloat(self, tmp_path: Path) -> None:
        (tmp_path / "AGENTS.md").write_text("\n".join(f"Line {i}" for i in range(160)), encoding="utf-8")
        service = DefaultCodebaseContextService(root=tmp_path)
        report = service.govern(root=tmp_path, complexity_score=0.45)

        assert report.passed is False
        assert any(v.rule_name == "Instruction Line Budget" for v in report.violations)
        assert report.recommended_tier == "Medium"


@pytest.mark.unit
class TestClickContextGovernCommand:
    """Validate headless Click CLI harness context govern command (Rule 10)."""

    def test_click_context_govern_json_output(self, tmp_path: Path) -> None:
        (tmp_path / "AGENTS.md").write_text("# Root\nCommands: `npm test`\n", encoding="utf-8")
        # Sync vendor files so exit code is 0
        service = DefaultCodebaseContextService(root=tmp_path)
        service.sync(root=tmp_path, dry_run=False)

        runner = CliRunner()
        result = runner.invoke(main, ["context", "govern", "--root", str(tmp_path), "--complexity", "0.85", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["passed"] is True
        assert data["recommended_tier"] == "High"
        assert len(data["stages"]) == 5

    def test_plugin_tool_entrypoints(self, tmp_path: Path) -> None:
        (tmp_path / "AGENTS.md").write_text("# Root\nCommands: `npm test`\n", encoding="utf-8")
        lint_res = context_lint(root=str(tmp_path))
        assert lint_res["passed"] is True

        sync_res = context_sync(root=str(tmp_path), dry_run=True)
        assert "in_sync" in sync_res

        gov_res = context_govern(root=str(tmp_path), complexity=0.3)
        assert gov_res["recommended_tier"] == "Low"
