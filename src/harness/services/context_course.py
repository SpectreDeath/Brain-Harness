"""Context Course service protocol, typed models, and ServiceKey.

Elevates the 6-layer context engineering stack (Skills, MCP, Plugins, Subagents, Hooks, Nano Harness)
from Hugging Face (Ben Burtenshaw 2026, ki_hf_context_engineering_six_layer_stack)
into a first-class micro-kernel IoC service seam.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class ContextAuditReport(BaseModel):
    """Payload representing 6-layer context engineering compliance evaluation."""

    overall_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Composite compliance score across the 6-layer stack",
    )
    layers_evaluated: dict[str, bool] = Field(
        ...,
        description="Presence of skills, mcp, plugins, subagents, hooks, and harness loop",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable recommendations to close context gaps",
    )
    token_budget_estimate: int = Field(
        ..., description="Estimated per-turn token budget required for active context"
    )
    status: str = Field(
        ..., description="Audit status: OPTIMIZED | PARTIAL | BLOATED | MINIMAL"
    )


class NanoHarnessRunResult(BaseModel):
    """Payload representing execution outcome of a sandboxed Nano Harness ReAct loop."""

    task: str = Field(..., description="The objective task assigned to the agent")
    steps_taken: int = Field(..., description="Number of ReAct steps executed")
    max_steps: int = Field(..., description="Configured upper bound for steps")
    final_answer: str = Field(
        ..., description="The terminal answer or settlement delivered"
    )
    success: bool = Field(
        ..., description="Whether the loop terminated with a successful final answer"
    )
    execution_log: list[str] = Field(
        default_factory=list,
        description="Ordered trajectory of thoughts, actions, and observations",
    )
    sandboxed_path: str = Field(
        ..., description="Confined workspace root used for safe_path"
    )


class SnippetLintResult(BaseModel):
    """Payload representing AST code-fence validation of context markdown and instructions."""

    snippets_count: int = Field(..., description="Total code blocks detected")
    valid_snippets: int = Field(..., description="Syntax-valid code blocks")
    invalid_snippets: int = Field(
        ..., description="Syntax-invalid or unparseable code blocks"
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Diagnostic error details for invalid snippets",
    )
    passed: bool = Field(
        ..., description="Whether 100% of tested code snippets passed syntax check"
    )


class SwarmDispatchResult(BaseModel):
    """Payload representing multi-agent subagent coordination topology planning."""

    topology: str = Field(
        ...,
        description="Recommended topology: FAN_OUT_FAN_IN | PIPELINE | SUPERVISOR | SINGLE_AGENT",
    )
    files_count: int = Field(..., description="Total files in task scope")
    subagents_planned: int = Field(
        ..., description="Recommended number of child subagents to spawn"
    )
    context_savings_percent: float = Field(
        ..., description="Estimated percentage of parent context tokens preserved"
    )
    rationale: str = Field(
        ..., description="Architectural reasoning for the selected topology"
    )


@runtime_checkable
class ContextCourseService(Protocol):
    """Service protocol for Hugging Face context engineering capabilities."""

    def audit_context_surface(self, project_dir: str | Path) -> ContextAuditReport:
        """Audit a project workspace against the 6-layer context engineering stack."""
        ...

    def run_nano_harness(
        self, task: str, workspace_root: str | Path, max_steps: int = 20
    ) -> NanoHarnessRunResult:
        """Execute a sandboxed, path-confined minimal ReAct agentic loop."""
        ...

    def verify_context_snippets(self, markdown_text: str) -> SnippetLintResult:
        """Parse and syntax-validate all fenced code snippets in markdown instructions."""
        ...

    def plan_subagent_topology(
        self, files_count: int, task_type: str = "general"
    ) -> SwarmDispatchResult:
        """Plan optimal subagent coordination topology using the 10+ files heuristic."""
        ...


CONTEXT_COURSE_SERVICE_KEY = ServiceKey[ContextCourseService]("service.context_course")
