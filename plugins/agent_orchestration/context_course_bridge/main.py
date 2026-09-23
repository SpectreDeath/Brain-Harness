"""Context Course Bridge Plugin — 6-Layer Context Engineering Engine.

Synthesized from Hugging Face The Context Course (Ben Burtenshaw et al., 2026),
grounded in ki_hf_context_engineering_six_layer_stack.
Provides in-memory micro-kernel IoC service implementation (Rule 45 & Rule 49).
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

# Dynamically ensure skill scripts directory and harness src are on sys.path
_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_SKILL_SCRIPTS = (
    _REPO_ROOT / ".agents" / "skills" / "context-engineering-architect" / "scripts"
)
_HARNESS_SRC = _REPO_ROOT / "src"

for _p in [_SKILL_SCRIPTS, _HARNESS_SRC]:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from context_engineering_engine import (  # type: ignore
    ContextEngineeringEngine,
    ContextStackScore,
    NanoHarnessTrajectory,
    SnippetAudit,
    SubagentTopologyPlan,
)

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.context_course import (
    CONTEXT_COURSE_SERVICE_KEY,
    ContextAuditReport,
    ContextCourseService,
    NanoHarnessRunResult,
    SnippetLintResult,
    SwarmDispatchResult,
)

logger = structlog.get_logger(__name__)


class ContextCourseBridgePlugin(HarnessPlugin, ContextCourseService):
    """Plugin providing 6-layer context engineering, FastMCP, and Nano Harness capabilities."""

    def __init__(self, root_dir: Path | str | None = None) -> None:
        super().__init__()
        self._root = Path(root_dir or _REPO_ROOT).resolve()
        self._engine = ContextEngineeringEngine()

    @property
    def name(self) -> str:
        return "plugin.context_course_bridge"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Hugging Face Context Engineering Bridge: 6-layer stack auditor, "
            "FastMCP validator, subagent swarm planner, and sandboxed Nano Harness ReAct loop"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [CONTEXT_COURSE_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register the service singleton in the IoC container (Rule 45)."""
        context.provide(CONTEXT_COURSE_SERVICE_KEY, self)
        logger.info(
            "context_course_bridge_plugin_loaded",
            name=self.name,
            version=self.version,
            key=str(CONTEXT_COURSE_SERVICE_KEY),
        )

    async def on_unload(self, context: ServiceContext) -> None:
        """Clean up on plugin unload."""
        logger.info("context_course_bridge_plugin_unloaded", name=self.name)

    def audit_context_surface(self, project_dir: str | Path) -> ContextAuditReport:
        """Audit project directory against the 6-layer context engineering stack."""
        score: ContextStackScore = self._engine.audit_context_surface(project_dir)
        layers = {
            "skills": score.has_skills,
            "mcp": score.has_mcp,
            "plugins": score.has_plugins,
            "subagents": score.has_subagents,
            "hooks": score.has_hooks,
            "harness_loop": score.has_harness_loop,
        }
        return ContextAuditReport(
            overall_score=score.overall_score,
            layers_evaluated=layers,
            recommendations=list(score.recommendations),
            token_budget_estimate=score.token_budget_estimate,
            status=score.status,
        )

    def run_nano_harness(
        self, task: str, workspace_root: str | Path, max_steps: int = 20
    ) -> NanoHarnessRunResult:
        """Execute a sandboxed, path-confined minimal ReAct agentic step loop."""
        traj: NanoHarnessTrajectory = self._engine.run_nano_harness(
            task=task, workspace_root=workspace_root, max_steps=max_steps
        )
        logs = [
            f"Step {s.step_number}: Thought='{s.thought}', Action={s.action_tool}({s.action_input}) -> Observation='{s.observation}'"
            for s in traj.steps
        ]
        return NanoHarnessRunResult(
            task=traj.task,
            steps_taken=traj.steps_taken,
            max_steps=traj.max_steps,
            final_answer=traj.final_answer,
            success=traj.success,
            execution_log=logs,
            sandboxed_path=traj.sandboxed_root,
        )

    def verify_context_snippets(self, markdown_text: str) -> SnippetLintResult:
        """Parse and syntax-validate all fenced code snippets in markdown instructions."""
        audit: SnippetAudit = self._engine.verify_snippets(markdown_text)
        return SnippetLintResult(
            snippets_count=audit.total_snippets,
            valid_snippets=audit.valid_snippets,
            invalid_snippets=audit.invalid_snippets,
            errors=list(audit.errors),
            passed=audit.passed,
        )

    def plan_subagent_topology(
        self, files_count: int, task_type: str = "general"
    ) -> SwarmDispatchResult:
        """Plan optimal subagent coordination topology using the 10+ files heuristic."""
        plan: SubagentTopologyPlan = self._engine.plan_subagent_topology(
            files_count=files_count, task_type=task_type
        )
        return SwarmDispatchResult(
            topology=plan.topology,
            files_count=plan.files_count,
            subagents_planned=plan.subagents_planned,
            context_savings_percent=plan.context_savings_percent,
            rationale=plan.rationale,
        )


# Module-level singleton (Rule 45)
plugin = ContextCourseBridgePlugin()


# Top-level tool entrypoints
def audit_context_surface(project_dir: str) -> dict[str, Any]:
    """Audit project directory against 6-layer context engineering stack."""
    rep = plugin.audit_context_surface(project_dir)
    return rep.model_dump()


def run_nano_harness(
    task: str, workspace_root: str, max_steps: int = 20
) -> dict[str, Any]:
    """Execute sandboxed Nano Harness ReAct loop."""
    res = plugin.run_nano_harness(task, workspace_root, max_steps)
    return res.model_dump()


def verify_context_snippets(markdown_text: str) -> dict[str, Any]:
    """Verify code fences in markdown text."""
    res = plugin.verify_context_snippets(markdown_text)
    return res.model_dump()


def plan_subagent_topology(
    files_count: int, task_type: str = "general"
) -> dict[str, Any]:
    """Plan subagent swarm topology."""
    res = plugin.plan_subagent_topology(files_count, task_type)
    return res.model_dump()
