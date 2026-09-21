"""Comprehensive tests for deepened HarnessCompass architecture.

Covers:
- Slotted frozen dataclass immutability (Rule 12 & Rule 43)
- Global Generalization Gate (Content & Placement invariants)
- Proactive First-Person Feedback attribution & trajectory grounding
- Component-wise dual-track optimization & R3 integration (Occam's razor purge)
- Closed-loop 5-stage evolution simulation & acceptance gating
- IoC service key registration & resolution (Rule 2 & Rule 49)
- PluginValidator compliance & zero-fork configuration (Rule 34, 38, 44)
- Click CLI commands and CliRunner assertions (Rule 6, 10, 23)
- Standalone HTML visual brief generation
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from click.testing import CliRunner
import pytest

_ws_root = Path(__file__).resolve().parent.parent
_skill_scripts = (
    _ws_root / ".agents" / "skills" / "harness-compass" / "scripts"
)
for _p in [_ws_root / "src", _skill_scripts, _ws_root]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from harness_compass_engine import (
    ComponentSurface,
    EvolutionRound,
    FailureAttribution,
    FeedbackItem,
    GateResult,
    GateViolation,
    GeneralizationGate,
    GroundedEvidence,
    HarnessCompassEngine,
    HarnessEdit,
    IntegrationManifest,
    ProactiveFeedbackGrounder,
    R3IntegratorEngine,
    Track,
)

from harness.commands.compass import compass_group
from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.harness_compass import (
    HARNESS_COMPASS_SERVICE_KEY,
    EvolutionRoundData,
    FeedbackItemData,
    GateResultData,
    HarnessCompassService,
    HarnessEditData,
    IntegrationManifestData,
)
from plugins.agent_orchestration.harness_compass.main import (
    HarnessCompassPlugin,
)
from plugins.agent_orchestration.harness_compass.main import (
    plugin as compass_plugin,
)


@pytest.fixture
def engine() -> HarnessCompassEngine:
    return HarnessCompassEngine()


@pytest.fixture
def service_context() -> ServiceContext:
    ctx = ServiceContext()
    ctx.provide(HARNESS_COMPASS_SERVICE_KEY, compass_plugin)
    return ctx


# --- 1. Slotted & Frozen Dataclass Immutability (Rule 12 & Rule 43) ---


def test_frozen_dataclass_immutability():
    """Verify slotted & frozen dataclasses prevent attribute mutation (Rule 12 & Rule 43)."""
    edit = HarnessEdit(
        id="edit-01",
        surface=ComponentSurface.SYSTEMPROMPT,
        description="General guidance",
        target_file="systemprompt.md",
        content="Always formulate narrow unit test.",
        is_advisory=True,
    )
    with pytest.raises((AttributeError, TypeError)):
        edit.content = "Mutated content"  # type: ignore

    violation = GateViolation(
        surface="systemprompt",
        rule="BANNED_TASK_INSTANCE_ID",
        detail="Violated rule",
    )
    with pytest.raises((AttributeError, TypeError)):
        violation.rule = "OTHER_RULE"  # type: ignore

    gate_res = GateResult(passed=False, violations=(violation,))
    with pytest.raises((AttributeError, TypeError)):
        gate_res.passed = True  # type: ignore

    item = FeedbackItem(
        kind="improve_existing",
        component=ComponentSurface.TOOL_IMPL,
        friction="Tool timeout",
        desired_change="Increase timeout",
    )
    with pytest.raises((AttributeError, TypeError)):
        item.friction = "New friction"  # type: ignore

    evidence = GroundedEvidence(
        item=item,
        grounded=True,
        assigned_track=Track.STRUCTURAL,
        confidence=0.95,
    )
    with pytest.raises((AttributeError, TypeError)):
        evidence.confidence = 0.5  # type: ignore

    manifest = IntegrationManifest(
        base_winner="Track A",
        winner_score=0.66,
        loser_score=0.62,
    )
    with pytest.raises((AttributeError, TypeError)):
        manifest.winner_score = 0.70  # type: ignore

    rnd = EvolutionRound(
        round_num=1,
        baseline_score=0.54,
        structural_score=0.66,
        guidance_score=0.62,
        winner_track=Track.STRUCTURAL,
        winner_score=0.66,
        manifest=manifest,
        accepted=True,
    )
    with pytest.raises((AttributeError, TypeError)):
        rnd.accepted = False  # type: ignore


# --- 2. Global Generalization Gate Tests ---


def test_generalization_gate_allows_valid_criterion(engine: HarnessCompassEngine):
    """Verify Generalization Gate accepts task-agnostic reusable principles."""
    edit = HarnessEdit(
        id="chg-valid",
        surface=ComponentSurface.SYSTEMPROMPT,
        description="Decision heuristic",
        target_file="systemprompt.md",
        content="When one shared producer feeds wrong values to multiple sites, fix at producer.",
        is_advisory=True,
    )
    res = engine.evaluate_edit(edit)
    assert res.passed is True
    assert len(res.violations) == 0


def test_generalization_gate_rejects_task_id(engine: HarnessCompassEngine):
    """Verify Generalization Gate rejects benchmark task IDs."""
    edit = HarnessEdit(
        id="chg-task",
        surface=ComponentSurface.SYSTEMPROMPT,
        description="Task fix",
        target_file="systemprompt.md",
        content="For task sympy-12445, change sign in polynomial reducer.",
        is_advisory=True,
    )
    res = engine.evaluate_edit(edit)
    assert res.passed is False
    assert any(v.rule == "BANNED_TASK_INSTANCE_ID" for v in res.violations)


def test_generalization_gate_rejects_test_paths(engine: HarnessCompassEngine):
    """Verify Generalization Gate rejects concrete test filenames or function signatures."""
    edit = HarnessEdit(
        id="chg-test",
        surface=ComponentSurface.MEMORY,
        description="Memorize test",
        target_file="MEMORY.md",
        content="Always run tests/test_algebra.py and ensure def test_factor() passes.",
        is_advisory=True,
    )
    res = engine.evaluate_edit(edit)
    assert res.passed is False
    assert any(v.rule == "BANNED_TEST_FILE_OR_FUNCTION" for v in res.violations)


def test_generalization_gate_rejects_keyword_branching(engine: HarnessCompassEngine):
    """Verify Generalization Gate rejects keyword branch hacks."""
    edit = HarnessEdit(
        id="chg-branch",
        surface=ComponentSurface.MIDDLEWARE,
        description="Keyword branch",
        target_file="middleware/guard.py",
        content="if 'django' in text:\n    return fast_patch()",
        is_code_executable=True,
    )
    res = engine.evaluate_edit(edit)
    assert res.passed is False
    assert any(v.rule == "BANNED_KEYWORD_BRANCHING" for v in res.violations)


def test_generalization_gate_placement_invariant(engine: HarnessCompassEngine):
    """Verify Generalization Gate enforces separation of executable capability and advice."""
    # Advisory leak in structural surface
    advisory_leak = HarnessEdit(
        id="chg-leak",
        surface=ComponentSurface.MIDDLEWARE,
        description="Advisory in middleware",
        target_file="middleware/advisor.py",
        content="# Prompt hint: Check boundary conditions",
        is_advisory=True,
        is_code_executable=False,
    )
    res = engine.evaluate_edit(advisory_leak)
    assert res.passed is False
    assert any(v.rule == "ADVISORY_LEAK_IN_STRUCTURAL_SURFACE" for v in res.violations)

    # Executable code in guidance surface
    code_in_guidance = HarnessEdit(
        id="chg-code-in-guidance",
        surface=ComponentSurface.SYSTEMPROMPT,
        description="Code in system prompt",
        target_file="systemprompt.md",
        content="def execute(): pass",
        is_code_executable=True,
        is_advisory=False,
    )
    res2 = engine.evaluate_edit(code_in_guidance)
    assert res2.passed is False
    assert any(v.rule == "EXECUTABLE_CODE_IN_GUIDANCE_SURFACE" for v in res2.violations)


# --- 3. Proactive First-Person Feedback Grounding Tests ---


def test_feedback_filters_non_harness_attributions(engine: HarnessCompassEngine):
    """Verify non-harness failure attributions are discarded from evolution evidence."""
    for attr in [
        FailureAttribution.AGENT_REASONING,
        FailureAttribution.TASK_AMBIGUITY,
        FailureAttribution.ENVIRONMENT,
    ]:
        item = FeedbackItem(
            kind="improve_existing",
            component=ComponentSurface.TOOL_IMPL,
            friction="Model hallucinated method call",
            desired_change="Better LLM",
            attribution=attr,
        )
        grounded = engine.ground_feedback(item, trajectory_turns=[])
        assert grounded.grounded is False
        assert "non-harness" in grounded.rejection_reason


def test_feedback_requires_trace_citation(engine: HarnessCompassEngine):
    """Verify improve_existing feedback requires turn citations validated against raw trace."""
    item = FeedbackItem(
        kind="improve_existing",
        component=ComponentSurface.TOOL_IMPL,
        friction="Git diff command timed out",
        desired_change="Increase timeout",
        trace_refs=("turn_3",),
        attribution=FailureAttribution.HARNESS,
        self_consistency="pre_post_agree",
    )
    # Missing citation in trace
    evidence_fail = engine.ground_feedback(item, trajectory_turns=[{"turn_id": "turn_1"}])
    assert evidence_fail.grounded is False
    assert "not found in raw execution trajectory" in evidence_fail.rejection_reason

    # Valid citation present in trace
    evidence_pass = engine.ground_feedback(
        item, trajectory_turns=[{"turn_id": "turn_1"}, {"turn_id": "turn_3"}]
    )
    assert evidence_pass.grounded is True
    assert evidence_pass.assigned_track == Track.STRUCTURAL
    assert evidence_pass.confidence >= 0.90


# --- 4. Component-Wise Dual-Track Optimization & R3 Integration ---


def test_r3_merge_revision_and_recombination(engine: HarnessCompassEngine):
    """Verify R3 revision triages loser edits and recombines positive changes onto winner base."""
    winner_edits = [
        HarnessEdit(
            id="win-01",
            surface=ComponentSurface.MIDDLEWARE,
            description="Patch guard blocking syntax errors",
            target_file="middleware/patch_guard.py",
            content="def check(): pass",
            is_code_executable=True,
        )
    ]
    loser_edits = [
        # Valid independent edit to keep
        HarnessEdit(
            id="lose-keep",
            surface=ComponentSurface.SYSTEMPROMPT,
            description="Prioritize minimal reproduction",
            target_file="systemprompt.md",
            content="Always formulate narrowest reproduction before edit.",
            is_advisory=True,
        ),
        # Overfitting edit to drop
        HarnessEdit(
            id="lose-overfit",
            surface=ComponentSurface.MEMORY,
            description="Specific task fix",
            target_file="MEMORY.md",
            content="Task sympy-1244 fix.",
            is_advisory=True,
        ),
        # Direct collision to drop
        HarnessEdit(
            id="lose-collide",
            surface=ComponentSurface.MIDDLEWARE,
            description="Colliding patch guard",
            target_file="middleware/patch_guard.py",
            content="def check_alt(): pass",
            is_code_executable=True,
        ),
    ]

    manifest = engine.merge(
        winner_name="Track A (Structural)",
        winner_score=0.66,
        winner_edits=winner_edits,
        loser_name="Track B (Guidance)",
        loser_score=0.62,
        loser_edits=loser_edits,
    )

    kept = [k["change"] for k in manifest.kept_from_loser]
    dropped = [d["change"] for d in manifest.dropped_from_loser]

    assert "lose-keep" in kept
    assert "lose-overfit" in dropped
    assert "lose-collide" in dropped


def test_r3_occam_razor_redundancy_purge(engine: HarnessCompassEngine):
    """Verify Occam's Razor refinement actively hunts and purges duplicate advisory prompt text."""
    winner_edits = [
        HarnessEdit(
            id="win-exec",
            surface=ComponentSurface.MIDDLEWARE,
            description="Isolated virtual environment test runner enforcing execution validation",
            target_file="middleware/test_runner.py",
            content="def run(): pass",
            is_code_executable=True,
        )
    ]
    loser_edits = [
        # Advisory prompt rule duplicating middleware behavior
        HarnessEdit(
            id="lose-adv-dup",
            surface=ComponentSurface.SYSTEMPROMPT,
            description="Advisory rule for isolated virtual environment test execution",
            target_file="systemprompt.md",
            content="Remember to run tests in an isolated virtual environment to validate execution.",
            is_advisory=True,
        )
    ]

    manifest = engine.merge(
        winner_name="Track A",
        winner_score=0.66,
        winner_edits=winner_edits,
        loser_name="Track B",
        loser_score=0.62,
        loser_edits=loser_edits,
    )

    purged = [r["change"] for r in manifest.removed_as_redundant]
    assert "lose-adv-dup" in purged


