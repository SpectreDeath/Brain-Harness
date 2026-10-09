"""Reason + Act autonomous agent execution orchestrator loop."""

from __future__ import annotations

from typing import Any

from harness.agent.base import (
    AgentLoopService,
    AgentTaskResult,
    AgentTrajectory,
)
from harness.agent.context_optimizer import AgentContextOptimizer
from harness.agent.session import AgentSessionManager
from harness.events.bus import EventBus
from harness.events.types import (
    EventType,
    agent_event,
)
from harness.kernel.context import ServiceContext
from harness.services.llm import LLMService
from harness.services.tools import ToolRegistry

from .engine import StepExecutionEngine


class ReActAgentLoop(AgentLoopService):
    """Reason + Act autonomous agent execution orchestrator.

    Coordinates task initialization, iterative step execution through
    `StepExecutionEngine`, and trajectory state management.
    """

    def __init__(
        self,
        llm: LLMService,
        tool_registry: ToolRegistry,
        event_bus: EventBus | None = None,
        step_engine: StepExecutionEngine | None = None,
        session_manager: AgentSessionManager | None = None,
        context: ServiceContext | None = None,
        optimizer: AgentContextOptimizer | None = None,
    ) -> None:
        self.llm = llm
        self.tools = tool_registry
        self.event_bus = event_bus
        self.session_manager = session_manager
        self.context = context
        self._step_engine = step_engine or StepExecutionEngine(
            llm=llm,
            tools=tool_registry,
            event_bus=event_bus,
            context=context,
            optimizer=optimizer,
        )

    @property
    def step_engine(self) -> StepExecutionEngine:
        """The atomic step execution engine."""
        return self._step_engine

    def create_trajectory(
        self,
        task: str,
        context: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> AgentTrajectory:
        """Initialize a new stateful AgentTrajectory for a task."""
        messages = self._step_engine.build_initial_messages(task)
        traj = AgentTrajectory(task=task, messages=messages, metadata=context or {})
        if session_id:
            traj.session_id = session_id
        return traj

    async def step(self, trajectory: AgentTrajectory, step_idx: int) -> bool:
        """Execute a single atomic step against a trajectory."""
        return await self._step_engine.execute_step(trajectory, step_idx)

    async def run_task(
        self,
        task: str,
        *,
        max_steps: int = 10,
        context: dict[str, Any] | None = None,
        session_id: str | None = None,
        parent_session_id: str | None = None,
    ) -> AgentTaskResult:
        """Run an autonomous task with tool calling, reasoning, and reflection."""
        actual_id = session_id or (context or {}).get("session_id")
        if not self.session_manager:
            return await self._execute_task_loop(task, max_steps=max_steps, context=context, session_id=actual_id, scope=None)

        async with self.session_manager.session_scope(
            task, session_id=actual_id, metadata=context, agent_name="agent.react", parent_session_id=parent_session_id,
        ) as scope:
            return await self._execute_task_loop(task, max_steps=max_steps, context=context, session_id=scope.session_id, scope=scope)

    async def _execute_task_loop(
        self,
        task: str,
        *,
        max_steps: int,
        context: dict[str, Any] | None,
        session_id: str | None,
        scope: Any | None,
    ) -> AgentTaskResult:
        trajectory = self.create_trajectory(task, context=context, session_id=session_id)
        if not scope and self.event_bus:
            await self.event_bus.emit(agent_event(
                EventType.AGENT_TASK_STARTED, agent_name="agent.react", task=task, max_steps=max_steps, session_id=session_id,
            ))

        for step_idx in range(1, max_steps + 1):
            if self.event_bus:
                await self.event_bus.emit(agent_event(
                    EventType.AGENT_STEP_STARTED, agent_name="agent.react", task=task, step=step_idx, session_id=session_id,
                ))

            should_continue = await self.step(trajectory, step_idx)

            if trajectory.steps:
                last_step = trajectory.steps[-1]
                if scope:
                    await scope.record_step(last_step)
                elif self.event_bus:
                    await self.event_bus.emit(agent_event(
                        EventType.AGENT_STEP_COMPLETED, agent_name="agent.react", task=task,
                        step=step_idx, action=last_step.action, session_id=session_id,
                    ))

            if not should_continue:
                break

        if trajectory.status == "running":
            trajectory.mark_max_steps()

        await self._finalize_outcome(trajectory, scope, task, session_id)
        return trajectory.to_result()

    async def _finalize_outcome(
        self, trajectory: AgentTrajectory, scope: Any | None, task: str, session_id: str | None
    ) -> None:
        """Finalize outcome on session scope or event bus."""
        if scope:
            if trajectory.status == "completed":
                scope.mark_completed(trajectory.final_answer, total_tokens=trajectory.total_tokens)
            elif trajectory.status == "max_steps_reached":
                scope.mark_max_steps(trajectory.final_answer)
            else:
                scope.mark_error(trajectory.final_answer or "Agent execution failed")
        elif self.event_bus:
            evt = (
                EventType.AGENT_TASK_COMPLETED
                if trajectory.status in ("completed", "max_steps_reached")
                else EventType.AGENT_TASK_FAILED
            )
            await self.event_bus.emit(agent_event(
                evt, agent_name="agent.react", task=task, status=trajectory.status,
                final_answer=trajectory.final_answer[:200], steps_count=len(trajectory.steps), session_id=session_id,
            ))
