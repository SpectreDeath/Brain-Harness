"""Deepened Architecture Verification Suite for AiNativeHarness.

Verifies:
1. Micro-Kernel Seam Elevation & IoC Container Resolution (AGENTS.md Rule 49, Rule 45)
2. PluginValidator & Manifest Contract Compliance (AGENTS.md Rule 34, Rule 38)
3. Slotted Dataclass Immutability Invariant (AGENTS.md Rule 12, Rule 43)
4. 4 Behavioral Verification Gates & Partial Payload Omission Audit
5. Credential-Free MCP Security Bridge & Uniform Leak Defense
6. Git Code-to-Doc Commit Drift Calculus & Badge Transitions
7. Negative Query Demand Mining & Documentation Backlog Clustering
8. Interactive HTML Visual Brief Generation (AGENTS.md Rule 51)
9. Top-Level Tool Entrypoints matching plugin.json
10. Headless Click CLI Command Seam Execution (AGENTS.md Rule 10, Rule 6)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

_ws_root = Path(__file__).resolve().parent.parent
_skill_scripts = (
    _ws_root / ".agents" / "skills" / "ai-native-harness-engineer" / "scripts"
)
_src = _ws_root / "src"

for _p in [_skill_scripts, _src, _ws_root]:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from ai_native_harness import (
    AiNativeHarnessAuditReport,
    AiNativeHarnessEngine,
    BehavioralGateResult,
    DocDriftItem,
    FourGatesEvaluation,
    HarnessDocDriftReport,
    McpSecurityCheck,
    NegativeBacklogReport,
)

from harness.cli import main
from harness.commands.gate import gate_group
from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.ai_native_harness import (
    AI_NATIVE_HARNESS_SERVICE_KEY,
    AiNativeHarnessAuditReportData,
    AiNativeHarnessService,
    FourGatesEvaluationData,
    HarnessDocDriftReportData,
    McpSecurityCheckData,
    NegativeBacklogReportData,
)
from plugins.agent_orchestration.ai_native_harness.main import (
    ai_native_harness_brief,
    doc_drift_audit,
    four_gates_evaluate,
    mcp_security_audit,
    negative_backlog_mine,
    plugin,
)

PLUGIN_DIR = (
    _ws_root
    / "plugins"
    / "agent_orchestration"
    / "ai_native_harness"
)


@pytest.mark.unit
class TestAiNativeHarnessPluginRegistration:
    """Verifies IoC container integration and plugin manifest conformity."""

    @pytest.mark.asyncio
    async def test_plugin_implements_protocol_and_registers_ioc(self) -> None:
        """Plugin satisfies AiNativeHarnessService and resolves via ServiceKey (Rule 49 & 45)."""
        assert isinstance(plugin, AiNativeHarnessService)
        assert plugin.name == "plugin.ai_native_harness"
        assert plugin.provides == [AI_NATIVE_HARNESS_SERVICE_KEY]
        assert plugin.requires == []

        ctx = ServiceContext()
        await plugin.on_load(ctx)

        resolved = ctx.require(AI_NATIVE_HARNESS_SERVICE_KEY)
        assert resolved is plugin

    def test_plugin_manifest_validation(self) -> None:
        """Plugin manifest complies with PluginValidator standards (Rule 34, Rule 38)."""
        report = PluginValidator.validate_sync(PLUGIN_DIR)
        assert report.valid is True, f"Plugin validation failed: {report.errors}"
        assert len(report.errors) == 0, f"Unexpected errors: {report.errors}"


@pytest.mark.unit
class TestSlottedDomainDataclasses:
    """Verifies memory-efficient slotted and frozen dataclass architecture (Rule 12, Rule 43)."""

    def test_frozen_dataclass_mutation_raises(self) -> None:
        """Direct attribute assignment must raise AttributeError/TypeError on frozen dataclass (Rule 43)."""
        gate = BehavioralGateResult(
            name="Gate 1: Static Type Checker",
            gate_number=1,
            passed=True,
            score=1.0,
            metrics={"type_errors": 0},
            details="Zero type errors",
            duration_ms=50.0,
        )
        with pytest.raises((AttributeError, TypeError)):
            gate.passed = False  # Direct assignment must be blocked

        drift_item = DocDriftItem(
            doc_slug="test-slug",
            doc_path="README.md",
            code_paths=["src/"],
            commits_since_doc_update=0,
            drift_count=0,
            status_badge="green",
        )
        with pytest.raises((AttributeError, TypeError)):
            drift_item.status_badge = "amber"

        mcp_chk = McpSecurityCheck(
            zero_stored_credentials=True,
            forward_user_tokens=True,
            dynamic_rbac_enabled=True,
            sanitized_403_forbidden=True,
            identical_404_leak_defense=True,
            human_sme_workflow_markers=True,
            passed=True,
            score=1.0,
            details={},
        )
        with pytest.raises((AttributeError, TypeError)):
            mcp_chk.zero_stored_credentials = False

    def test_slotted_memory_footprint(self) -> None:
        """Ensure __slots__ is defined on high-frequency domain dataclasses (Rule 12)."""
        gate = BehavioralGateResult(
            name="Gate 2", gate_number=2, passed=True, score=1.0, metrics={}, details=""
        )
        assert hasattr(gate, "__slots__")
        assert not hasattr(gate, "__dict__")


@pytest.mark.unit
class TestAiNativeHarnessEngine:
    """Verifies domain engine behavior across all 3 governance pillars."""

    @pytest.fixture
    def engine(self) -> AiNativeHarnessEngine:
        return AiNativeHarnessEngine(root_dir=_ws_root)

    def test_evaluate_four_gates(self, engine: AiNativeHarnessEngine) -> None:
        """Evaluate 4 behavioral gates and partial payload omission check."""
        result = engine.evaluate_gates()
        assert isinstance(result, FourGatesEvaluation)
        assert result.gate1_typecheck.gate_number == 1
        assert result.gate2_coverage.gate_number == 2
        assert result.gate3_e2e_simulation.gate_number == 3
        assert result.gate4_live_demo.gate_number == 4
        assert result.payload_omission_audit.passed is True
        assert 0.0 <= result.overall_score <= 1.0
        assert result.disallowed_lint_budget is True

        # Test dictionary serialization
        d = result.to_dict()
        assert "gate1_typecheck" in d
        assert "overall_score" in d
        validated = FourGatesEvaluationData.model_validate(d)
        assert validated.overall_score == round(result.overall_score, 2)

    def test_calculate_code_to_doc_drift(self, engine: AiNativeHarnessEngine) -> None:
        """Calculate Git code-to-doc commit drift count and verify status badges."""
        report = engine.calculate_code_to_doc_drift()
        assert isinstance(report, HarnessDocDriftReport)
        assert len(report.items) > 0
        assert report.total_drift_count >= 0
        assert report.green_count + report.amber_count == len(report.items)

        for it in report.items:
            assert it.status_badge in ("green", "amber")
            if it.drift_count == 0:
                assert it.status_badge == "green"
            else:
                assert it.status_badge == "amber"

        d = report.to_dict()
        validated = HarnessDocDriftReportData.model_validate(d)
        assert validated.total_drift_count == report.total_drift_count

    def test_audit_mcp_security(self, engine: AiNativeHarnessEngine) -> None:
        """Audit MCP server posture for zero credentials and uniform leak defense."""
        check = engine.audit_mcp_security()
        assert isinstance(check, McpSecurityCheck)
        assert check.zero_stored_credentials is True
        assert check.forward_user_tokens is True
        assert check.dynamic_rbac_enabled is True
        assert check.sanitized_403_forbidden is True
        assert check.identical_404_leak_defense is True
        assert check.human_sme_workflow_markers is True
        assert check.passed is True
        assert check.score == 1.0

        d = check.to_dict()
        validated = McpSecurityCheckData.model_validate(d)
        assert validated.passed is True

    def test_mine_negative_backlog(self, engine: AiNativeHarnessEngine) -> None:
        """Mine unanswered queries into demand-ranked documentation clusters."""
        custom_queries = [
            "How do I configure credential-free MCP tokens?",
            "Where are MCP credentials stored?",
            "Can I pass a user PAT through MCP?",
            "How does Gate 2 100% coverage check work?",
            "How do I run playwright in Gate 3?",
            "What is the code-to-doc drift formula?",
        ]
        report = engine.mine_negative_backlog(queries=custom_queries)
        assert isinstance(report, NegativeBacklogReport)
        assert report.total_unanswered_queries == 6
        assert report.total_clusters >= 3

        # Assert cluster ordering by demand count descending
        counts = [item.demand_count for item in report.items]
        assert counts == sorted(counts, reverse=True)

        d = report.to_dict()
        validated = NegativeBacklogReportData.model_validate(d)
        assert validated.total_unanswered_queries == 6

    def test_composite_audit(self, engine: AiNativeHarnessEngine) -> None:
        """Execute full composite audit across all 3 pillars."""
        report = engine.audit()
        assert isinstance(report, AiNativeHarnessAuditReport)
        assert report.target_path == str(_ws_root)
        assert "AI-Native Harness Audit completed" in report.summary
        assert report.operational_budgets_enforced is True

        d = report.to_dict()
        validated = AiNativeHarnessAuditReportData.model_validate(d)
        assert validated.summary == report.summary

    def test_visual_brief_generation(self, engine: AiNativeHarnessEngine, tmp_path: Path) -> None:
        """Render interactive HTML visual brief with Mermaid topology (Rule 51)."""
        brief_file = tmp_path / "test-brief.html"
        generated = engine.visual_brief(output_path=brief_file)
        assert generated.exists()
        content = generated.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "AI-Native Harness Governance Visual Brief" in content
        assert "GATE 1" in content
        assert "Pillar 2: Zero-Credential MCP Security Bridge" in content
        assert "Pillar 3: Code-to-Doc Drift Telemetry" in content


@pytest.mark.unit
class TestPluginTopLevelToolEntrypoints:
    """Verifies standalone top-level tool functions matching plugin.json entrypoints."""

    def test_four_gates_evaluate_tool(self) -> None:
        res = four_gates_evaluate()
        assert isinstance(res, dict)
        assert "gate1_typecheck" in res
        assert "overall_score" in res

    def test_doc_drift_audit_tool(self) -> None:
        res = doc_drift_audit()
        assert isinstance(res, dict)
        assert "total_drift_count" in res
        assert "items" in res

    def test_mcp_security_audit_tool(self) -> None:
        res = mcp_security_audit()
        assert isinstance(res, dict)
        assert "zero_stored_credentials" in res
        assert res["zero_stored_credentials"] is True

    def test_negative_backlog_mine_tool(self) -> None:
        res = negative_backlog_mine()
        assert isinstance(res, dict)
        assert "total_unanswered_queries" in res

    def test_ai_native_harness_brief_tool(self, tmp_path: Path) -> None:
        dest = str(tmp_path / "tool-brief.html")
        path_str = ai_native_harness_brief(output_path=dest)
        assert Path(path_str).exists()


@pytest.mark.unit
class TestHeadlessClickCLISeams:
    """Verifies Click CLI command execution and JSON outputs (Rule 10 & Rule 6)."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_gate_audit_cli(self, runner: CliRunner) -> None:
        res = runner.invoke(gate_group, ["audit"])
        assert res.exit_code == 0
        assert "=== AI-Native Harness Governance Audit ===" in res.output
        assert "4 Behavioral Gates:" in res.output

        # JSON mode
        res_json = runner.invoke(gate_group, ["audit", "--json"])
        assert res_json.exit_code == 0
        assert '"target_path":' in res_json.output

    def test_gate_evaluate_cli(self, runner: CliRunner) -> None:
        res = runner.invoke(gate_group, ["evaluate"])
        assert res.exit_code == 0
        assert "=== 4 Behavioral Verification Gates ===" in res.output
        assert "Gate 1 [Typecheck]:" in res.output

    def test_gate_mcp_cli(self, runner: CliRunner) -> None:
        res = runner.invoke(gate_group, ["mcp"])
        assert res.exit_code == 0
        assert "=== Credential-Free MCP Security Bridge ===" in res.output
        assert "Zero Stored Credentials:" in res.output

    def test_gate_drift_cli(self, runner: CliRunner) -> None:
        res = runner.invoke(gate_group, ["drift"])
        assert res.exit_code == 0
        assert "=== Code-to-Doc Drift Telemetry ===" in res.output
        assert "Total Drift Count:" in res.output

    def test_gate_mine_cli(self, runner: CliRunner) -> None:
        res = runner.invoke(gate_group, ["mine"])
        assert res.exit_code == 0
        assert "=== Unanswered Query Demand Backlog ===" in res.output
        assert "Topic Clusters:" in res.output

    def test_gate_brief_cli(self, runner: CliRunner, tmp_path: Path) -> None:
        out_file = str(tmp_path / "cli-brief.html")
        res = runner.invoke(gate_group, ["brief", "--output", out_file, "--no-open"])
        assert res.exit_code == 0
        assert "Visual brief generated at:" in res.output
        assert Path(out_file).exists()

    def test_cli_main_alias(self, runner: CliRunner) -> None:
        """Verify top-level alias `harness ai-native-harness`."""
        res = runner.invoke(main, ["ai-native-harness", "audit"])
        assert res.exit_code == 0
        assert "=== AI-Native Harness Governance Audit ===" in res.output