# --- 5. Full 5-Stage Evolution Simulation & Acceptance Gating ---


def test_simulation_round_acceptance_and_rejection(engine: HarnessCompassEngine):
    """Verify evolution round is accepted when Pass@1 beats baseline, rejected otherwise."""
    s_edits = [
        HarnessEdit(
            id="s-01",
            surface=ComponentSurface.MIDDLEWARE,
            description="Execution guard",
            target_file="middleware/guard.py",
            content="def guard(): pass",
            is_code_executable=True,
        )
    ]
    g_edits = [
        HarnessEdit(
            id="g-01",
            surface=ComponentSurface.SYSTEMPROMPT,
            description="Reproduction guideline",
            target_file="systemprompt.md",
            content="Narrow reproduction first.",
            is_advisory=True,
        )
    ]

    # Acceptance case: winner (0.66) > baseline (0.54)
    round_acc = engine.simulate_evolution_round(
        round_num=1,
        baseline_score=0.54,
        structural_edits=s_edits,
        guidance_edits=g_edits,
        structural_score=0.66,
        guidance_score=0.62,
    )
    assert round_acc.accepted is True
    assert round_acc.winner_track == Track.STRUCTURAL
    assert round_acc.winner_score == 0.66

    # Rejection case: winner (0.50) <= baseline (0.54)
    round_rej = engine.simulate_evolution_round(
        round_num=2,
        baseline_score=0.54,
        structural_edits=s_edits,
        guidance_edits=g_edits,
        structural_score=0.50,
        guidance_score=0.48,
    )
    assert round_rej.accepted is False


