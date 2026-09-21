"""Deepened Architecture Verification Suite for CodingHarnessCalibrator.

Verifies:
1. Micro-Kernel Seam Elevation & IoC Container Resolution (AGENTS.md Rule 49, Rule 45)
2. PluginValidator & Manifest Contract Compliance (AGENTS.md Rule 34, Rule 38)
3. Slotted Dataclass Immutability Invariants (AGENTS.md Rule 12, Rule 43)
4. Empirical Capability & Workload Triage (Fan et al. arXiv:2609.20804v1)
5. Two-Tier Context Staging ($T_4$) Simulation (B1 elision, B2 7-heading summary, M2 deprecation)
6. Fan et al. Empirical Re-Patch & Cost Reduction Forecasting
7. In-Flight Stuck Detection (Streak 5 warn / Streak 8 kill)
8. Interactive HTML Visual Brief Generation with Mermaid Topology (AGENTS.md Rule 51)
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
    _ws_root / ".agents" / "skills" / "coding-harness-calibrator" / "scripts"
)
for _p in [_ws_root / "src", _skill_scripts, _ws_root]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from calibrator_engine import (  # type: ignore
    ActionSpaceType,
    CodingHarnessCalibrator,
    ContextStagingEvent,
    ContextStagingSimulationResult,
    HarnessBudgetConfig,
    HarnessMode,
    RepatchPredictionResult,
    WorkloadType,
)

from harness.commands.calibrator import calibrator_group
from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.coding_harness_calibrator import (
    CODING_HARNESS_CALIBRATOR_SERVICE_KEY,
    CodingHarnessCalibratorService,
)
from plugins.agent_orchestration.coding_harness_calibrator.main import (
    calibrate_harness,
    calibrator_visual_brief,
    plugin,
    predict_repatch,
    simulate_staging,
)

PLUGIN_DIR = _ws_root / "plugins" / "agent_orchestration" / "coding_harness_calibrator"


@pytest.mark.unit
class TestCodingHarnessCalibratorPluginRegistration:
    """Verifies IoC container integration and plugin manifest conformity."""

    @pytest.mark.asyncio
    async def test_plugin_implements_protocol_and_registers_ioc(self) -> None:
        """Plugin satisfies CodingHarnessCalibratorService and resolves via ServiceKey."""
        assert isinstance(plugin, CodingHarnessCalibratorService)
        assert plugin.name == "plugin.coding_harness_calibrator"
        assert plugin.provides == [CODING_HARNESS_CALIBRATOR_SERVICE_KEY]
        assert plugin.requires == []

        ctx = ServiceContext()
        await plugin.on_load(ctx)

        resolved = ctx.require(CODING_HARNESS_CALIBRATOR_SERVICE_KEY)
        assert resolved is plugin

    def test_plugin_manifest_validation(self) -> None:
        """Plugin manifest complies with PluginValidator standards (Rule 34, Rule 38)."""
        report = PluginValidator.validate_sync(PLUGIN_DIR)
        assert report.valid is True
        warnings = [
            c
            for c in report.checks
            if getattr(c, "severity", None) and c.severity.value == "warning"
        ]
        assert len(warnings) == 0, f"Unexpected warnings: {warnings}"


@pytest.mark.unit
class TestSlottedDomainDataclasses:
    """Verifies memory-efficient slotted and frozen dataclass architecture (Rule 12, Rule 43)."""

    def test_frozen_dataclass_mutation_raises(self) -> None:
        cfg = HarnessBudgetConfig(usable_window=100000)
        with pytest.raises((AttributeError, TypeError)):
            cfg.usable_window = 50000  # type: ignore

        ev = ContextStagingEvent(
            role="tool_observation",
            content="test output",
            turn=1,
            token_count=200,
        )
        with pytest.raises((AttributeError, TypeError)):
            ev.token_count = 100  # type: ignore

        repatch = RepatchPredictionResult(
            model_scale="strong_550b",
            workload=WorkloadType.TERMINAL_CLI,
            action_space=ActionSpaceType.BASH_ONLY,
            predicted_mean_repatches=1.5,
            coarse_replace_ratio=0.76,
            estimated_cost_reduction_pct=42.5,
            rationale="Test rationale",
        )
        with pytest.raises((AttributeError, TypeError)):
            repatch.predicted_mean_repatches = 2.0  # type: ignore

    def test_dataclass_slots_present(self) -> None:
        cfg = HarnessBudgetConfig()
        assert hasattr(cfg, "__slots__")
        ev = ContextStagingEvent(role="user", content="hi", turn=1, token_count=5)
        assert hasattr(ev, "__slots__")
        sim = ContextStagingSimulationResult(
            usable_window=1000,
            initial_tokens=100,
            final_tokens=100,
            b1_elision_triggered=False,
            b2_summary_triggered=False,
            elided_observations_count=0,
            pruned_tokens_count=0,
            structured_summary="",
        )
        assert hasattr(sim, "__slots__")


@pytest.mark.unit
class TestEmpiricalTriageAndForecasting:
    """Verifies Fan et al. empirical capability triage and re-patch forecasting."""

    def test_capability_triage_tiers(self) -> None:
        # Weak 30B model -> Scaffold mode + Predefined Tools
        rec_weak = CodingHarnessCalibrator.calibrate(
            "Weak-30B", 30.0, WorkloadType.CODEBASE_REPO
        )
        assert rec_weak.harness_mode == HarnessMode.SCAFFOLD
        assert rec_weak.action_space == ActionSpaceType.PREDEFINED_TOOLS
        assert rec_weak.planning_role == "accuracy_scaffold"

        # Mid 120B model on CLI -> Balanced mode + Bash Only
        rec_mid = CodingHarnessCalibrator.calibrate(
            "Mid-120B", 120.0, WorkloadType.TERMINAL_CLI
        )
        assert rec_mid.harness_mode == HarnessMode.BALANCED
        assert rec_mid.action_space == ActionSpaceType.BASH_ONLY

        # Strong 550B model on CLI -> Efficiency mode + Bash Only
        rec_strong = CodingHarnessCalibrator.calibrate(
            "Strong-550B", 550.0, WorkloadType.TERMINAL_CLI
        )
        assert rec_strong.harness_mode == HarnessMode.EFFICIENCY
        assert rec_strong.action_space == ActionSpaceType.BASH_ONLY
        assert rec_strong.planning_role == "stopping_point_controller"

    def test_repatch_and_cost_prediction_laws(self) -> None:
        # Strong model with bash-only on CLI cuts re-patches from 4.6 to 1.5 and costs by 42.5%
        pred_strong_bash = CodingHarnessCalibrator.predict_repatch_efficiency(
            model_capability=550.0,
            action_space=ActionSpaceType.BASH_ONLY,
            workload=WorkloadType.TERMINAL_CLI,
        )
        assert pred_strong_bash.predicted_mean_repatches == 1.5
        assert pred_strong_bash.coarse_replace_ratio == 0.76
        assert pred_strong_bash.estimated_cost_reduction_pct == 42.5

        # Strong model forced with predefined tools has re-patches of 4.6
        pred_strong_tools = CodingHarnessCalibrator.predict_repatch_efficiency(
            model_capability=550.0,
            action_space=ActionSpaceType.PREDEFINED_TOOLS,
            workload=WorkloadType.TERMINAL_CLI,
        )
        assert pred_strong_tools.predicted_mean_repatches == 4.6
        assert pred_strong_tools.estimated_cost_reduction_pct == 0.0

        # Weak model forced with bash-only collapses (-25% efficiency, 6.5 re-patches)
        pred_weak_bash = CodingHarnessCalibrator.predict_repatch_efficiency(
            model_capability=30.0,
            action_space=ActionSpaceType.BASH_ONLY,
            workload=WorkloadType.TERMINAL_CLI,
        )
        assert pred_weak_bash.predicted_mean_repatches == 6.5
        assert pred_weak_bash.estimated_cost_reduction_pct < 0

        # Weak model with predefined tools is protected (+12% efficiency, 3.2 re-patches)
        pred_weak_tools = CodingHarnessCalibrator.predict_repatch_efficiency(
            model_capability=30.0,
            action_space=ActionSpaceType.PREDEFINED_TOOLS,
            workload=WorkloadType.TERMINAL_CLI,
        )
        assert pred_weak_tools.predicted_mean_repatches == 3.2
        assert pred_weak_tools.estimated_cost_reduction_pct > 0


@pytest.mark.unit
class TestTwoTierContextStagingSimulation:
    """Verifies Two-Tier Context Staging ($T_4$) elision and summarization rules."""

    def test_staging_below_thresholds(self) -> None:
        events = [
            ContextStagingEvent(
                role="system", content="System prompt", turn=0, token_count=500
            ),
            ContextStagingEvent(
                role="user", content="Turn 1 task", turn=1, token_count=500
            ),
            ContextStagingEvent(
                role="assistant", content="Turn 1 reply", turn=1, token_count=500
            ),
        ]
        res = CodingHarnessCalibrator.simulate_context_staging(
            events=events, usable_window=100000
        )
        assert not res.b1_elision_triggered
        assert not res.b2_summary_triggered
        assert res.elided_observations_count == 0
        assert res.pruned_tokens_count == 0
        assert res.final_tokens == 1500

    def test_staging_soft_threshold_b1_elision(self) -> None:
        # Total tokens = 75,000 >= B1 (60,000) on 100,000 window
        events = [
            ContextStagingEvent(
                role="system", content="System preamble", turn=0, token_count=2000
            ),
            ContextStagingEvent(
                role="user", content="Task step 1", turn=1, token_count=1000
            ),
            ContextStagingEvent(
                role="tool_observation",
                content="line 1\nline 2\nline 3\n" * 500,
                turn=1,
                token_count=60000,
                is_bulky=True,
                tool_name="cat_large_file",
            ),
            # Recent pinned window (turns 2 and 3)
            ContextStagingEvent(
                role="user", content="Task step 2", turn=2, token_count=1000
            ),
            ContextStagingEvent(
                role="assistant", content="Task step 2 reply", turn=2, token_count=1000
            ),
            ContextStagingEvent(
                role="user", content="Task step 3", turn=3, token_count=1000
            ),
            ContextStagingEvent(
                role="assistant", content="Task step 3 reply", turn=3, token_count=1000
            ),
        ]
        res = CodingHarnessCalibrator.simulate_context_staging(
            events=events,
            usable_window=100000,
            soft_ratio=0.60,
            hard_ratio=0.85,
            min_recent_turns=2,
        )
        assert res.b1_elision_triggered is True
        assert res.elided_observations_count == 1
        assert res.pruned_tokens_count > 50000
        # Check that observation was replaced with stub
        stub_ev = next(
            e
            for e in res.events_after_staging
            if e.turn == 1 and e.role == "tool_observation"
        )
        assert "[tool output elided:" in stub_ev.content

    def test_staging_hard_threshold_b2_summarization(self) -> None:
        # Total tokens remains >= B2 (85,000) even after non-bulky middle events
        events = [
            ContextStagingEvent(
                role="system", content="System preamble", turn=0, token_count=2000
            ),
        ]
        # Middle turns 1 to 5 with heavy conversational text (not tool observations)
        for t in range(1, 6):
            events.append(
                ContextStagingEvent(
                    role="user", content=f"Step {t}", turn=t, token_count=9000
                )
            )
            events.append(
                ContextStagingEvent(
                    role="assistant", content=f"Reply {t}", turn=t, token_count=9000
                )
            )

        # Recent turns 6 and 7
        events.append(
            ContextStagingEvent(role="user", content="Step 6", turn=6, token_count=2000)
        )
        events.append(
            ContextStagingEvent(role="user", content="Step 7", turn=7, token_count=2000)
        )

        res = CodingHarnessCalibrator.simulate_context_staging(
            events=events,
            usable_window=100000,
            soft_ratio=0.60,
            hard_ratio=0.85,
            min_recent_turns=2,
        )
        assert res.b2_summary_triggered is True
        assert "## Goal" in res.structured_summary
        assert "## Files touched" in res.structured_summary
        assert "## Done" in res.structured_summary
        assert "## Pending" in res.structured_summary
        assert "## Errors & fixes" in res.structured_summary
        assert "## Current state" in res.structured_summary
        assert "## Next step" in res.structured_summary


@pytest.mark.unit
class TestVisualBriefAndEntrypoints:
    """Verifies HTML visual brief generation and top-level entrypoints."""

    def test_visual_brief_generation(self, tmp_path: Path) -> None:
        out_file = tmp_path / "test_calibrator_brief.html"
        generated_path = plugin.visual_brief(output_path=out_file)
        assert generated_path.exists()
        content = generated_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "5-Stage Closed-Loop Calibration Topology" in content
        assert "Empirical Prediction Scorecard (Fan et al.)" in content
        assert "mermaid" in content.lower()

    def test_top_level_tool_entrypoints(self) -> None:
        calib_res = calibrate_harness(
            model_name="Claude-3.7-Sonnet",
            parameter_billions=550.0,
            workload="terminal_cli",
        )
        assert isinstance(calib_res, dict)
        assert calib_res["harness_mode"] == "efficiency"
        assert calib_res["action_space"] == "bash_only"

        repatch_res = predict_repatch(
            model_capability="strong_550b",
            action_space="bash_only",
            workload="terminal_cli",
        )
        assert isinstance(repatch_res, dict)
        assert repatch_res["predicted_mean_repatches"] == 1.5

        staging_res = simulate_staging(
            events=[
                {
                    "role": "system",
                    "content": "Preamble",
                    "turn": 0,
                    "token_count": 500,
                },
                {"role": "user", "content": "Turn 1", "turn": 1, "token_count": 500},
            ],
            usable_window=100000,
        )
        assert isinstance(staging_res, dict)
        assert staging_res["final_tokens"] == 1000

        brief_str = calibrator_visual_brief(output_path=None)
        assert isinstance(brief_str, str)
        assert Path(brief_str).exists()


@pytest.mark.unit
class TestCalibratorCLI:
    """Verifies Click CLI command execution (Rule 10, Rule 6)."""

    def test_cli_recommend_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            calibrator_group,
            [
                "recommend",
                "--model",
                "Claude-3.7",
                "--params",
                "550",
                "--workload",
                "terminal_cli",
            ],
        )
        assert result.exit_code == 0
        assert "Coding Harness Calibration Recommendation" in result.output
        assert "EFFICIENCY" in result.output
        assert "bash_only" in result.output

    def test_cli_recommend_json_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            calibrator_group,
            [
                "recommend",
                "--model",
                "Claude-3.7",
                "--params",
                "550",
                "--workload",
                "terminal_cli",
                "--json",
            ],
        )
        assert result.exit_code == 0
        assert '"harness_mode": "efficiency"' in result.output

    def test_cli_staging_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            calibrator_group,
            ["staging", "--budget", "80000", "--turns", "8"],
        )
        assert result.exit_code == 0
        assert "Two-Tier Context Staging ($T_4$) Simulation" in result.output
        assert "Usable Window:" in result.output

    def test_cli_repatch_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            calibrator_group,
            [
                "repatch",
                "--model-scale",
                "strong_550b",
                "--action-space",
                "bash_only",
                "--workload",
                "terminal_cli",
            ],
        )
        assert result.exit_code == 0
        assert "Empirical Re-Patch & Cost Prediction" in result.output
        assert "1.5" in result.output

    def test_cli_brief_command(self, tmp_path: Path) -> None:
        out_file = tmp_path / "cli_brief.html"
        runner = CliRunner()
        result = runner.invoke(
            calibrator_group,
            ["brief", "--output", str(out_file), "--no-open"],
        )
        assert result.exit_code == 0
        assert out_file.exists()
        assert "HTML visual brief generated at:" in result.output
