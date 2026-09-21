"""Tests for the HarnessCompass skill, R3 Integrator engine, and Knowledge Item."""

import json
from pathlib import Path
import pytest

from harness.creator.skills import SkillValidator
try:
    from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser
except ImportError:
    SkillCardParser = None

# Import the slotted R3 engine from the skill's scripts
import sys
skill_scripts = Path(__file__).parents[2] / ".agents" / "skills" / "harness-compass" / "scripts"
sys.path.insert(0, str(skill_scripts))

from r3_integrator import (  # type: ignore # noqa: E402
    ComponentSurface,
    FailureAttribution,
    FeedbackItem,
    GeneralizationGate,
    HarnessEdit,
    ProactiveFeedbackGrounder,
    R3IntegratorEngine,
    Track,
)


@pytest.fixture
def gate() -> GeneralizationGate:
    return GeneralizationGate()


@pytest.fixture
def grounder() -> ProactiveFeedbackGrounder:
    return ProactiveFeedbackGrounder()


@pytest.fixture
def engine(gate: GeneralizationGate) -> R3IntegratorEngine:
    return R3IntegratorEngine(gate=gate)


# ---------------------------------------------------------------------------
# Principle 1: Constrained Evolution & Generalization Gate Tests
# ---------------------------------------------------------------------------

def test_generalization_gate_allows_valid_criterion(gate: GeneralizationGate) -> None:
    valid_edit = HarnessEdit(
        id="chg-01",
        surface=ComponentSurface.SYSTEMPROMPT,
        description="Add multi-consumer decision criterion",
        target_file="systemprompt.md",
        content="When one shared producer feeds a wrong value to several call-sites, fix the producer. When wrong only in local scenario, keep fix local.",
        is_advisory=True,
        is_code_executable=False,
    )
    result = gate.validate_edit(valid_edit)
    assert result.passed
    assert len(result.violations) == 0


def test_generalization_gate_rejects_task_id(gate: GeneralizationGate) -> None:
    bad_edit = HarnessEdit(
        id="chg-02",
        surface=ComponentSurface.SYSTEMPROMPT,
        description="Fix for specific benchmark task",
        target_file="systemprompt.md",
        content="Special handling for task sympy-12445: invert the sign on polynomial reduction.",
        is_advisory=True,
    )
    result = gate.validate_edit(bad_edit)
    assert not result.passed
    assert any(v.rule == "BANNED_TASK_INSTANCE_ID" for v in result.violations)


def test_generalization_gate_rejects_test_function_names(gate: GeneralizationGate) -> None:
    bad_edit = HarnessEdit(
        id="chg-03",
        surface=ComponentSurface.MEMORY,
        description="Memorize test failure",
        target_file="LongTermMEMORY.md",
        content="Always run tests/test_matrix.py and ensure def test_eval_matrix() passes before finalizing.",
        is_advisory=True,
    )
    result = gate.validate_edit(bad_edit)
    assert not result.passed
    assert any(v.rule == "BANNED_TEST_FILE_OR_FUNCTION" for v in result.violations)


def test_generalization_gate_rejects_keyword_branching(gate: GeneralizationGate) -> None:
    bad_edit = HarnessEdit(
        id="chg-04",
        surface=ComponentSurface.MIDDLEWARE,
        description="Branch on dataset keyword",
        target_file="middleware/patch_guard.py",
        content="if 'django_v4' in text:\n    return skip_patch()",
        is_code_executable=True,
    )
    result = gate.validate_edit(bad_edit)
    assert not result.passed
    assert any(v.rule == "BANNED_KEYWORD_BRANCHING" for v in result.violations)


