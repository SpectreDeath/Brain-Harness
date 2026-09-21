"""Coding Harness Calibrator commands — headless CLI and IoC service seams.

Provides CLI inspection for model capability triage, action space calibration,
Two-Tier Context Staging ($T_4$) simulation, Fan et al. empirical re-patch forecasting,
and HTML visual briefs.
"""

from __future__ import annotations

import json as _json
import sys
import webbrowser
from pathlib import Path
from typing import Any

import click
import structlog

from harness.kernel.context import ServiceContext
from harness.services.coding_harness_calibrator import (
    CODING_HARNESS_CALIBRATOR_SERVICE_KEY,
    CalibrationRecommendationData,
    CodingHarnessCalibratorService,
    ContextStagingSimulationData,
    HarnessCalibrationReportData,
    RepatchPredictionData,
)

logger = structlog.get_logger(__name__)


def get_calibrator_service(
    context: ServiceContext | None = None,
) -> CodingHarnessCalibratorService:
    """Resolve CodingHarnessCalibratorService from context or fall back to plugin singleton / engine adapter."""
    if context is not None:
        svc = context.optional(CODING_HARNESS_CALIBRATOR_SERVICE_KEY)
        if svc is not None:
            return svc

    # Lazy fallback to plugin singleton
    _ws_root = Path.cwd()
    if str(_ws_root) not in sys.path:
        sys.path.insert(0, str(_ws_root))
    if str(_ws_root / "src") not in sys.path:
        sys.path.insert(0, str(_ws_root / "src"))

    try:
        from plugins.agent_orchestration.coding_harness_calibrator.main import (
            plugin as calibrator_plugin,
        )

        return calibrator_plugin
    except Exception as exc:
        logger.warning(
            "coding_harness_calibrator_plugin_fallback_failed", error=str(exc)
        )
        # Direct fallback to CodingHarnessCalibrator in skill scripts
        skill_scripts = (
            _ws_root / ".agents" / "skills" / "coding-harness-calibrator" / "scripts"
        )
        if str(skill_scripts) not in sys.path:
            sys.path.insert(0, str(skill_scripts))
        from calibrator_engine import (  # type: ignore
            CodingHarnessCalibrator,
            WorkloadType,
        )

        class _EngineAdapter(CodingHarnessCalibratorService):
            def __init__(self) -> None:
                self._eng = CodingHarnessCalibrator()

            def calibrate(
                self,
                model_name: str,
                parameter_billions: float,
                workload: str,
                context_budget: int = 131072,
            ) -> CalibrationRecommendationData:
                wl = WorkloadType.CODEBASE_REPO
                if "cli" in workload.lower():
                    wl = WorkloadType.TERMINAL_CLI
                rec = self._eng.calibrate(
                    model_name=model_name,
                    parameter_billions=parameter_billions,
                    workload=wl,
                    context_budget=context_budget,
                )
                from harness.services.coding_harness_calibrator import BudgetConfigData

                b_data = BudgetConfigData(
                    usable_window=rec.budget_config.usable_window,
                    soft_threshold_ratio=rec.budget_config.soft_threshold_ratio,
                    hard_threshold_ratio=rec.budget_config.hard_threshold_ratio,
                    recent_window_ratio=rec.budget_config.recent_window_ratio,
                    min_recent_turns=rec.budget_config.min_recent_turns,
                    b1_tokens=rec.budget_config.b1_tokens,
                    b2_tokens=rec.budget_config.b2_tokens,
                )
                return CalibrationRecommendationData(
                    model_name=rec.model_name,
                    harness_mode=rec.harness_mode.value,
                    action_space=rec.action_space.value,
                    context_tier=rec.context_tier.value,
                    enable_planning=rec.enable_planning,
                    planning_role=rec.planning_role,
                    budget_config=b_data,
                    stuck_warn_threshold=rec.stuck_warn_threshold,
                    stuck_kill_threshold=rec.stuck_kill_threshold,
                    deprecation_flags=rec.deprecation_flags,
                )

            def simulate_staging(
                self,
                events: list[dict[str, Any]] | list[Any],
                usable_window: int = 131072,
                soft_ratio: float = 0.60,
                hard_ratio: float = 0.85,
            ) -> ContextStagingSimulationData:
                from calibrator_engine import ContextStagingEvent  # type: ignore

                converted = [
                    ContextStagingEvent(
                        role=e.get("role", "user"),
                        content=e.get("content", ""),
                        turn=int(e.get("turn", 1)),
                        token_count=int(e.get("token_count", 100)),
                        is_bulky=bool(e.get("is_bulky", False)),
                    )
                    for e in events
                ]
                sim = self._eng.simulate_context_staging(
                    events=converted,
                    usable_window=usable_window,
                    soft_ratio=soft_ratio,
                    hard_ratio=hard_ratio,
                )
                return ContextStagingSimulationData(
                    usable_window=sim.usable_window,
                    initial_tokens=sim.initial_tokens,
                    final_tokens=sim.final_tokens,
                    b1_elision_triggered=sim.b1_elision_triggered,
                    b2_summary_triggered=sim.b2_summary_triggered,
                    elided_observations_count=sim.elided_observations_count,
                    pruned_tokens_count=sim.pruned_tokens_count,
                    structured_summary=sim.structured_summary,
                )

            def predict_repatch(
                self,
                model_capability: str | float,
                action_space: str,
                workload: str,
            ) -> RepatchPredictionData:
                res = self._eng.predict_repatch_efficiency(
                    model_capability=model_capability,
                    action_space=action_space,
                    workload=workload,
                )
                return RepatchPredictionData(
                    model_scale=res.model_scale,
                    workload=res.workload.value,
                    action_space=res.action_space.value,
                    predicted_mean_repatches=res.predicted_mean_repatches,
                    coarse_replace_ratio=res.coarse_replace_ratio,
                    estimated_cost_reduction_pct=res.estimated_cost_reduction_pct,
                    rationale=res.rationale,
                )

            def generate_report(
                self,
                model_name: str,
                parameter_billions: float,
                workload: str,
                context_budget: int = 131072,
                events: list[Any] | None = None,
            ) -> HarnessCalibrationReportData:
                rec_data = self.calibrate(
                    model_name, parameter_billions, workload, context_budget
                )
                repatch_data = self.predict_repatch(
                    parameter_billions, rec_data.action_space, workload
                )
                return HarnessCalibrationReportData(
                    recommendation=rec_data,
                    repatch_prediction=repatch_data,
                    summary_narrative=f"Calibrated {model_name} for {workload}.",
                )

            def visual_brief(
                self,
                report_or_rec: Any | None = None,
                output_path: str | Path | None = None,
            ) -> Path:
                return self._eng.generate_visual_brief(
                    report_or_rec=report_or_rec, output_path=output_path
                )

        return _EngineAdapter()