# --- 6. Micro-Kernel IoC Service Seam (Rule 2 & Rule 49) ---


def test_ioc_service_registration_and_execution(service_context: ServiceContext):
    """Verify HarnessCompassService resolves via ServiceKey and executes cleanly."""
    svc: HarnessCompassService = service_context.require(HARNESS_COMPASS_SERVICE_KEY)
    assert svc is not None

    # Test gate validation through service seam
    edit = HarnessEditData(
        id="svc-01",
        surface="systemprompt",
        description="General principle",
        target_file="systemprompt.md",
        content="Fix at producer if multiple consumers impacted.",
        is_advisory=True,
    )
    res = svc.validate_edit(edit)
    assert res.passed is True

    # Test feedback grounding through service seam
    item = FeedbackItemData(
        kind="improve_existing",
        component="tool_impl",
        friction="Tool error",
        desired_change="Add retry",
        trace_refs=["turn_2"],
        attribution="harness",
    )
    evidence = svc.ground_feedback(item, [{"turn_id": "turn_2"}])
    assert evidence.grounded is True
    assert evidence.assigned_track == "structural"

    # Test R3 merge through service seam
    manifest = svc.execute_r3_merge(
        winner_name="Track A",
        winner_score=0.65,
        winner_edits=[edit],
        loser_name="Track B",
        loser_score=0.60,
        loser_edits=[],
    )
    assert manifest.winner_score == 0.65

    # Test simulation round through service seam
    round_res = svc.simulate_round(
        round_num=1,
        baseline_score=0.50,
        structural_edits=[edit],
        guidance_edits=[],
        structural_score=0.65,
        guidance_score=0.55,
    )
    assert round_res.accepted is True