def test_generalization_gate_placement_invariant(gate: GeneralizationGate) -> None:
    # Advisory leak in structural surface
    leak_edit = HarnessEdit(
        id="chg-05",
        surface=ComponentSurface.MIDDLEWARE,
        description="Conversational advice in middleware",
        target_file="middleware/advisor.py",
        content="# Inject text: Remember to check symmetric case",
        is_advisory=True,
        is_code_executable=False,
    )
    result = gate.validate_edit(leak_edit)
    assert not result.passed
    assert any(v.rule == "ADVISORY_LEAK_IN_STRUCTURAL_SURFACE" for v in result.violations)


# ---------------------------------------------------------------------------
# Principle 2: Proactive First-Person Feedback Tests
# ---------------------------------------------------------------------------

def test_feedback_filters_non_harness_attributions(grounder: ProactiveFeedbackGrounder) -> None:
    item = FeedbackItem(
        kind="improve_existing",
        component=ComponentSurface.TOOL_IMPL,
        friction="Agent hallucinated variable name",
        desired_change="Make agent smarter",
        attribution=FailureAttribution.AGENT_REASONING,
    )
    grounded = grounder.ground_feedback(item, trajectory_turns=[])
    assert not grounded.grounded
    assert "non-harness" in grounded.rejection_reason


def test_feedback_requires_trace_citation_for_existing_tools(grounder: ProactiveFeedbackGrounder) -> None:
    item = FeedbackItem(
        kind="improve_existing",
        component=ComponentSurface.TOOL_IMPL,
        friction="Bash tool timed out on git diff",
        desired_change="Increase timeout to 30s",
        trace_refs=("turn_4",),
        attribution=FailureAttribution.HARNESS,
        self_consistency="pre_post_agree",
    )
    # Trace does NOT have turn_4
    fake_trace = [{"turn_id": "turn_1"}, {"turn_id": "turn_2"}]
    grounded = grounder.ground_feedback(item, trajectory_turns=fake_trace)
    assert not grounded.grounded
    assert "not found in raw execution trajectory" in grounded.rejection_reason

    # Trace DOES have turn_4
    valid_trace = [{"turn_id": "turn_1"}, {"turn_id": "turn_4"}]
    grounded_ok = grounder.ground_feedback(item, trajectory_turns=valid_trace)
    assert grounded_ok.grounded
    assert grounded_ok.confidence >= 0.90
    assert grounded_ok.assigned_track == Track.STRUCTURAL


# ---------------------------------------------------------------------------
# Principle 3: Component-Wise Optimization & R3 Merge Tests
# ---------------------------------------------------------------------------