@click.group("calibrator")
def calibrator_group() -> None:
    """Empirical coding harness component calibration, staging simulation, and forecasting."""


@calibrator_group.command("recommend")
@click.option(
    "--model",
    "-m",
    "model_name",
    default="Claude-3.7-Sonnet",
    help="Target model identifier",
)
@click.option(
    "--params",
    "-p",
    "parameter_billions",
    type=float,
    default=550.0,
    help="Model parameter size in billions (e.g. 30, 120, 550)",
)
@click.option(
    "--workload",
    "-w",
    default="codebase_repo",
    help="Workload type: terminal_cli | codebase_repo | mixed",
)
@click.option(
    "--budget",
    "-b",
    "context_budget",
    type=int,
    default=131072,
    help="Context window usable budget in tokens",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output recommendation as structured JSON",
)
def calibrator_recommend_cli(
    model_name: str,
    parameter_billions: float,
    workload: str,
    context_budget: int,
    as_json: bool,
) -> None:
    """Derive optimal empirical harness configuration across model tiers and workloads."""
    service = get_calibrator_service()
    rec = service.calibrate(
        model_name=model_name,
        parameter_billions=parameter_billions,
        workload=workload,
        context_budget=context_budget,
    )

    if as_json:
        click.echo(_json.dumps(rec.model_dump(), indent=2))
        return

    click.echo(
        click.style(
            "=== Coding Harness Calibration Recommendation ===", fg="cyan", bold=True
        )
    )
    click.echo(f"Model: {rec.model_name} ({parameter_billions}B parameters)")
    click.echo(f"Workload: {workload}")
    click.echo(
        f"Harness Operational Mode: "
        f"{click.style(rec.harness_mode.upper(), fg='green', bold=True)}"
    )
    click.echo(
        f"Action Space Interface: {click.style(rec.action_space, fg='yellow', bold=True)}"
    )
    click.echo(f"Context Staging Tier: {rec.context_tier} (Two-Tier Staging B1/B2)")
    click.echo(f"Planning Role: {rec.planning_role}")
    click.echo(
        f"Context Budget: {rec.budget_config.usable_window:,} tokens "
        f"(B1: {rec.budget_config.b1_tokens:,} / B2: {rec.budget_config.b2_tokens:,})"
    )
    click.echo(
        f"Stuck Detector: streak {rec.stuck_warn_threshold} warn / streak {rec.stuck_kill_threshold} kill"
    )
    if rec.deprecation_flags:
        click.echo(
            click.style(
                f"Pruned Machinery: {', '.join(rec.deprecation_flags)}", fg="magenta"
            )
        )