# --- 7. Plugin Validator Compliance (Rule 34, 38, 44, 45) ---


def test_plugin_validation_sync():
    """Verify harness_compass plugin passes PluginValidator checks (Rule 34 & Rule 38)."""
    plugin_dir = _ws_root / "plugins" / "agent_orchestration" / "harness_compass"
    assert plugin_dir.exists()

    report = PluginValidator.validate_sync(plugin_dir)
    assert report.valid is True, f"Plugin validation failed: {[c.message for c in report.checks if not c.passed]}"


@pytest.mark.asyncio
async def test_plugin_lifecycle():
    """Verify plugin on_load registers HARNESS_COMPASS_SERVICE_KEY in context."""
    ctx = ServiceContext()
    p = HarnessCompassPlugin()
    assert HARNESS_COMPASS_SERVICE_KEY in p.provides

    await p.on_load(ctx)
    resolved = ctx.require(HARNESS_COMPASS_SERVICE_KEY)
    assert resolved is p

    await p.on_unload(ctx)


# --- 8. Headless Click CLI Commands (Rule 6, 10, 23) ---


def test_cli_gate_command():
    """Verify 'harness compass gate' evaluates candidate edits."""
    runner = CliRunner()
    res = runner.invoke(
        compass_group,
        ["gate", "Fix at producer for multi-consumer bugs.", "--id", "chg-cli"],
    )
    assert res.exit_code == 0
    assert "PASSED" in res.output

    # Test rejection with benchmark task token
    res_bad = runner.invoke(
        compass_group,
        ["gate", "Fix for task sympy-12445.", "--id", "chg-cli-bad"],
    )
    assert res_bad.exit_code == 0
    assert "FAILED" in res_bad.output
    assert "BANNED_TASK_INSTANCE_ID" in res_bad.output

    # Test JSON output
    res_json = runner.invoke(
        compass_group,
        ["gate", "Task-agnostic rule.", "--json-output"],
    )
    assert res_json.exit_code == 0
    data = json.loads(res_json.output)
    assert data["passed"] is True