def test_r3_merge_preserves_winner_and_integrates_loser(engine: R3IntegratorEngine) -> None:
    winner_edits = [
        HarnessEdit(
            id="win-01",
            surface=ComponentSurface.MIDDLEWARE,
            description="Patch-verdict guard: block finalizing on failing test validation",
            target_file="middleware/patch_guard.py",
            content="def check_patch(verdict): return verdict == 'pass'",
            is_code_executable=True,
        )
    ]

    loser_edits = [
        # Valid independent edit
        HarnessEdit(
            id="lose-01",
            surface=ComponentSurface.SYSTEMPROMPT,
            description="Guide agent to prioritize narrow unit reproduction",
            target_file="systemprompt.md",
            content="Always formulate the narrowest possible reproduction script before modifying source files.",
            is_advisory=True,
        ),
        # Overfitting edit (should be dropped in Revision)
        HarnessEdit(
            id="lose-02",
            surface=ComponentSurface.MEMORY,
            description="Task specific note",
            target_file="LongTermMEMORY.md",
            content="In task-4421, the fix is in models.py line 20.",
            is_advisory=True,
        ),
        # Collision with winner (should be dropped in Recombination)
        HarnessEdit(
            id="lose-03",
            surface=ComponentSurface.MIDDLEWARE,
            description="Alternative patch guard",
            target_file="middleware/patch_guard.py",
            content="def check_patch_alt(): pass",
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

    # Assert Revision kept lose-01 and dropped lose-02 (gate failure) and lose-03 (file collision)
    kept_ids = [k["change"] for k in manifest.kept_from_loser]
    dropped_ids = [d["change"] for d in manifest.dropped_from_loser]

    assert "lose-01" in kept_ids
    assert "lose-02" in dropped_ids
    assert "lose-03" in dropped_ids


def test_r3_refinement_occam_razor_purges_duplicate_advisory(engine: R3IntegratorEngine) -> None:
    winner_edits = [
        HarnessEdit(
            id="win-code-01",
            surface=ComponentSurface.MIDDLEWARE,
            description="Isolated virtual environment test runner enforcing execution validation",
            target_file="middleware/test_runner.py",
            content="def run_isolated_test(): pass",
            is_code_executable=True,
        )
    ]

    loser_edits = [
        # Advisory prompt rule that does the exact same job in prose
        HarnessEdit(
            id="lose-adv-01",
            surface=ComponentSurface.SYSTEMPROMPT,
            description="Advisory rule for isolated virtual environment test execution",
            target_file="systemprompt.md",
            content="Remember to always run tests inside an isolated virtual environment to validate execution.",
            is_advisory=True,
        )
    ]

    manifest = engine.merge(
        winner_name="Track A (Structural)",
        winner_score=0.66,
        winner_edits=winner_edits,
        loser_name="Track B (Guidance)",
        loser_score=0.62,
        loser_edits=loser_edits,
    )

    # Occam's razor refinement should identify the redundancy and schedule the advisory rule for removal
    redundant_ids = [r["change"] for r in manifest.removed_as_redundant]
    assert "lose-adv-01" in redundant_ids


# ---------------------------------------------------------------------------
# Skill Specification & Knowledge Item Verification
# ---------------------------------------------------------------------------

def test_skill_conforms_to_harness_catalog_standards() -> None:
    skill_dir = Path(__file__).parents[2] / ".agents" / "skills" / "harness-compass"
    assert skill_dir.exists(), f"Skill directory {skill_dir} not found"

    report = SkillValidator.validate(skill_dir)
    # Rule 34: evaluate overall status via report.valid
    assert report.valid, f"Skill validation failed: {[c.message for c in report.checks if not c.passed]}"


def test_skill_card_ascii_formatting() -> None:
    card_path = Path(__file__).parents[2] / ".agents" / "skills" / "harness-compass" / "CARD.md"
    assert card_path.exists()
    content = card_path.read_text(encoding="utf-8")

    # Rule 37: check single-pipe borders and exact SKILL: tag
    assert "SKILL:       harness-compass" in content
    assert "║" not in content, "CARD.md must not use double-pipe borders"
    assert "│" in content, "CARD.md must use single-pipe borders"

    # Verify parser works cleanly if available
    if SkillCardParser is not None:
        node = SkillCardParser.parse_directory(card_path.parent)
        assert node is not None
        assert node.name == "harness-compass"


def test_knowledge_item_conforms_to_canonical_vault() -> None:
    ki_dir = Path(__file__).parents[2] / ".harness" / "knowledge" / "ki-harnesscompass-evolution"
    assert ki_dir.exists()

    meta_file = ki_dir / "metadata.json"
    summary_file = ki_dir / "summary.md"

    # Rule 40: Canonical dual-file directory
    assert meta_file.exists()
    assert summary_file.exists()

    with open(meta_file, encoding="utf-8") as f:
        meta = json.load(f)

    # Rule 41: Epistemic isnad verification
    assert meta["id"] == "ki-harnesscompass-evolution"
    assert "isnad" in meta
    assert len(meta["isnad"]["claims"]) >= 3
    assert all(c.get("verified") is True for c in meta["isnad"]["claims"])

    summary_content = summary_file.read_text(encoding="utf-8")
    assert "SWE-Bench Verified" in summary_content
    assert "Constrained Evolution" in summary_content
    assert "R3 Integrator" in summary_content
