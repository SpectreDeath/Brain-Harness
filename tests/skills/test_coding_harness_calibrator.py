"""Tests for the coding-harness-calibrator skill, calibration engine, and Knowledge Item."""

import json

# Import engine from skill scripts
import sys
from pathlib import Path

import pytest

from harness.creator.skills import SkillValidator
from harness.services.skill_graph import BuiltinSkillRegistryService

skill_scripts = (
    Path(__file__).parents[2]
    / ".agents"
    / "skills"
    / "coding-harness-calibrator"
    / "scripts"
)
sys.path.insert(0, str(skill_scripts))

from calibrator_engine import (  # type: ignore
    ActionSpaceType,
    CalibrationRecommendation,
    CodingHarnessCalibrator,
    ContextTier,
    HarnessBudgetConfig,
    HarnessMode,
    StuckDetector,
    WorkloadType,
)

# ---------------------------------------------------------------------------
# 1. Dataclass Immutability & Mathematical Bounds (Rule 12 & Rule 43)
# ---------------------------------------------------------------------------


def test_budget_config_immutability() -> None:
    cfg = HarnessBudgetConfig(
        usable_window=131072, soft_threshold_ratio=0.60, hard_threshold_ratio=0.85
    )
    assert cfg.b1_tokens == 78643
    assert cfg.b2_tokens == 111411

    # Immutability check via direct attribute assignment (Rule 43)
    with pytest.raises((AttributeError, TypeError)):
        cfg.usable_window = 65536  # type: ignore


def test_budget_config_threshold_invariant() -> None:
    # B1 must be strictly less than B2
    with pytest.raises(AssertionError):
        HarnessBudgetConfig(soft_threshold_ratio=0.90, hard_threshold_ratio=0.80)


def test_calibration_recommendation_immutability() -> None:
    cfg = HarnessBudgetConfig()
    rec = CalibrationRecommendation(
        model_name="test-model",
        harness_mode=HarnessMode.EFFICIENCY,
        action_space=ActionSpaceType.BASH_ONLY,
        context_tier=ContextTier.T4_STAGED,
        enable_planning=True,
        planning_role="stopping_point_controller",
        budget_config=cfg,
    )
    with pytest.raises((AttributeError, TypeError)):
        rec.harness_mode = HarnessMode.SCAFFOLD  # type: ignore


# ---------------------------------------------------------------------------
# 2. Empirical Calibration Logic across Model Tiers & Workloads
# ---------------------------------------------------------------------------


def test_calibration_weak_model_scaffold() -> None:
    # 30B model requires scaffold mode, typed tools, and planning as accuracy scaffold
    rec = CodingHarnessCalibrator.calibrate(
        model_name="Nemotron-3-30B",
        parameter_billions=30.0,
        workload=WorkloadType.CODEBASE_REPO,
    )
    assert rec.harness_mode == HarnessMode.SCAFFOLD
    assert rec.action_space == ActionSpaceType.PREDEFINED_TOOLS
    assert rec.planning_role == "accuracy_scaffold"
    assert rec.context_tier == ContextTier.T4_STAGED
    assert "m2_recoverable_recall_deprecated" in rec.deprecation_flags


def test_calibration_strong_model_cli_efficiency() -> None:
    # 550B model on terminal-centric workload requires bash-only and stopping-point planning
    rec = CodingHarnessCalibrator.calibrate(
        model_name="Nemotron-3-550B",
        parameter_billions=550.0,
        workload=WorkloadType.TERMINAL_CLI,
    )
    assert rec.harness_mode == HarnessMode.EFFICIENCY
    assert rec.action_space == ActionSpaceType.BASH_ONLY
    assert rec.planning_role == "stopping_point_controller"
    assert rec.context_tier == ContextTier.T4_STAGED


# ---------------------------------------------------------------------------
# 3. Stuck Detection In-Flight Safeguards
# ---------------------------------------------------------------------------


def test_stuck_detector_warning_and_kill() -> None:
    detector = StuckDetector(warn_threshold=5, kill_threshold=8)

    # 4 identical calls: no alert
    for _ in range(4):
        action, should_terminate = detector.record_call(
            "edit_file", "path=foo.py,old=x,new=y", is_failure=True
        )
        assert action == "none"
        assert not should_terminate

    # 5th identical call: trigger warning reminder
    action, should_terminate = detector.record_call(
        "edit_file", "path=foo.py,old=x,new=y", is_failure=True
    )
    assert action == "inject_warning_reminder"
    assert not should_terminate

    # Calls 6 and 7: keep running
    for _ in range(2):
        action, should_terminate = detector.record_call(
            "edit_file", "path=foo.py,old=x,new=y", is_failure=True
        )
        assert action == "none"
        assert not should_terminate

    # 8th consecutive failure: hard terminate
    action, should_terminate = detector.record_call(
        "edit_file", "path=foo.py,old=x,new=y", is_failure=True
    )
    assert action == "terminate_stuck_failures"
    assert should_terminate


def test_stuck_detector_streak_reset_on_new_action() -> None:
    detector = StuckDetector(warn_threshold=5, kill_threshold=8)
    for _ in range(4):
        detector.record_call("edit_file", "path=foo.py,old=x,new=y", is_failure=True)

    # Intervening different call resets streak
    action, should_terminate = detector.record_call(
        "read_file", "path=foo.py", is_failure=False
    )
    assert action == "none"
    assert not should_terminate

    # Another identical edit call starts from 1, not 5
    action, should_terminate = detector.record_call(
        "edit_file", "path=foo.py,old=x,new=y", is_failure=True
    )
    assert action == "none"
    assert not should_terminate


# ---------------------------------------------------------------------------
# 4. Diagnostic Validation & Knowledge Graph Integration
# ---------------------------------------------------------------------------


def test_skill_validator_passes_zero_warnings() -> None:
    workspace_root = Path(__file__).parents[2]
    skill_path = workspace_root / ".agents" / "skills" / "coding-harness-calibrator"
    report = SkillValidator.validate(skill_path)
    assert report.valid
    # Check zero warnings
    warnings = [
        c
        for c in report.checks
        if getattr(c, "severity", None) and c.severity.value == "warning"
    ]
    assert len(warnings) == 0, f"Encountered unexpected warnings: {warnings}"


def test_skill_registry_intent_routing() -> None:
    workspace_root = Path(__file__).parents[2]
    registry = BuiltinSkillRegistryService(default_root=str(workspace_root))
    routing = registry.route_intent("calibrate harness")
    matches = routing.get("matches", [])
    assert len(matches) > 0
    top_skill = matches[0]["skill_name"]
    assert top_skill == "coding-harness-calibrator"


def test_knowledge_item_isnad_integrity() -> None:
    workspace_root = Path(__file__).parents[2]
    ki_dir = (
        workspace_root / ".harness" / "knowledge" / "ki-empirical-harness-calibration"
    )
    assert (ki_dir / "metadata.json").exists()
    assert (ki_dir / "summary.md").exists()

    metadata = json.loads((ki_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["id"] == "ki-empirical-harness-calibration"
    assert len(metadata["isnad"]["claims"]) >= 5
    for claim in metadata["isnad"]["claims"]:
        assert claim["verified"] is True
        assert "arXiv:2609.20804v1" in claim["source"]
