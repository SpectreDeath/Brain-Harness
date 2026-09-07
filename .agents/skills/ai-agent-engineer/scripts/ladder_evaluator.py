"""The Four-Level Ladder & Pre-Flight Agent Scoping Evaluator.

Distilled from Chapter 0 of 'The AI Agent Engineer\'s Guide' by Vahe Aslanyan.
Automates classification into Level 1 (Static Prompt), Level 2 (Deterministic Workflow),
Level 3 (Bounded Agent), or Level 4 (Full Agent), and validates the 5 Pre-Flight Questions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


@dataclass(slots=True, frozen=True)
class TaskScopingInput:
    """Task specification inputs to evaluate on the 4-Level Ladder."""

    task_description: str
    candidate_tools: list[str] = field(default_factory=list)
    estimated_steps: int = 1
    state_dependent_decisions: bool = False
    is_flow_invariant: bool = False
    has_irreversible_mutations: bool = False
    success_metric: str = ""
    worst_case_blast_radius: str = ""
    cost_ceiling_per_session: float = 0.0
    evaluation_harness_description: str = ""
    off_switch_description: str = ""


@dataclass(slots=True, frozen=True)
class ScopingQuestionAssessment:
    """Evaluation of one of the 5 Pre-Flight Scoping Questions."""

    question_number: int
    name: str
    response: str
    passed: bool
    critique: str


@dataclass(slots=True, frozen=True)
class LadderEvaluationResult:
    """Result of ladder evaluation and scoping gate check."""

    recommended_level: int
    level_name: str
    confidence: float
    rationale: list[str]
    scoping_assessments: list[ScopingQuestionAssessment]
    all_questions_passed: bool
    approved_for_implementation: bool


class LadderEvaluator:
    """Evaluates task requirements and asserts pre-flight scoping invariants."""

    LEVEL_NAMES: dict[int, str] = {
        1: "Level 1: Static Prompt",
        2: "Level 2: Deterministic Workflow",
        3: "Level 3: Bounded Agent",
        4: "Level 4: Full Agent",
    }

    @classmethod
    def evaluate(cls, task: TaskScopingInput, config: dict[str, Any] | None = None) -> LadderEvaluationResult:
        """Classify task into lowest viable ladder level and assess 5 scoping questions."""
        cfg = config or {}
        ladder_cfg = cfg.get("ladder", {})
        l3_max = ladder_cfg.get("level_3_max_steps", 20)

        rationale: list[str] = []
        rec_level: int = 1
        confidence: float = 0.90

        # Heuristic 1: No tools and 1 step -> Level 1
        if len(task.candidate_tools) == 0 and task.estimated_steps <= 1 and not task.state_dependent_decisions:
            rec_level = 1
            rationale.append("Zero external tools required and single step execution: fits Level 1 (Static Prompt).")
        # Heuristic 2: Invariant sequence without dynamic branching -> Level 2
        elif task.is_flow_invariant and not task.state_dependent_decisions:
            rec_level = 2
            rationale.append("Execution sequence is fixed regardless of content: fits Level 2 (Deterministic Workflow).")
        # Heuristic 3: State-dependent decisions with bounded tools (<15) and small step budget (<=20) -> Level 3
        elif task.state_dependent_decisions and len(task.candidate_tools) <= 15 and task.estimated_steps <= l3_max:
            rec_level = 3
            rationale.append(
                f"Requires state-dependent tool branching ({len(task.candidate_tools)} tools) "
                f"within bounded step budget ({task.estimated_steps} <= {l3_max}): fits Level 3 (Bounded Agent)."
            )
        # Heuristic 4: Long horizon, large toolset, or complex unguided autonomy -> Level 4
        else:
            rec_level = 4
            rationale.append(
                f"Requires long-horizon autonomy ({task.estimated_steps} steps) or extensive tool branching "
                f"({len(task.candidate_tools)} tools): escalates to Level 4 (Full Agent)."
            )

        # Assess 5 Pre-Flight Scoping Questions if Level 3 or 4
        assessments: list[ScopingQuestionAssessment] = []
        all_passed = True

        if rec_level >= 3:
            # Q1: Measurable Success
            q1_pass, q1_critique = cls._eval_success_metric(task.success_metric)
            assessments.append(ScopingQuestionAssessment(1, "Measurable Success", task.success_metric, q1_pass, q1_critique))

            # Q2: Worst-Case Blast Radius
            q2_pass, q2_critique = cls._eval_blast_radius(task.worst_case_blast_radius, task.has_irreversible_mutations)
            assessments.append(ScopingQuestionAssessment(2, "Worst-Case Blast Radius", task.worst_case_blast_radius, q2_pass, q2_critique))

            # Q3: Cost Ceiling
            q3_pass, q3_critique = cls._eval_cost_ceiling(task.cost_ceiling_per_session)
            assessments.append(ScopingQuestionAssessment(3, "Cost Ceiling per Session", f"${task.cost_ceiling_per_session:.2f}", q3_pass, q3_critique))

            # Q4: Evaluation Harness
            q4_pass, q4_critique = cls._eval_eval_harness(task.evaluation_harness_description)
            assessments.append(ScopingQuestionAssessment(4, "Session Evaluation Harness", task.evaluation_harness_description, q4_pass, q4_critique))

            # Q5: Off-Switch & Rollback
            q5_pass, q5_critique = cls._eval_off_switch(task.off_switch_description)
            assessments.append(ScopingQuestionAssessment(5, "Off-Switch & Rollback", task.off_switch_description, q5_pass, q5_critique))

            all_passed = all(a.passed for a in assessments)
        else:
            # Level 1 and 2 don't require full agent scoping questions
            all_passed = True

        approved = (rec_level < 3) or (rec_level >= 3 and all_passed)

        return LadderEvaluationResult(
            recommended_level=rec_level,
            level_name=cls.LEVEL_NAMES[rec_level],
            confidence=confidence,
            rationale=rationale,
            scoping_assessments=assessments,
            all_questions_passed=all_passed,
            approved_for_implementation=approved,
        )

    @classmethod
    def _eval_success_metric(cls, metric: str) -> tuple[bool, str]:
        if not metric or len(metric.strip()) < 10:
            return False, "Empty or vague success metric. Must specify quantifiable threshold (e.g. >= 85% completion)."
        has_num = bool(re.search(r"\d+%?|\d+\.\d+", metric))
        if not has_num:
            return False, "Success metric lacks numeric target or threshold. Qualitative statements are unmeasurable."
        return True, "Quantifiable metric specified with measurable threshold."

    @classmethod
    def _eval_blast_radius(cls, blast: str, irreversible: bool) -> tuple[bool, str]:
        if not blast or len(blast.strip()) < 10:
            return False, "Worst-case blast radius undefined. Unbounded autonomy is prohibited."
        if irreversible and ("sandbox" not in blast.lower() and "permission" not in blast.lower() and "bound" not in blast.lower()):
            return False, "Task involves irreversible mutations but lacks explicit sandbox or permission bounding."
        return True, "Blast radius documented with bounded risk controls."

    @classmethod
    def _eval_cost_ceiling(cls, cost: float) -> tuple[bool, str]:
        if cost <= 0.0:
            return False, "Cost ceiling must be positive non-zero value."
        if cost > 50.0:
            return False, f"Cost ceiling ${cost:.2f} exceeds standard safety threshold ($50.00) without high-tier escalation."
        return True, f"Cost ceiling bounded at ${cost:.2f}/session."

    @classmethod
    def _eval_eval_harness(cls, harness: str) -> tuple[bool, str]:
        if not harness or len(harness.strip()) < 10:
            return False, "Missing evaluation harness. Must specify labeled dataset or trajectory replay suite."
        if "later" in harness.lower() or "manual" in harness.lower():
            return False, "Deferred or manual evaluation does not satisfy automated session eval criteria."
        return True, "Automated evaluation dataset / replay harness declared."

    @classmethod
    def _eval_off_switch(cls, off_switch: str) -> tuple[bool, str]:
        if not off_switch or len(off_switch.strip()) < 8:
            return False, "Missing off-switch specification. Action-taking agents must define an explicit interrupt."
        return True, "Operator off-switch / rollback mechanism verified."
