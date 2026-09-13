"""Tests for Deepened Architecture Enhancements:
- Rule 12 & Rule 43 Slotted Dataclasses (AgentStep, AgentTaskResult, AgentTrajectory, SwarmNode)
- Rule 9 AST RepoMap Pre-LLM Injection in StepExecutionEngine
- Rule 6, Rule 10 & Rule 49 Click CLI Doc Seam and IoC Service Resolution
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click.testing
import pytest

from harness.agent.base import AgentStep, AgentTaskResult, AgentTrajectory
from harness.agent.context_optimizer import (
    ContextOptimizationConfig,
    DefaultContextOptimizer,
)
from harness.agent.react import StepExecutionEngine
from harness.agent.swarm import SwarmNode
from harness.cli import main
from harness.commands.doc import doc_group, get_doc_service
from harness.kernel.context import ServiceContext
from harness.services.doc_synchronizer import (
    DOC_SYNCHRONIZER_SERVICE_KEY,
    DocCoverageReportData,
)
from harness.services.llm import LLMMessage, LLMResponse, LLMService
from harness.services.repomap import REPO_MAP_SERVICE_KEY, DefaultRepoMapService
from harness.services.tools import ToolRegistry

# ---------------------------------------------------------------------------
# 1. Slotted Dataclass Contracts (Rule 12 & Rule 43)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSlottedAgentDataclasses:
    def test_agent_step_slots_and_validation(self) -> None:
        step = AgentStep(step_number=1, thought="Thinking", action="tool.test")
        assert hasattr(step, "__slots__")
        assert step.step_number == 1
        assert step.thought == "Thinking"

        # Rule 43: Direct attribute assignment verification for non-slotted fields
        with pytest.raises((AttributeError, TypeError)):
            step.unslotted_dynamic_field = "invalid"  # type: ignore[attr-defined]

        # __post_init__ validation for negative step numbers
        with pytest.raises(ValueError, match="step_number must be non-negative"):
            AgentStep(step_number=-1)

    def test_agent_task_result_slots(self) -> None:
        result = AgentTaskResult(task="Analyze codebase", status="completed")
        assert hasattr(result, "__slots__")
        assert result.task == "Analyze codebase"

        with pytest.raises((AttributeError, TypeError)):
            result.arbitrary_metadata_key = "forbidden"  # type: ignore[attr-defined]

    def test_agent_trajectory_slots(self) -> None:
        trajectory = AgentTrajectory(task="Build plugin")
        assert hasattr(trajectory, "__slots__")
        assert trajectory.status == "running"

        step = AgentStep(step_number=0, thought="Starting")
        trajectory.add_step(step)
        assert len(trajectory.steps) == 1

        with pytest.raises((AttributeError, TypeError)):
            trajectory.dynamic_runtime_patch = True  # type: ignore[attr-defined]

    def test_swarm_node_slots_and_validation(self) -> None:
        node = SwarmNode(id="worker_1", role="analyst", task="Analyze log data")
        assert hasattr(node, "__slots__")
        assert node.allocated_tokens == 10_000

        # Negative token allocation validation
        with pytest.raises(ValueError, match="allocated_tokens must be non-negative"):
            SwarmNode(
                id="worker_2", role="analyst", task="Run task", allocated_tokens=-100
            )

        with pytest.raises((AttributeError, TypeError)):
            node.untracked_attribute = "disallowed"  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. AST RepoMap Pre-LLM Injection into ReAct Step Loop (Rule 9)
# ---------------------------------------------------------------------------


class RecordingMockLLM(LLMService):
    def __init__(self, response_content: str = "FINAL ANSWER: Done") -> None:
        self.response_content = response_content
        self.received_messages: list[list[LLMMessage]] = []

    async def complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        self.received_messages.append(list(messages))
        return LLMResponse(content=self.response_content)

    async def stream(self, messages: list[LLMMessage], **kwargs: Any) -> Any:
        yield "mock"


@pytest.mark.unit
@pytest.mark.asyncio
class TestReActStepExecutionRepoMapInjection:
    async def test_step_engine_injects_repo_map_when_configured(self) -> None:
        context = ServiceContext()
        repo_map_svc = DefaultRepoMapService()
        context.provide(REPO_MAP_SERVICE_KEY, repo_map_svc)

        cfg = ContextOptimizationConfig(
            repo_map_root=str(Path.cwd() / "src" / "harness" / "agent"),
            repo_map_budget_tokens=1000,
        )
        optimizer = DefaultContextOptimizer(config=cfg, context=context)

        llm = RecordingMockLLM("FINAL ANSWER: Analyzed agents successfully")
        tools = ToolRegistry()

        engine = StepExecutionEngine(llm, tools, optimizer=optimizer)

        # Build initial messages
        initial_msgs = engine.build_initial_messages("Inspect agent definitions")

        # Initial messages must contain the injected Repository Map
        system_content = initial_msgs[0].content
        assert "Repository Map:" in system_content or "base.py" in system_content

        # Run step and verify LLM receives injected repository map
        trajectory = AgentTrajectory(
            task="Inspect agent definitions", messages=initial_msgs
        )
        cont = await engine.execute_step(trajectory, step_idx=1)

        assert cont is False  # FINAL ANSWER marks completion
        assert trajectory.status == "completed"
        assert len(trajectory.steps) == 1
        assert trajectory.steps[0].step_number == 1
        assert len(llm.received_messages) == 1
        llm_messages = llm.received_messages[0]
        assert any("Repository Map:" in m.content for m in llm_messages)


# ---------------------------------------------------------------------------
# 3. Click CLI Doc Seam and IoC Service Resolution (Rule 6, Rule 10, Rule 49)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDocCLICommandSeam:
    def setup_method(self) -> None:
        self.runner = click.testing.CliRunner()

    def test_doc_help_displays_subcommands(self) -> None:
        result = self.runner.invoke(doc_group, ["--help"])
        assert result.exit_code == 0
        assert "audit" in result.output
        assert "drift" in result.output
        assert "scaffold" in result.output
        assert "brief" in result.output
        assert "stats" in result.output

    def test_doc_stats_json(self) -> None:
        result = self.runner.invoke(doc_group, ["stats", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "hits" in data
        assert "misses" in data
        assert "cached_entries" in data

    def test_doc_stats_formatted(self) -> None:
        result = self.runner.invoke(doc_group, ["stats"])
        assert result.exit_code == 0
        assert "AST Parsing Cache Statistics:" in result.output

    def test_doc_audit_json(self) -> None:
        result = self.runner.invoke(
            doc_group,
            ["audit", "--target", "src/harness/agent", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_modules" in data
        assert data["total_modules"] >= 5
        assert "overall_coverage_pct" in data
        assert data["overall_coverage_pct"] >= 80.0
        assert data["passed"] is True

    def test_doc_scaffold_help(self) -> None:
        result = self.runner.invoke(doc_group, ["scaffold", "--help"])
        assert result.exit_code == 0
        assert "--type" in result.output
        assert "api" in result.output

    def test_doc_brief_help(self) -> None:
        result = self.runner.invoke(doc_group, ["brief", "--help"])
        assert result.exit_code == 0
        assert "--target" in result.output

    def test_main_cli_doc_group_integration(self) -> None:
        """Verify harness doc is discoverable via top-level main Click CLI."""
        result = self.runner.invoke(main, ["doc", "--help"])
        assert result.exit_code == 0
        assert "Repository documentation auditing" in result.output

    def test_get_doc_service_with_custom_context(self) -> None:
        """Verify IoC resolution via DOC_SYNCHRONIZER_SERVICE_KEY."""
        mock_service = type(
            "MockDocService",
            (),
            {
                "audit": lambda *a, **k: DocCoverageReportData(
                    scanned_root="mock",
                    total_modules=1,
                    modules_with_docstring=1,
                    total_symbols=1,
                    documented_symbols=1,
                    overall_coverage_pct=100.0,
                    passed=True,
                ),
                "drift_check": lambda *a, **k: None,
                "scaffold": lambda *a, **k: Path("mock.md"),
                "visual_brief": lambda *a, **k: Path("mock.html"),
                "get_cache_stats": lambda *a, **k: {
                    "hits": 10,
                    "misses": 0,
                    "cached_entries": 5,
                },
            },
        )()

        ctx = ServiceContext()
        ctx.provide(DOC_SYNCHRONIZER_SERVICE_KEY, mock_service)

        resolved = get_doc_service(ctx)
        assert resolved is mock_service
        stats = resolved.get_cache_stats()
        assert stats["hits"] == 10
