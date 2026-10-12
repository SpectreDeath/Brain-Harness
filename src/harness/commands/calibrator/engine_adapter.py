"""Engine adapter implementing CodingHarnessCalibratorService over standalone engine."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from harness.services.coding_harness_calibrator import (
    BudgetConfigData,
    CalibrationRecommendationData,
    CodingHarnessCalibratorService,
    ContextStagingSimulationData,
    HarnessCalibrationReportData,
    RepatchPredictionData,
)


def _ensure_scripts_path() -> None:
    ws_root = Path.cwd()
    skill_scripts = ws_root / ".agents" / "skills" / "coding-harness-calibrator" / "scripts"
    if skill_scripts.exists() and str(skill_scripts) not in sys.path:
        sys.path.insert(0, str(skill_scripts))


class CodingHarnessCalibratorEngineAdapter(CodingHarnessCalibratorService):
    """Adapter bridging standalone CodingHarnessCalibrator to typed service protocol."""

    def __init__(self) -> None:
        _ensure_scripts_path()
        from calibrator_engine import CodingHarnessCalibrator

        self._eng = CodingHarnessCalibrator()

    def calibrate(
        self,
        model_name: str,
        parameter_billions: float,
        workload: str,
        context_budget: int = 131072,
    ) -> CalibrationRecommendationData:
        _ensure_scripts_path()
        from calibrator_engine import WorkloadType

        wl = WorkloadType.TERMINAL_CLI if "cli" in workload.lower() else WorkloadType.CODEBASE_REPO
        rec = self._eng.calibrate(
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
        _ensure_scripts_path()
        from calibrator_engine import ContextStagingEvent

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
        rec_data = self.calibrate(model_name, parameter_billions, workload, context_budget)
        repatch_data = self.predict_repatch(parameter_billions, rec_data.action_space, workload)
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
        return self._eng.generate_visual_brief(report_or_rec=report_or_rec, output_path=output_path)