@calibrator_group.command("staging")
@click.option(
    "--budget",
    "-b",
    "usable_window",
    type=int,
    default=100000,
    help="Usable context window budget",
)
@click.option(
    "--turns",
    "-t",
    type=int,
    default=10,
    help="Number of turns to simulate",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output simulation result as structured JSON",
)
def calibrator_staging_cli(
    usable_window: int,
    turns: int,
    as_json: bool,
) -> None:
    """Simulate Two-Tier Context Staging ($T_4$) over an execution transcript."""
    service = get_calibrator_service()

    # Generate synthetic transcript turns to demonstrate B1 elision & B2 summarization
    events: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": "You are a calibrated autonomous coding assistant.",
            "turn": 0,
            "token_count": 2500,
            "is_bulky": False,
        }
    ]

    for turn_idx in range(1, turns + 1):
        events.append(
            {
                "role": "user",
                "content": f"Execute step {turn_idx} of repository refactoring task.",
                "turn": turn_idx,
                "token_count": 1200,
                "is_bulky": False,
            }
        )
        # Add tool calls and observations
        events.append(
            {
                "role": "tool_call",
                "content": f"read_file(path='module_{turn_idx}.py')",
                "turn": turn_idx,
                "token_count": 400,
                "is_bulky": False,
            }
        )
        # Add a bulky observation in middle turns
        is_bulky = turn_idx in (2, 3, 4, 5)
        obs_tokens = 15000 if is_bulky else 1500
        events.append(
            {
                "role": "tool_observation",
                "content": f"Source dump for module_{turn_idx} with {obs_tokens * 4} chars of code and symbols.",
                "turn": turn_idx,
                "token_count": obs_tokens,
                "is_bulky": is_bulky,
                "tool_name": "read_file",
            }
        )

    sim = service.simulate_staging(events=events, usable_window=usable_window)

    if as_json:
        click.echo(_json.dumps(sim.model_dump(), indent=2))
        return

    click.echo(
        click.style(
            "=== Two-Tier Context Staging ($T_4$) Simulation ===", fg="cyan", bold=True
        )
    )
    click.echo(f"Usable Window: {sim.usable_window:,} tokens")
    click.echo(f"Initial Token Count: {sim.initial_tokens:,} tokens")
    click.echo(
        f"Soft Threshold B1 (0.60) Elision: "
        f"{'TRIGGERED' if sim.b1_elision_triggered else 'NOT TRIGGERED'}"
    )
    click.echo(
        f"Hard Threshold B2 (0.85) Summary: "
        f"{'TRIGGERED' if sim.b2_summary_triggered else 'NOT TRIGGERED'}"
    )
    click.echo(f"Elided Bulky Observations: {sim.elided_observations_count}")
    click.echo(f"Pruned Tokens: {sim.pruned_tokens_count:,}")
    click.echo(
        f"Final Staged Tokens: {click.style(f'{sim.final_tokens:,}', fg='green', bold=True)} tokens"
    )
    if sim.structured_summary:
        click.echo("\nGenerated 7-Heading Structured Summary:")
        for line in sim.structured_summary.splitlines():
            click.echo(f"  {line}")


