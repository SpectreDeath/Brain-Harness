"""Contract test suite for Context Engineering Architect skill engine.

Verifies slotted/frozen dataclass immutability (Rule 12, Rule 43), safe_path path confinement (Unit 6),
AST snippet verification (Unit tests), and subagent topology planning (Unit 4).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ws_root = Path(__file__).resolve().parent.parent
_skill_scripts = (
    _ws_root / ".agents" / "skills" / "context-engineering-architect" / "scripts"
)
for _p in [_ws_root / "src", _skill_scripts, _ws_root]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from context_engineering_engine import (
    ContextEngineeringEngine,
    ContextStackScore,
    NanoHarnessTrajectory,
    ReActStep,
    SnippetAudit,
    SubagentTopologyPlan,
)


@pytest.mark.unit
class TestContextEngineeringDataclasses:
    """Verify slotted and frozen dataclass construction and immutability (Rule 12, Rule 43)."""

    def test_context_stack_score_immutability(self) -> None:
        score = ContextStackScore(
            overall_score=0.83,
            has_skills=True,
            has_mcp=True,
            has_plugins=True,
            has_subagents=True,
            has_hooks=True,
            has_harness_loop=False,
            recommendations=("Add harness loop",),
            token_budget_estimate=3500,
            status="OPTIMIZED",
        )
        assert score.overall_score == 0.83
        assert score.has_skills is True
        assert score.status == "OPTIMIZED"

        # Direct attribute assignment must raise AttributeError/TypeError (Rule 43)
        with pytest.raises((AttributeError, TypeError)):
            score.overall_score = 0.99  # type: ignore[misc]

    def test_react_step_immutability(self) -> None:
        step = ReActStep(
            step_number=1,
            thought="Inspecting root",
            action_tool="list_dir",
            action_input=".",
            observation="file1.txt",
        )
        assert step.step_number == 1
        with pytest.raises((AttributeError, TypeError)):
            step.thought = "Mutated"  # type: ignore[misc]

    def test_nano_harness_trajectory_immutability(self) -> None:
        traj = NanoHarnessTrajectory(
            task="Audit repository",
            steps_taken=2,
            max_steps=10,
            final_answer="Done",
            success=True,
            sandboxed_root="/tmp/sandbox",
        )
        assert traj.success is True
        with pytest.raises((AttributeError, TypeError)):
            traj.success = False  # type: ignore[misc]

    def test_snippet_audit_immutability(self) -> None:
        audit = SnippetAudit(
            total_snippets=3,
            valid_snippets=3,
            invalid_snippets=0,
            passed=True,
        )
        assert audit.passed is True
        with pytest.raises((AttributeError, TypeError)):
            audit.total_snippets = 10  # type: ignore[misc]

    def test_subagent_topology_plan_immutability(self) -> None:
        plan = SubagentTopologyPlan(
            topology="FAN_OUT_FAN_IN",
            files_count=15,
            subagents_planned=3,
            context_savings_percent=60.0,
            rationale="15 files touch",
        )
        assert plan.topology == "FAN_OUT_FAN_IN"
        with pytest.raises((AttributeError, TypeError)):
            plan.files_count = 5  # type: ignore[misc]


@pytest.mark.unit
class TestPathConfinementSafePath:
    """Verify Unit 6 safe_path sandboxing against path traversal escapes."""

    def test_safe_path_valid_subpath(self, tmp_path: Path) -> None:
        subfile = tmp_path / "src" / "main.py"
        resolved = ContextEngineeringEngine.safe_path("src/main.py", tmp_path)
        assert resolved == subfile.resolve()

    def test_safe_path_absolute_within_workspace(self, tmp_path: Path) -> None:
        subfile = tmp_path / "data.json"
        resolved = ContextEngineeringEngine.safe_path(str(subfile), tmp_path)
        assert resolved == subfile.resolve()

    def test_safe_path_traversal_escape_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(PermissionError, match="Path confinement violation"):
            ContextEngineeringEngine.safe_path("../../outside.txt", tmp_path)

    def test_safe_path_absolute_outside_workspace_rejected(
        self, tmp_path: Path
    ) -> None:
        outside = Path(tmp_path.parent / "escape.txt").resolve()
        with pytest.raises(PermissionError, match="Path confinement violation"):
            ContextEngineeringEngine.safe_path(str(outside), tmp_path)


@pytest.mark.unit
class TestContextSurfaceAuditor:
    """Verify 6-layer context engineering surface evaluation."""

    def test_audit_nonexistent_directory(self) -> None:
        report = ContextEngineeringEngine.audit_context_surface(
            "nonexistent_path_xyz_123"
        )
        assert report.overall_score == 0.0
        assert report.status == "MINIMAL"

    def test_audit_workspace_root(self) -> None:
        workspace = Path(__file__).resolve().parents[1]
        report = ContextEngineeringEngine.audit_context_surface(workspace)
        assert 0.0 <= report.overall_score <= 1.0
        assert report.has_skills is True  # .agents/skills exists in repo
        assert report.token_budget_estimate > 0
        assert isinstance(report.recommendations, tuple)


@pytest.mark.unit
class TestSnippetVerification:
    """Verify AST code-fence validation."""

    def test_valid_python_and_json_snippets(self) -> None:
        markdown = """
