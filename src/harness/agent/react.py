"""ReAct Agent Plugin — autonomous Reason + Act execution loop.

Coordinates LLM reasoning with tool dispatching and event telemetry.
"""

from __future__ import annotations

import json
from typing import Any

import structlog

from harness.agent.base import (
    AGENT_LOOP_KEY,
    AgentLoopService,
    AgentStep,
    AgentTaskResult,
    AgentTrajectory,
)
from harness.agent.session import (
    AGENT_SESSION_MANAGER_KEY,
    AgentSessionManager,
)
from harness.events.bus import EVENT_BUS_KEY, EventBus
from harness.events.types import (
    EventType,
    agent_event,
    llm_event,
)
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.llm import LLM_SERVICE_KEY, LLMMessage, LLMService
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry

logger = structlog.get_logger()


class StepExecutionEngine:
    """Atomic step execution engine for Reason + Act reasoning loops.

    Encapsulates prompt construction, action extraction (native structured tool
    calls and markdown JSON fallback), tool dispatch with transactional boundaries,
    and observation synchronization.
    """

    def __init__(
        self,
        llm: LLMService,
        tools: ToolRegistry,
        event_bus: EventBus | None = None,
        context: ServiceContext | None = None,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.event_bus = event_bus
        self.context = context

    async def _invoke_tool_safely(self, action_name: str, action_input: dict[str, Any]) -> Any:
        """Invoke tool inside a transactional boundary if context supports transactions."""
        if self.context is not None and hasattr(self.context, "transaction"):
            async with self.context.transaction() as tx:
                prev_ctx = self.context
                self.context = tx
                try:
                    obs = await self.tools.invoke(action_name, action_input)
                    if isinstance(obs, dict) and obs.get("status") == "error":
                        # Roll back any intermediate context mutations performed during this failed tool call
                        await tx.dispose()
                    return obs
                finally:
                    self.context = prev_ctx
        return await self.tools.invoke(action_name, action_input)

    def build_initial_messages(self, task: str) -> list[LLMMessage]:
        """Construct the standard ReAct system prompt and user task message."""
        schemas = self.tools.get_schemas()
        return [
            LLMMessage(
                role="system",
                content=(
                    "You are an autonomous AI assistant running inside the Harness micro-kernel.\n"
                    "You solve tasks by reasoning and calling tools available to you.\n"
                    "Available tools:\n"
                    f"{json.dumps(schemas, indent=2)}\n\n"
                    "When deciding what to do, you can choose to call a tool or provide a final answer.\n"
                    "If providing a final answer, prefix with 'FINAL ANSWER: <your answer>'."
                ),
            ),
            LLMMessage(role="user", content=f"Task: {task}"),
        ]

    def extract_action(self, thought: str) -> tuple[str | None, dict[str, Any]]:
        """Extract action name and input parameters from thought text."""
        # 1. Check markdown fenced JSON blocks
        if "```json" in thought:
            try:
                json_str = thought.split("```json", 1)[1].split("```", 1)[0].strip()
                parsed = json.loads(json_str)
                if isinstance(parsed, dict) and "action" in parsed:
                    return parsed["action"], parsed.get("input", {})
            except Exception:
                pass

        # 2. Check direct raw JSON object
        if thought.strip().startswith("{") and thought.strip().endswith("}"):
            try:
                parsed = json.loads(thought.strip())
                if isinstance(parsed, dict) and "action" in parsed:
                    return parsed["action"], parsed.get("input", {})
            except Exception:
                pass

        return None, {}

    async def execute_step(self, trajectory: AgentTrajectory, step_idx: int) -> bool:
        """Execute a single atomic ReAct step on the trajectory.

        Args:
            trajectory: The active stateful execution trajectory.
            step_idx: 1-indexed step number.

        Returns:
            True if the agent should continue to the next step, False if finished.
        """
        logger.info("Agent iteration", step=step_idx, task=trajectory.task[:50])

        if self.event_bus:
            await self.event_bus.emit(
                llm_event(
                    EventType.LLM_REQUEST,
                    source="agent.react",
                    step=step_idx,
                    message_count=len(trajectory.messages),
                )
            )

        tool_schemas = self.tools.get_schemas()
        try:
            response = await self.llm.complete(
                trajectory.messages, tools=tool_schemas if tool_schemas else None
            )
        except Exception as e:
            logger.error("LLM call failed during agent loop", error=str(e))
            trajectory.mark_error(f"Error communicating with LLM: {e}")
            return False

        thought = response.content.strip()

        if self.event_bus:
            await self.event_bus.emit(
                llm_event(
                    EventType.LLM_RESPONSE,
                    source="agent.react",
                    step=step_idx,
                    content=thought[:200],
                    tool_calls_count=len(response.tool_calls),
                )
            )

        # Check if final answer reached directly
        if "FINAL ANSWER:" in thought and not response.tool_calls:
            final_text = thought.split("FINAL ANSWER:", 1)[1].strip()
            trajectory.add_step(AgentStep(step_number=step_idx, thought=thought))
            trajectory.mark_completed(final_text)
            return False

        # 1. Native Structured Tool Calls
        if response.tool_calls:
            for tc in response.tool_calls:
                fn_info = (
                    tc.get("function", {})
                    if isinstance(tc.get("function"), dict)
                    else tc
                )
                action_name = fn_info.get("name") or tc.get("name", "")
                raw_args = fn_info.get("arguments") or tc.get("arguments", {})
                if isinstance(raw_args, str):
                    try:
                        action_input = json.loads(raw_args)
                    except Exception:
                        action_input = {"raw": raw_args}
                elif isinstance(raw_args, dict):
                    action_input = raw_args
                else:
                    action_input = {}

                step = AgentStep(
                    step_number=step_idx,
                    thought=thought or f"Calling tool {action_name}",
                    action=action_name,
                    action_input=action_input,
                )

                if action_name in self.tools:
                    try:
                        obs = await self._invoke_tool_safely(action_name, action_input)
                    except Exception as err:
                        obs = {"status": "error", "error": f"Tool execution failed: {err}"}
                    step.observation = obs
                    trajectory.messages.append(
                        LLMMessage(
                            role="assistant",
                            content=thought or f"Call: {action_name}",
                        )
                    )
                    trajectory.messages.append(
                        LLMMessage(
                            role="user",
                            content=f"Observation from {action_name}: {json.dumps(obs)}",
                            tool_call_id=tc.get("id"),
                        )
                    )
                else:
                    obs = {"status": "error", "error": f"Tool '{action_name}' not found"}
                    step.observation = obs
                    trajectory.messages.append(
                        LLMMessage(
                            role="assistant",
                            content=thought or f"Call: {action_name}",
                        )
                    )
                    trajectory.messages.append(
                        LLMMessage(
                            role="user",
                            content=f"Observation: {json.dumps(obs)}",
                        )
                    )

                trajectory.add_step(step)
            return True

        # 2. Text-based Action Extraction Fallback
        action_name, action_input = self.extract_action(thought)

        step = AgentStep(
            step_number=step_idx,
            thought=thought,
            action=action_name,
            action_input=action_input,
        )

        if action_name and action_name in self.tools:
            try:
                obs = await self._invoke_tool_safely(action_name, action_input)
            except Exception as err:
                obs = {"status": "error", "error": f"Tool execution failed: {err}"}
            step.observation = obs
            trajectory.messages.append(LLMMessage(role="assistant", content=thought))
            trajectory.messages.append(
                LLMMessage(
                    role="user",
                    content=f"Observation from {action_name}: {json.dumps(obs)}",
                )
            )
        else:
            trajectory.messages.append(LLMMessage(role="assistant", content=thought))

        trajectory.add_step(step)
        return True


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
    ) -> None:
        self.llm = llm
        self.tools = tool_registry
        self.event_bus = event_bus
        self.session_manager = session_manager
        self.context = context
        self._step_engine = step_engine or StepExecutionEngine(
            llm=llm, tools=tool_registry, event_bus=event_bus, context=context
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
        traj = AgentTrajectory(
            task=task,
            messages=messages,
            metadata=context or {},
        )
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
        actual_session_id = session_id or (context or {}).get("session_id")

        if self.session_manager:
            async with self.session_manager.session_scope(
                task,
                session_id=actual_session_id,
                metadata=context,
                agent_name="agent.react",
                parent_session_id=parent_session_id,
            ) as scope:
                return await self._execute_task_loop(
                    task, max_steps=max_steps, context=context, session_id=scope.session_id, scope=scope
                )

        return await self._execute_task_loop(
            task, max_steps=max_steps, context=context, session_id=actual_session_id, scope=None
        )

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
            await self.event_bus.emit(
                agent_event(
                    EventType.AGENT_TASK_STARTED,
                    agent_name="agent.react",
                    task=task,
                    max_steps=max_steps,
                    session_id=session_id,
                )
            )

        for step_idx in range(1, max_steps + 1):
            if self.event_bus:
                await self.event_bus.emit(
                    agent_event(
                        EventType.AGENT_STEP_STARTED,
                        agent_name="agent.react",
                        task=task,
                        step=step_idx,
                        session_id=session_id,
                    )
                )

            should_continue = await self.step(trajectory, step_idx)

            if trajectory.steps:
                last_step = trajectory.steps[-1]
                if scope:
                    await scope.record_step(last_step)
                elif self.event_bus:
                    await self.event_bus.emit(
                        agent_event(
                            EventType.AGENT_STEP_COMPLETED,
                            agent_name="agent.react",
                            task=task,
                            step=step_idx,
                            action=last_step.action,
                            session_id=session_id,
                        )
                    )

            if not should_continue:
                break

        if trajectory.status == "running":
            trajectory.mark_max_steps()

        if scope:
            if trajectory.status == "completed":
                scope.mark_completed(trajectory.final_answer, total_tokens=trajectory.total_tokens)
            elif trajectory.status == "max_steps_reached":
                scope.mark_max_steps(trajectory.final_answer)
            else:
                scope.mark_error(trajectory.final_answer or "Agent execution failed")
        elif self.event_bus:
            evt_type = (
                EventType.AGENT_TASK_COMPLETED
                if trajectory.status in ("completed", "max_steps_reached")
                else EventType.AGENT_TASK_FAILED
            )
            await self.event_bus.emit(
                agent_event(
                    evt_type,
                    agent_name="agent.react",
                    task=task,
                    status=trajectory.status,
                    final_answer=trajectory.final_answer[:200],
                    steps_count=len(trajectory.steps),
                    session_id=session_id,
                )
            )

        return trajectory.to_result()


class ReActAgentPlugin(HarnessPlugin):
    """Plugin providing the ReAct agent loop service."""

    def __init__(self) -> None:
        self._loop: ReActAgentLoop | None = None
        self._ctx: ServiceContext | None = None

    @property
    def name(self) -> str:
        return "agent.react"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Autonomous ReAct Reason + Act agent execution loop"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [AGENT_LOOP_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return [LLM_SERVICE_KEY, TOOL_REGISTRY_KEY]

    @property
    def trusted(self) -> bool:
        return True

    async def on_load(self, ctx: ServiceContext) -> None:
        self._ctx = ctx

    async def on_enable(self) -> None:
        assert self._ctx is not None
        llm: LLMService = self._ctx.require(LLM_SERVICE_KEY)
        tools: ToolRegistry = self._ctx.require(TOOL_REGISTRY_KEY)
        event_bus: EventBus | None = self._ctx.optional(EVENT_BUS_KEY)
        session_manager: AgentSessionManager | None = self._ctx.optional(AGENT_SESSION_MANAGER_KEY)
        self._loop = ReActAgentLoop(
            llm=llm,
            tool_registry=tools,
            event_bus=event_bus,
            session_manager=session_manager,
            context=self._ctx,
        )
        self._ctx.provide(AGENT_LOOP_KEY, self._loop, provider=self.name, allow_override=True)
        logger.info(
            "ReAct agent loop enabled",
            telemetry=event_bus is not None,
            sessions=session_manager is not None,
        )

    async def on_disable(self) -> None:
        if self._ctx:
            self._ctx.revoke(AGENT_LOOP_KEY)
        self._loop = None

    async def on_unload(self) -> None:
        self._loop = None
        self._ctx = None