def test_cli_feedback_command():
    """Verify 'harness compass feedback' grounds agent feedback."""
    runner = CliRunner()
    res = runner.invoke(
        compass_group,
        ["feedback", "Tool timed out", "--trace-refs", "turn_1"],
    )
    assert res.exit_code == 0
    assert "Grounded:         YES" in res.output
    assert "STRUCTURAL" in res.output


def test_cli_merge_command():
    """Verify 'harness compass merge' executes R3 integration."""
    runner = CliRunner()
    res = runner.invoke(compass_group, ["merge"])
    assert res.exit_code == 0
    assert "R3 Integration Manifest:" in res.output
    assert "Winner Base:" in res.output
    assert "Kept from Loser:" in res.output
    assert "Occam Redundancy:" in res.output


def test_cli_run_command():
    """Verify 'harness compass run' simulates evolution rounds."""
    runner = CliRunner()
    res = runner.invoke(
        compass_group,
        ["run", "--baseline", "0.54", "--structural-score", "0.66"],
    )
    assert res.exit_code == 0
    assert "ACCEPTED" in res.output
    assert "66.0%" in res.output


def test_cli_brief_command(tmp_path: Path):
    """Verify 'harness compass brief' generates interactive HTML Visual Brief."""
    runner = CliRunner()
    out_file = tmp_path / "test_brief.html"
    res = runner.invoke(compass_group, ["brief", "--output", str(out_file)])
    assert res.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "HarnessCompass Evolution Telemetry" in content
    assert "mermaid" in content