Here is valid Python:
```python
def add(a: int, b: int) -> int:
    return a + b
```
And valid JSON:
```json
{
  "name": "harness",
  "version": "1.0.0"
}
```
"""
        audit = ContextEngineeringEngine.verify_snippets(markdown)
        assert audit.total_snippets == 2
        assert audit.valid_snippets == 2
        assert audit.invalid_snippets == 0
        assert audit.passed is True
        assert len(audit.errors) == 0

    def test_invalid_python_syntax(self) -> None:
        markdown = """
```python
def broken_syntax(
    return "missing closing paren"
```
"""
        audit = ContextEngineeringEngine.verify_snippets(markdown)
        assert audit.total_snippets == 1
        assert audit.valid_snippets == 0
        assert audit.invalid_snippets == 1
        assert audit.passed is False
        assert any("Python syntax error" in e for e in audit.errors)

    def test_invalid_json_syntax(self) -> None:
        markdown = """
```json
{
  "unclosed": "missing brace"
```
"""
        audit = ContextEngineeringEngine.verify_snippets(markdown)
        assert audit.total_snippets == 1
        assert audit.valid_snippets == 0
        assert audit.invalid_snippets == 1
        assert audit.passed is False
        assert any("JSON syntax error" in e for e in audit.errors)


@pytest.mark.unit
class TestSubagentTopologyPlanner:
    """Verify subagent coordination topology planning under the 10+ files heuristic (Unit 4)."""

    def test_below_threshold_single_agent(self) -> None:
        plan = ContextEngineeringEngine.plan_subagent_topology(files_count=4)
        assert plan.topology == "SINGLE_AGENT"
        assert plan.subagents_planned == 0
        assert plan.context_savings_percent == 0.0

    def test_ten_plus_files_review_fan_out(self) -> None:
        plan = ContextEngineeringEngine.plan_subagent_topology(
            files_count=15, task_type="code_review"
        )
        assert plan.topology == "FAN_OUT_FAN_IN"
        assert plan.subagents_planned >= 2
        assert plan.context_savings_percent > 0.0

    def test_ten_plus_files_refactor_pipeline(self) -> None:
        plan = ContextEngineeringEngine.plan_subagent_topology(
            files_count=12, task_type="refactor_pipeline"
        )
        assert plan.topology == "PIPELINE"
        assert plan.subagents_planned == 3

    def test_ten_plus_files_general_supervisor(self) -> None:
        plan = ContextEngineeringEngine.plan_subagent_topology(
            files_count=20, task_type="general"
        )
        assert plan.topology == "SUPERVISOR"
        assert plan.subagents_planned >= 2


@pytest.mark.unit
class TestNanoHarnessExecution:
    """Verify Unit 6 sandboxed minimal ReAct loop execution."""

    def test_nano_harness_step_trajectory(self, tmp_path: Path) -> None:
        # Create a sample file inside tmp_path
        (tmp_path / "hello.py").write_text("print('hello world')", encoding="utf-8")

        traj = ContextEngineeringEngine.run_nano_harness(
            task="Inspect hello.py and verify content",
            workspace_root=tmp_path,
            max_steps=5,
        )
        assert traj.success is True
        assert traj.steps_taken == 2
        assert len(traj.steps) == 2
        assert traj.steps[0].action_tool == "list_dir"
        assert traj.steps[1].action_tool == "final_answer"
        assert "hello.py" in traj.steps[0].observation
        assert traj.sandboxed_root == str(tmp_path)
