"""Contract tests for Cycle 70: Codebase Context Service Decomposition."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.services.codebase_context import (
    BANNER_TEMPLATE,
    CODEBASE_CONTEXT_SERVICE_KEY,
    CheckResult,
    CodebaseContextService,
    ConfigResolver,
    ContextGovernanceReport,
    ContextGovernor,
    ContextLintReport,
    ContextLinter,
    ContextSmellViolation,
    ContextSynchronizer,
    DEFAULT_CLAUDE_EXTRAS,
    DefaultCodebaseContextService,
    GovernanceStageResult,
    ManifestScriptInspector,
    PathIntegrityCheck,
    ScriptIntegrityCheck,
    SemanticPathClassifier,
    SyncDriftCheck,
    SyncResult,
    TokenBudgetCheck,
    resolve_codebase_context,
)
from harness.services.codebase_context.checks import (
    ContextLintReport as ModularLintReport,
    TokenBudgetCheck as ModularTokenBudgetCheck,
)
from harness.services.codebase_context.classifier import (
    SemanticPathClassifier as ModularClassifier,
)
from harness.services.codebase_context.config import (
    ConfigResolver as ModularConfigResolver,
)
from harness.services.codebase_context.governor import (
    ContextGovernor as ModularGovernor,
)
from harness.services.codebase_context.linter import (
    ContextLinter as ModularLinter,
)
from harness.services.codebase_context.manifest import (
    ManifestScriptInspector as ModularInspector,
)
from harness.services.codebase_context.protocol import (
    CODEBASE_CONTEXT_SERVICE_KEY as ModularServiceKey,
    CodebaseContextService as ModularProtocol,
)
from harness.services.codebase_context.reports import (
    ContextGovernanceReport as ModularGovernanceReport,
    ContextSmellViolation as ModularSmellViolation,
)
from harness.services.codebase_context.resolvers import (
    resolve_codebase_context as modular_resolve,
)
from harness.services.codebase_context.service import (
    DefaultCodebaseContextService as ModularDefaultService,
)
from harness.services.codebase_context.synchronizer import (
    ContextSynchronizer as ModularSynchronizer,
)


def test_submodule_line_count_bounds():
    """Rule 11: All submodules in codebase_context/ must not exceed 200 lines."""
    service_dir = Path(__file__).resolve().parent.parent / "src" / "harness" / "services" / "codebase_context"
    assert service_dir.is_dir(), f"Directory not found: {service_dir}"

    submodules = list(service_dir.glob("*.py"))
    assert len(submodules) >= 10, f"Expected at least 10 submodules, found {len(submodules)}"

    for py_file in submodules:
        lines = py_file.read_text(encoding="utf-8").splitlines()
        line_count = len(lines)
        assert line_count <= 200, f"{py_file.name} exceeded line limit: {line_count} > 200 lines"


def test_modular_exports_and_aliases():
    """Verify facade re-exports match granular submodules."""
    assert ModularTokenBudgetCheck is TokenBudgetCheck
    assert ModularLintReport is ContextLintReport
    assert ModularSmellViolation is ContextSmellViolation
    assert ModularGovernanceReport is ContextGovernanceReport
    assert ModularClassifier is SemanticPathClassifier
    assert ModularInspector is ManifestScriptInspector
    assert ModularConfigResolver is ConfigResolver
    assert ModularProtocol is CodebaseContextService
    assert ModularServiceKey is CODEBASE_CONTEXT_SERVICE_KEY
    assert ModularLinter is ContextLinter
    assert ModularSynchronizer is ContextSynchronizer
    assert ModularGovernor is ContextGovernor
    assert ModularDefaultService is DefaultCodebaseContextService
    assert modular_resolve is resolve_codebase_context


def test_slotted_frozen_dataclass_architecture():
    """Rule 12 & Rule 43: Slotted and frozen dataclass architecture."""
    # Check slots
    for cls in (TokenBudgetCheck, PathIntegrityCheck, ScriptIntegrityCheck, SyncDriftCheck,
                ContextLintReport, SyncResult, ContextSmellViolation, GovernanceStageResult, ContextGovernanceReport):
        assert hasattr(cls, "__slots__"), f"{cls.__name__} missing __slots__"

    # Check immutability
    check = TokenBudgetCheck("AGENTS.md", 100, 800, True, "OK")
    with pytest.raises((AttributeError, TypeError)):
        check.token_count = 200  # type: ignore

    violation = ContextSmellViolation("Rule", "AGENTS.md", 10, "Defect", "ERROR")
    with pytest.raises((AttributeError, TypeError)):
        violation.severity = "WARNING"  # type: ignore


def test_semantic_classifier_routes_and_archetypes():
    """Verify RFC MIME types, API routes, and archetypes classification."""
    assert SemanticPathClassifier.is_mime_type("application/json") is True
    assert SemanticPathClassifier.is_mime_type("text/plain") is True
    assert SemanticPathClassifier.is_mime_type("not-a-mime") is False

    assert SemanticPathClassifier.is_api_route("/api/health") is True
    assert SemanticPathClassifier.is_api_route("/ws/events") is True
    assert SemanticPathClassifier.is_api_route("src/code.py") is False

    assert SemanticPathClassifier.is_archetype_template("package.json") is True
    assert SemanticPathClassifier.is_archetype_template("CARD.md") is True
    assert SemanticPathClassifier.is_archetype_template("custom_module.py") is False


def test_manifest_script_extraction(tmp_path: Path):
    """Verify script extraction from polyglot project manifests."""
    # Empty root
    scripts = ManifestScriptInspector.extract_available_scripts(tmp_path)
    assert isinstance(scripts, set)

    # Node package.json
    (tmp_path / "package.json").write_text('{"scripts": {"build:prod": "tsc", "lint": "eslint"}}', encoding="utf-8")
    scripts = ManifestScriptInspector.extract_available_scripts(tmp_path)
    assert "build:prod" in scripts
    assert "lint" in scripts
    assert "test" in scripts  # npm default


def test_3tier_config_resolution(tmp_path: Path):
    """Rule 44: 3-tier zero-fork configuration resolution."""
    config = ConfigResolver.resolve_config(tmp_path)
    assert config["chars_per_token"] == 4
    assert "AGENTS.md" in config["budgets"]
    assert config["budgets"]["AGENTS.md"] == 800


def test_linter_and_synchronizer(tmp_path: Path):
    """Verify linter execution and synchronization rendering."""
    (tmp_path / "AGENTS.md").write_text("# Test Architecture\nInline `tests/test_code.py` path\n", encoding="utf-8")
    service = DefaultCodebaseContextService(root=tmp_path)

    # Linter
    report = service.lint()
    assert isinstance(report, ContextLintReport)
    assert report.checks_count > 0

    # Synchronizer
    claude_md = service.render_claude_md("AGENTS.md")
    assert "@AGENTS.md" in claude_md
    assert "Claude Code specific" in claude_md


def test_five_stage_governance_and_compute_tier(tmp_path: Path):
    """Verify 5-stage governance pipeline and dynamic compute tier (Rule 25)."""
    (tmp_path / "AGENTS.md").write_text("# Test\n`npm test`\n", encoding="utf-8")
    service = DefaultCodebaseContextService(root=tmp_path)

    # Low complexity
    stage_low, tier_low = service.assess_compute_tier(0.2)
    assert tier_low == "Low"
    assert stage_low.passed is True

    # High complexity (Rule 25)
    stage_high, tier_high = service.assess_compute_tier(0.85)
    assert tier_high == "High"
    assert stage_high.details["timeout_seconds"] == 300

    report = service.govern(complexity_score=0.5)
    assert isinstance(report, ContextGovernanceReport)
    assert len(report.stages) == 5


def test_single_seam_resolver(tmp_path: Path):
    """Rule 58: Single-seam resolver resolution."""
    resolved_none = resolve_codebase_context(None, root=tmp_path)
    assert isinstance(resolved_none, CodebaseContextService)

    ctx = ServiceContext()
    ctx.provide(CODEBASE_CONTEXT_SERVICE_KEY, resolved_none, provider="test")
    resolved_ctx = resolve_codebase_context(ctx, root=tmp_path)
    assert resolved_ctx is resolved_none
