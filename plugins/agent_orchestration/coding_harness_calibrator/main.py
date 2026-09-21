"""Coding Harness Calibrator Plugin — Empirical component-level harness calibration.

Grounded in Fan et al. (arXiv:2609.20804v1, September 2026).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Dynamically ensure skill scripts directory is on sys.path
_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_SKILL_SCRIPTS = (
    _REPO_ROOT / ".agents" / "skills" / "coding-harness-calibrator" / "scripts"
)
_HARNESS_SRC = _REPO_ROOT / "src"

for _p in [_SKILL_SCRIPTS, _HARNESS_SRC]:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from calibrator_engine import (  # type: ignore
    ActionSpaceType,
    CalibrationRecommendation,
    CodingHarnessCalibrator,
    ContextStagingEvent,
    ContextTier,
    HarnessBudgetConfig,
    HarnessMode,
    WorkloadType,
)

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.coding_harness_calibrator import (
    CODING_HARNESS_CALIBRATOR_SERVICE_KEY,
    BudgetConfigData,
    CalibrationRecommendationData,
    CodingHarnessCalibratorService,
    ContextStagingEventData,
    ContextStagingSimulationData,
    HarnessCalibrationReportData,
    RepatchPredictionData,
)

logger = structlog.get_logger(__name__)


class CodingHarnessCalibratorPlugin(HarnessPlugin, CodingHarnessCalibratorService):
    """Plugin providing in-memory harness component calibration, staging simulation, and visual briefs."""

    def __init__(self, root_dir: Path | str | None = None) -> None:
        super().__init__()
        self._root = Path(root_dir or _REPO_ROOT).resolve()
        self._calibrator = CodingHarnessCalibrator()

    @property
    def name(self) -> str:
        return "plugin.coding_harness_calibrator"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Empirical component-level coding harness calibration across context staging, "
            "action spaces, and planning scaffolds"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [CODING_HARNESS_CALIBRATOR_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register self as the CodingHarnessCalibratorService into the IoC container."""
        context.provide(CODING_HARNESS_CALIBRATOR_SERVICE_KEY, self)
        logger.info(
            "coding_harness_calibrator_service_provided",
            service=str(CODING_HARNESS_CALIBRATOR_SERVICE_KEY),
        )

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    # --- CodingHarnessCalibratorService Implementation ---

    def calibrate(
        self,
        model_name: str,
        parameter_billions: float,
        workload: str,
        context_budget: int = 131072,
    ) -> CalibrationRecommendationData:
        """Derive optimal empirical harness configuration."""
        wl = WorkloadType.CODEBASE_REPO
        w_lower = workload.lower()
        if "cli" in w_lower or "terminal" in w_lower:
            wl = WorkloadType.TERMINAL_CLI
        elif "mixed" in w_lower:
            wl = WorkloadType.MIXED

        rec = self._calibrator.calibrate(
            model_name=model_name,
            parameter_billions=parameter_billions,
            workload=wl,
            context_budget=context_budget,
        )

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
        """Simulate Two-Tier Context Staging ($T_4$) over an event sequence."""
        converted_events: list[ContextStagingEvent] = []
        for ev in events:
            if isinstance(ev, ContextStagingEvent):
                converted_events.append(ev)
            elif isinstance(ev, dict):
                converted_events.append(
                    ContextStagingEvent(
                        role=ev.get("role", "user"),
                        content=ev.get("content", ""),
                        turn=int(ev.get("turn", 1)),
                        token_count=int(
                            ev.get("token_count", len(ev.get("content", "")) // 4)
                        ),
                        is_bulky=bool(ev.get("is_bulky", False)),
                        tool_name=ev.get("tool_name", ""),
                    )
                )

        sim_res = self._calibrator.simulate_context_staging(
            events=converted_events,
            usable_window=usable_window,
            soft_ratio=soft_ratio,
            hard_ratio=hard_ratio,
        )

        out_events = [
            ContextStagingEventData(
                role=e.role,
                content=e.content,
                turn=e.turn,
                token_count=e.token_count,
                is_bulky=e.is_bulky,
                tool_name=e.tool_name,
            )
            for e in sim_res.events_after_staging
        ]

        return ContextStagingSimulationData(
            usable_window=sim_res.usable_window,
            initial_tokens=sim_res.initial_tokens,
            final_tokens=sim_res.final_tokens,
            b1_elision_triggered=sim_res.b1_elision_triggered,
            b2_summary_triggered=sim_res.b2_summary_triggered,
            elided_observations_count=sim_res.elided_observations_count,
            pruned_tokens_count=sim_res.pruned_tokens_count,
            structured_summary=sim_res.structured_summary,
            events_after_staging=out_events,
        )

    def predict_repatch(
        self,
        model_capability: str | float,
        action_space: str,
        workload: str,
    ) -> RepatchPredictionData:
        """Predict mean re-patches per task and cost reductions."""
        res = self._calibrator.predict_repatch_efficiency(
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
        """Synthesize aggregate calibration report."""
        rec_data = self.calibrate(
            model_name=model_name,
            parameter_billions=parameter_billions,
            workload=workload,
            context_budget=context_budget,
        )
        repatch_data = self.predict_repatch(
            model_capability=parameter_billions,
            action_space=rec_data.action_space,
            workload=workload,
        )

        staging_data: ContextStagingSimulationData | None = None
        if events:
            staging_data = self.simulate_staging(
                events=events,
                usable_window=context_budget,
            )

        narrative = (
            f"Calibrated {model_name} ({parameter_billions}B) for {workload} workload. "
            f"Mode: {rec_data.harness_mode}, Action Space: {rec_data.action_space}. "
            f"Predicted re-patches: {repatch_data.predicted_mean_repatches}, "
            f"Cost reduction: {repatch_data.estimated_cost_reduction_pct}%."
        )

        return HarnessCalibrationReportData(
            recommendation=rec_data,
            repatch_prediction=repatch_data,
            staging_simulation=staging_data,
            summary_narrative=narrative,
        )

    def visual_brief(
        self,
        report_or_rec: Any | None = None,
        output_path: str | Path | None = None,
    ) -> Path:
        """Generate interactive HTML visual brief with Mermaid topology."""
        if report_or_rec is None:
            report_or_rec = self._calibrator.calibrate(
                model_name="Frontier-Coding-Agent",
                parameter_billions=550.0,
                workload=WorkloadType.TERMINAL_CLI,
            )
        elif isinstance(report_or_rec, CalibrationRecommendationData):
            # Convert back to engine dataclass
            cfg = HarnessBudgetConfig(
                usable_window=report_or_rec.budget_config.usable_window,
                soft_threshold_ratio=report_or_rec.budget_config.soft_threshold_ratio,
                hard_threshold_ratio=report_or_rec.budget_config.hard_threshold_ratio,
            )
            report_or_rec = CalibrationRecommendation(
                model_name=report_or_rec.model_name,
                harness_mode=HarnessMode(report_or_rec.harness_mode),
                action_space=ActionSpaceType(report_or_rec.action_space),
                context_tier=ContextTier(report_or_rec.context_tier),
                enable_planning=report_or_rec.enable_planning,
                planning_role=report_or_rec.planning_role,
                budget_config=cfg,
                deprecation_flags=report_or_rec.deprecation_flags,
            )

        return self._calibrator.generate_visual_brief(
            report_or_rec=report_or_rec,
            output_path=output_path,
        )


# Rule 45: Export module singleton plugin instance
plugin = CodingHarnessCalibratorPlugin()


# Top-level entrypoints matching plugin.json tool declarations
def calibrate_harness(
    model_name: str,
    parameter_billions: float,
    workload: str = "codebase_repo",
    context_budget: int = 131072,
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level entrypoint for calibrate_harness tool invocation."""
    rec = plugin.calibrate(
        model_name=model_name,
        parameter_billions=parameter_billions,
        workload=workload,
        context_budget=context_budget,
    )
    return rec.model_dump()


def simulate_staging(
    events: list[dict[str, Any]],
    usable_window: int = 131072,
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level entrypoint for simulate_staging tool invocation."""
    sim = plugin.simulate_staging(events=events, usable_window=usable_window)
    return sim.model_dump()


def predict_repatch(
    model_capability: str | float,
    action_space: str,
    workload: str = "codebase_repo",
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level entrypoint for predict_repatch tool invocation."""
    res = plugin.predict_repatch(
        model_capability=model_capability,
        action_space=action_space,
        workload=workload,
    )
    return res.model_dump()


def calibrator_visual_brief(
    model_name: str = "Frontier-Coding-Agent",
    parameter_billions: float = 550.0,
    workload: str = "terminal_cli",
    output_path: str | None = None,
    **kwargs: Any,
) -> str:
    """Top-level entrypoint for calibrator_visual_brief tool invocation."""
    rec = plugin.calibrate(
        model_name=model_name,
        parameter_billions=parameter_billions,
        workload=workload,
    )
    res = plugin.visual_brief(report_or_rec=rec, output_path=output_path)
    return str(res)
