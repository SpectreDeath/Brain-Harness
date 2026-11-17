"""Contract tests for CISC confidence-weighted voting and UQ shift calibration in UncertaintyGuard."""

from __future__ import annotations

import math
from pathlib import Path
import sys

import pytest

_WS_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = _WS_ROOT / ".agents" / "skills" / "uncertainty-aware-ai-architect" / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from harness.commands.uncertainty.resolver import get_uncertainty_service
from harness.kernel.context import ServiceContext
from harness.services.uncertainty_guard import (
    UNCERTAINTY_GUARD_SERVICE_KEY,
    UncertaintyGuardService,
)
from plugins.agent_orchestration.uncertainty_guard.main import plugin as guard_plugin


@pytest.mark.unit
def test_cisc_softmax_voting_overrides_low_confidence_majority_and_keeps_zero_conf() -> None:
    """High-confidence minority traces outweigh noisy low-confidence majority; 0.0 is valid, NaN is dropped."""
    from uncertainty_guard_engine import ConfidenceVotingResult, UncertaintyGuardEngine

    engine = UncertaintyGuardEngine()
    # Unweighted count favors "B" (3 votes) over "A" (2 votes), plus a NaN trace to filter.
    # Valid 0.0 confidence must remain counted rather than discarded.
    answers = ["B", "B", "B", "A", "A", "A"]
    confidences = [0.0, 0.1, 0.1, 0.95, 0.92, float("nan")]

    res = engine.aggregate_confidence_votes(
        answers,
        confidences,
        normalization="softmax",
        temperature=2.0,
    )
    assert isinstance(res, ConfidenceVotingResult)
    assert res.chosen_answer == "A"
    assert res.valid_trace_count == 5
    assert res.total_trace_count == 6
    assert 0.5 < res.confidence <= 1.0

    with pytest.raises((AttributeError, TypeError)):
        res.chosen_answer = "B"  # type: ignore[misc]


@pytest.mark.unit
def test_cisc_only_tie_break_respects_unique_plurality_and_breaks_ties() -> None:
    """only_tie_break=True preserves strict unweighted majority and uses confidence only on ties."""
    from uncertainty_guard_engine import UncertaintyGuardEngine

    engine = UncertaintyGuardEngine()
    # Strict majority for "B" (3 vs 2) stays "B" even when "A" has higher confidence
    res_plurality = engine.aggregate_confidence_votes(
        ["B", "B", "B", "A", "A"],
        [0.1, 0.1, 0.1, 0.99, 0.99],
        normalization="linear",
        only_tie_break=True,
    )
    assert res_plurality.chosen_answer == "B"

    # Tie (2 vs 2) is broken by confidence in favor of "A"
    res_tie = engine.aggregate_confidence_votes(
        ["B", "B", "A", "A"],
        [0.2, 0.2, 0.85, 0.9],
        normalization="linear",
        only_tie_break=True,
    )
    assert res_tie.chosen_answer == "A"


@pytest.mark.unit
def test_cisc_empty_or_all_nan_returns_none_safely() -> None:
    """All-invalid inputs return chosen_answer=None without raising."""
    from uncertainty_guard_engine import UncertaintyGuardEngine

    engine = UncertaintyGuardEngine()
    res = engine.aggregate_confidence_votes(
        ["", "A"],
        [0.9, float("nan")],
        normalization="softmax",
    )
    assert res.chosen_answer is None
    assert res.valid_trace_count == 0
    assert res.confidence == 0.0


@pytest.mark.unit
def test_uq_calibration_brier_decomposition_and_selectivity_sweep() -> None:
    """Verify ECE, Murphy Brier identity (uncertainty - resolution + reliability == brier), and threshold sweep."""
    from uncertainty_guard_engine import UncertaintyCalibrationReport, UncertaintyGuardEngine

    engine = UncertaintyGuardEngine()
    # 6 samples: confident ones are accurate, uncertain ones make errors, including exact 0.0 edge prob
    probs = [
        [0.95, 0.05],
        [0.90, 0.10],
        [0.15, 0.85],
        [0.55, 0.45],
        [0.60, 0.40],
        [0.0, 1.0],
    ]
    labels = [0, 0, 1, 1, 1, 1]

    report = engine.evaluate_uncertainty_calibration(
        probs,
        labels,
        bins=5,
        thresholds=(0.5, 0.8),
    )
    assert isinstance(report, UncertaintyCalibrationReport)
    assert 0.0 <= report.ece <= 1.0
    assert 0.0 <= report.brier_uncertainty <= 1.0
    assert report.brier_resolution >= 0.0
    assert report.brier_reliability >= 0.0
    assert 0.0 <= report.brier_score <= 2.0
    assert len(report.selectivity_curve) == 2
    p_low, p_high = report.selectivity_curve
    assert p_high.coverage_count <= p_low.coverage_count
    assert p_high.accuracy >= p_low.accuracy

    # When forecasts are constant within each predicted class, Murphy's identity holds identically
    discrete_probs = [[0.8, 0.2], [0.8, 0.2], [0.1, 0.9], [0.1, 0.9]]
    discrete_labels = [0, 1, 1, 1]
    disc_report = engine.evaluate_uncertainty_calibration(discrete_probs, discrete_labels, bins=4)
    assert math.isclose(
        disc_report.brier_score,
        disc_report.brier_uncertainty - disc_report.brier_resolution + disc_report.brier_reliability,
        rel_tol=1e-5,
        abs_tol=1e-6,
    )

    with pytest.raises((AttributeError, TypeError)):
        report.ece = 0.0  # type: ignore[misc]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ioc_plugin_and_cli_adapter_expose_cisc_and_uq_seams() -> None:
    """Both UncertaintyGuardPlugin and UncertaintyEngineAdapter conform to updated UncertaintyGuardService."""
    ctx = ServiceContext()
    await guard_plugin.on_load(ctx)
    svc = ctx.require(UNCERTAINTY_GUARD_SERVICE_KEY)
    assert isinstance(svc, UncertaintyGuardService)

    fallback = get_uncertainty_service(None)
    assert isinstance(fallback, UncertaintyGuardService)

    for provider in (svc, fallback):
        vote = provider.aggregate_confidence_votes(
            ["opt_a", "opt_a", "opt_b"],
            [0.2, 0.2, 0.99],
            normalization="softmax",
            temperature=4.0,
        )
        assert vote.chosen_answer == "opt_b"
        cal = provider.evaluate_uncertainty_calibration(
            [0.9, 0.8, 0.2, 0.1],
            [1, 1, 0, 0],
            bins=4,
            thresholds=(0.5, 0.85),
        )
        assert 0.0 <= cal.ece <= 1.0
        assert math.isclose(cal.brier_score, 0.05, abs_tol=1e-6)

    await guard_plugin.on_unload(ctx)