@calibrator_group.command("repatch")
@click.option(
    "--model-scale",
    "-m",
    default="strong_550b",
    help="Model scale: weak_30b | mid_120b | strong_550b",
)
@click.option(
    "--action-space",
    "-a",
    default="bash_only",
    help="Action space: predefined_tools | bash_only",
)
@click.option(
    "--workload",
    "-w",
    default="terminal_cli",
    help="Workload: terminal_cli | codebase_repo | mixed",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output prediction as structured JSON",
)
def calibrator_repatch_cli(
    model_scale: str,
    action_space: str,
    workload: str,
    as_json: bool,
) -> None:
    """Predict re-patch churn, action granularity, and cost reduction using Fan et al. empirical laws."""
    service = get_calibrator_service()
    pred = service.predict_repatch(
        model_capability=model_scale,
        action_space=action_space,
        workload=workload,
    )

    if as_json:
        click.echo(_json.dumps(pred.model_dump(), indent=2))
        return

    click.echo(
        click.style(
            "=== Empirical Re-Patch & Cost Prediction (Fan et al.) ===",
            fg="cyan",
            bold=True,
        )
    )
    click.echo(f"Model Scale: {pred.model_scale}")
    click.echo(f"Workload: {pred.workload}")
    click.echo(f"Action Space: {pred.action_space}")
    click.echo(
        f"Predicted Mean Re-patches: "
        f"{click.style(str(pred.predicted_mean_repatches), fg='green' if pred.predicted_mean_repatches <= 2.0 else 'yellow', bold=True)}"
    )
    click.echo(f"Coarse Action Ratio: {int(pred.coarse_replace_ratio * 100)}%")
    click.echo(
        f"Estimated Cost Reduction: "
        f"{click.style(f'{pred.estimated_cost_reduction_pct}%', fg='green' if pred.estimated_cost_reduction_pct > 0 else 'red', bold=True)}"
    )
    click.echo(f"\nEmpirical Rationale:\n  {pred.rationale}")


@calibrator_group.command("brief")
@click.option(
    "--model",
    "-m",
    "model_name",
    default="Claude-3.7-Sonnet",
    help="Target model identifier",
)
@click.option(
    "--params",
    "-p",
    "parameter_billions",
    type=float,
    default=550.0,
    help="Model parameter size in billions",
)
@click.option(
    "--workload",
    "-w",
    default="terminal_cli",
    help="Workload: terminal_cli | codebase_repo | mixed",
)
@click.option(
    "--output",
    "-o",
    default=None,
    help="Destination file path for generated HTML brief",
)
@click.option(
    "--open/--no-open",
    "open_browser",
    default=False,
    help="Open generated HTML brief in default browser",
)
def calibrator_brief_cli(
    model_name: str,
    parameter_billions: float,
    workload: str,
    output: str | None,
    open_browser: bool,
) -> None:
    """Generate interactive HTML visual brief with Mermaid topology and empirical scorecard."""
    service = get_calibrator_service()
    rec = service.calibrate(
        model_name=model_name,
        parameter_billions=parameter_billions,
        workload=workload,
    )
    out_path = service.visual_brief(report_or_rec=rec, output_path=output)
    click.echo(f"HTML visual brief generated at:\n  {out_path}")

    if open_browser:
        webbrowser.open(out_path.as_uri())
