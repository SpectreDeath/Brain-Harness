"""Deepened Architecture Verification Suite for AgentHarnessArchitect.

Verifies:
1. Micro-Kernel Seam Elevation & IoC Container Resolution (AGENTS.md Rule 49, Rule 45)
2. PluginValidator & Manifest Contract Compliance (AGENTS.md Rule 34, Rule 38)
3. Slotted Dataclass Immutability Invariant (AGENTS.md Rule 12, Rule 43)
4. In-Memory 5-Part Harness Audit & 4-Layer Stack Boundary Verification (AGENTS.md Rule 49)
5. 4-Mechanism Reliability Scoring across Level 0 to Level 2
6. Architectural Bet Classification for 2026 Turnkey Harnesses
7. Interactive HTML Visual Brief Generation with Mermaid Topology (AGENTS.md Rule 51)
8. Top-Level Tool Entrypoints matching plugin.json
9. Headless Click CLI Command Seam Execution (AGENTS.md Rule 10, Rule 6)
"""

from __future__ import annotations

from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.commands.harness_architect import architect_group
from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.agent_harness import (
    AGENT_HARNESS_ARCHITECT_SERVICE_KEY,
    AgentHarnessArchitectService,
    ArchitecturalBetRecommendationData,
    FivePartHarnessAuditData,
    FourMechanismReliabilityGateData,
    HarnessAuditReportData,
)
from plugins.agent_orchestration.agent_harness_architect.main import (
    AgentHarnessArchitectPlugin,
    harness_audit,
    harness_classify_bet,
    harness_score,
    harness_visual_brief,
    plugin,
)
import sys
_ws_root = Path(__file__).resolve().parent.parent
_skill_scripts = (
    _ws_root / ".agents" / "skills" / "agent-harness-architect" / "scripts"
)
if str(_skill_scripts) not in sys.path:
    sys.path.insert(0, str(_skill_scripts))

from agent_harness_architect import (
    AgentHarnessArchitectEngine,
    ArchitecturalBetRecommendation,
    FivePartHarnessAudit,
    FourMechanismReliabilityGate,
    HarnessAuditReport,
    HarnessComponentStatus,
    MechanismReliabilityScore,
)

PLUGIN_DIR = (
    Path(__file__).resolve().parent.parent
    / "plugins"
    / "agent_orchestration"
    / "agent_harness_architect"
)


@pytest.mark.unit
class TestAgentHarnessArchitectPluginRegistration:
    """Verifies IoC container integration and plugin manifest conformity."""

    @pytest.mark.asyncio
    async def test_plugin_implements_protocol_and_registers_ioc(self) -> None:
        """Plugin satisfies AgentHarnessArchitectService and resolves via ServiceKey."""
        assert isinstance(plugin, AgentHarnessArchitectService)
        assert plugin.name == "plugin.agent_harness_architect"
        assert plugin.provides == [AGENT_HARNESS_ARCHITECT_SERVICE_KEY]
        assert plugin.requires == []

        ctx = ServiceContext()
        await plugin.on_load(ctx)

        resolved = ctx.require(AGENT_HARNESS_ARCHITECT_SERVICE_KEY)
        assert resolved is plugin

    def test_plugin_manifest_validation(self) -> None:
        """Plugin manifest complies with PluginValidator standards (Rule 34, Rule 38)."""
        report = PluginValidator.validate_sync(PLUGIN_DIR)
        assert report.valid is True, f"Plugin validation failed: {report.errors}"
        assert len(report.warnings) == 0, f"Unexpected warnings: {report.warnings}"


@pytest.mark.unit
class TestSlottedDomainDataclasses:
    """Verifies memory-efficient slotted and frozen dataclass architecture (Rule 12, Rule 43)."""

    def test_frozen_dataclass_mutation_raises(self) -> None:
        status = HarnessComponentStatus(
            name="Model Core",
            present=True,
            score=1.0,
            details="Test status",
        )
        with pytest.raises((AttributeError, TypeError)):
            status.score = 0.5  # Rule 43: Direct attribute assignment

    def test_dataclass_slots_and_serialization(self) -> None:
        score = MechanismReliabilityScore(
            name="Planning Gate",
            level=2,
            level_name="Production Gate",
            rationale="Approval gated",
            passed_l2_gate=True,
        )
        assert hasattr(score, "__slots__")
        d = score.to_dict()
        assert d["level"] == 2
        assert d["passed_l2_gate"] is True


