"""Helper for visual brief generation bridging data classes to engine models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from harness.services.self_evaluating_pipeline import (
    RegressionReportData,
    StatisticalGateData,
)


def generate_visual_brief_via_engine(
    engine: Any,
    regression_data: RegressionReportData | dict[str, Any],
    gate_data: StatisticalGateData | dict[str, Any] | None = None,
    output_path: str | Path | None = None,
) -> Path:
    """Transform regression and gate data into engine models and generate visual brief."""
    from self_evaluating_pipeline_engine import (
        RegressionRunResult,
        StatisticalGatingDecision,
    )

    reg_dict = (
        regression_data.model_dump()
        if isinstance(regression_data, RegressionReportData)
        else regression_data
    )
    reg_obj = RegressionRunResult(
        run_id=reg_dict["run_id"],
        total_cases=reg_dict["total_cases"],
        passed_cases=reg_dict["passed_cases"],
        pass_rate=reg_dict["pass_rate"],
        layer1_pass_rate=reg_dict["layer1_pass_rate"],
        mean_score=reg_dict["mean_score"],
        scores=tuple(reg_dict["scores"]),
        failures=tuple(reg_dict["failures"]),
    )
    gate_obj = None
    if gate_data:
        g_dict = (
            gate_data.model_dump()
            if isinstance(gate_data, StatisticalGateData)
            else gate_data
        )
        gate_obj = StatisticalGatingDecision(
            p_value=g_dict["p_value"],
            t_statistic=g_dict["t_statistic"],
            mean_difference=g_dict["mean_difference"],
            sample_size=g_dict["sample_size"],
            is_significant=g_dict["is_significant"],
            is_improvement=g_dict["is_improvement"],
            decision=g_dict["decision"],
            justification=g_dict["justification"],
        )
    return engine.generate_visual_brief(
        reg_obj, gating_decision=gate_obj, output_path=output_path
    )