@pytest.mark.unit
class TestInMemoryHarnessAuditAndReliabilityScoring:
    """Verifies 5-part architecture and 4-mechanism reliability scoring without subprocess CLI forks (Rule 49)."""

    @pytest.fixture
    def engine(self) -> AgentHarnessArchitectEngine:
        ws_root = Path(__file__).resolve().parent.parent
        return AgentHarnessArchitectEngine(root_dir=ws_root)

    def test_audit_execution(self, engine: AgentHarnessArchitectEngine) -> None:
        report = engine.audit()
        assert isinstance(report, HarnessAuditReport)
        assert report.five_part_audit.overall_score >= 0.80
        assert report.five_part_audit.passed is True
        assert report.five_part_audit.model_core.present is True
        assert report.five_part_audit.tool_router.present is True
        assert report.five_part_audit.planning_gate.present is True
        assert report.five_part_audit.sandbox_boundary.present is True

        # 4-Layer Stack Decoupling
        assert report.stack_audit.layer1_mcp is True
        assert report.stack_audit.layer2_harness is True
        assert report.stack_audit.layer3_orchestration is True
        assert report.stack_audit.layer4_observability_sandbox is True
        assert report.stack_audit.clean_boundaries is True

    def test_evaluate_reliability_default_gate(self, engine: AgentHarnessArchitectEngine) -> None:
        gate = engine.evaluate_reliability()
        assert isinstance(gate, FourMechanismReliabilityGate)
        assert gate.planning.passed_l2_gate is True
        assert gate.sandbox.passed_l2_gate is True
        assert gate.subagents.passed_l2_gate is True
        assert gate.compression.passed_l2_gate is True
        assert gate.observability.passed_l2_gate is True
        assert gate.meets_l2_production_gate is True

    def test_evaluate_reliability_toy_configuration(self, engine: AgentHarnessArchitectEngine) -> None:
        toy_cfg = {
            "harness_evaluation": {"enforce_planning_gate": False},
            "sandbox_policy": {"restrict_cwd": False, "allow_host_shell": True},
        }
        gate = engine.evaluate_reliability(toy_cfg)
        assert gate.planning.level == 1
        assert gate.sandbox.level == 0
        assert gate.meets_l2_production_gate is False

    def test_architectural_bet_classification(self, engine: AgentHarnessArchitectEngine) -> None:
        bet_mod = engine.classify_bet(bottleneck="Avoid vendor lock-in with swappable components")
        assert bet_mod.recommended_bet == "modularity"
        assert "deepseek-harness" in bet_mod.archetype_name

        bet_mem = engine.classify_bet(bottleneck="Eliminate cross-session amnesia with standing slack bot")
        assert bet_mem.recommended_bet == "compounding_memory"
        assert "hermes" in bet_mem.archetype_name

        bet_min = engine.classify_bet(bottleneck="Minimal lightweight audit surface for compliance")
        assert bet_min.recommended_bet == "radical_minimalism"
        assert "pi" in bet_min.archetype_name

        bet_rel = engine.classify_bet(bottleneck="Reliable multi-turn code refactoring with test pass")
        assert bet_rel.recommended_bet == "fixed_reliability"
        assert "claude-code" in bet_rel.archetype_name


@pytest.mark.unit
class TestVisualBriefAndEntrypoints:
    """Verifies HTML visual brief generation and top-level entrypoints."""

    def test_visual_brief_generation(self, tmp_path: Path) -> None:
        output_file = tmp_path / "test_harness_brief.html"
        generated_path = plugin.visual_brief(output_path=output_file)
        assert generated_path.exists()
        content = generated_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "Core 5-Part Harness Architecture" in content
        assert "4-Mechanism Reliability Scorecard" in content
        assert "mermaid" in content.lower()

    def test_top_level_tool_entrypoints(self) -> None:
        audit_res = harness_audit()
        assert isinstance(audit_res, dict)
        assert "five_part_audit" in audit_res
        assert audit_res["five_part_audit"]["passed"] is True

        score_res = harness_score()
        assert isinstance(score_res, dict)
        assert "meets_l2_production_gate" in score_res

        bet_res = harness_classify_bet(bottleneck="vendor lock-in")
        assert isinstance(bet_res, dict)
        assert bet_res["recommended_bet"] == "modularity"


@pytest.mark.unit
class TestHarnessArchitectCLI:
    """Verifies Click CLI command execution (Rule 10, Rule 6)."""

    def test_cli_audit_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(architect_group, ["audit"])
        assert result.exit_code == 0
        assert "Harness Architecture Audit" in result.output
        assert "5-Part Overall Score:" in result.output

    def test_cli_audit_json_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(architect_group, ["audit", "--json"])
        assert result.exit_code == 0
        assert '"five_part_audit"' in result.output

    def test_cli_score_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(architect_group, ["score"])
        assert result.exit_code == 0
        assert "4-Mechanism Reliability Scorecard" in result.output
        assert "Planning Gate" in result.output

    def test_cli_bet_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(architect_group, ["bet", "--bottleneck", "swappable modular components"])
        assert result.exit_code == 0
        assert "MODULARITY" in result.output

    def test_cli_brief_command(self, tmp_path: Path) -> None:
        out_file = tmp_path / "cli_brief.html"
        runner = CliRunner()
        result = runner.invoke(architect_group, ["brief", "--output", str(out_file), "--no-open"])
        assert result.exit_code == 0
        assert out_file.exists()
        assert "HTML visual brief generated at:" in result.output
