"""Atomic step execution engine for Reason + Act reasoning loops."""

from __future__ import annotations

from typing import Any

import structlog

from harness.agent.base import AgentStep, AgentTrajectory
from harness.agent.context_optimizer import (
    AgentContextOptimizer,
    DefaultContextOptimizer,
)
from harness.events.bus import EventBus
from harness.events.types import (
    EventType,
    llm_event,
)
from harness.kernel.context import ServiceContext
from harness.services.llm import LLMMessage, LLMService
from harness.services.tools import ToolRegistry

from .dispatch import dispatch_native_tool_calls, dispatch_text_fallback_action
from .prompting import build_react_initial_messages, extract_action_from_thought
from .transactions import invoke_tool_transactional

logger = structlog.get_logger()


class StepExecutionEngine:
    """Atomic step execution engine for Reason + Act reasoning loops.

    Encapsulates prompt construction, action extraction (native structured tool
    calls and markdown JSON fallback), tool dispatch with transactional boundaries,
    context budgeting/pruning, and observation synchronization.
    """

    def __init__(
        self,
        llm: LLMService | None = None,
        tools: ToolRegistry | None = None,
        event_bus: EventBus | None = None,
        context: ServiceContext | None = None,
        optimizer: AgentContextOptimizer | None = None,
    ) -> None:
        self.llm = llm  # type: ignore[assignment]
        self.tools = tools if tools is not None else ToolRegistry()
        self.event_bus = event_bus
        self.context: ServiceContext = (
            context if context is not None else ServiceContext()
        )
        self.optimizer: AgentContextOptimizer = optimizer or DefaultContextOptimizer(
            context=self.context
        )
        self._step_count: int = 0
        self._context_rotation_cadence: int = 25
        self.active_skills: list[str] = []

    async def _invoke_tool_safely(
        self, action_name: str, action_input: dict[str, Any]
    ) -> Any:
        """Invoke tool inside a transactional boundary if context supports transactions."""
        return await invoke_tool_transactional(
            context=self.context,
            tools=self.tools,
            action_name=action_name,
            action_input=action_input,
            active_skills=self.active_skills,
            state_holder=self,
        )

    def build_initial_messages(self, task: str) -> list[LLMMessage]:
        """Construct the standard ReAct system prompt and user task message."""
        messages, skills = build_react_initial_messages(
            task=task,
            tools=self.tools,
            optimizer=self.optimizer,
            context=self.context,
        )
        if skills:
            self.active_skills = skills
        return messages

    def extract_action(self, thought: str) -> tuple[str | None, dict[str, Any]]:
        """Extract action name and input parameters from thought text."""
        return extract_action_from_thought(thought)

    async def _rotate_context_if_needed(self) -> None:
        """Rotate session child context to bound inverse accumulator size."""
        self._step_count += 1
        if (
            self._step_count % self._context_rotation_cadence == 0
            and self.context.parent is not None
        ):
            parent = self.context.parent
            await self.context.dispose()
            self.context = parent.child()
            logger.debug("Session context rotated", step=self._step_count)

    async def execute_step(
        self,
        trajectory: AgentTrajectory | None = None,
        step_idx: int = 1,
        action_name: str | None = None,
        action_input: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a single atomic ReAct step or direct action invocation."""
        if action_name is not None:
            return await self._invoke_tool_safely(
                action_name, action_input if action_input is not None else {}
            )

        if trajectory is None:
            raise ValueError(
                "trajectory must be provided when action_name is not specified"
            )

        logger.info("Agent iteration", step=step_idx, task=trajectory.task[:50])
        await self._rotate_context_if_needed()

        if self.event_bus:
            await self.event_bus.emit(
                llm_event(
                    EventType.LLM_REQUEST,
                    source="agent.react",
                    step=step_idx,
                    message_count=len(trajectory.messages),
                )
            )

        # Context optimization & Rule 9 dynamic AST RepoMap injection
        effective = self.optimizer.optimize_messages(trajectory.messages)
        cfg = getattr(self.optimizer, "config", None)
        if cfg and cfg.repo_map_root:
            effective = self.optimizer.inject_repo_map(
                effective, query_context=trajectory.task, config=cfg
            )

        tool_schemas = self.tools.get_schemas()
        try:
            response = await self.llm.complete(
                effective, tools=tool_schemas if tool_schemas else None
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

        if "FINAL ANSWER:" in thought and not response.tool_calls:
            final_text = thought.split("FINAL ANSWER:", 1)[1].strip()
            trajectory.add_step(AgentStep(step_number=step_idx, thought=thought))
            trajectory.mark_completed(final_text)
            return False

        if response.tool_calls:
            await dispatch_native_tool_calls(
                tool_calls=response.tool_calls,
                thought=thought,
                tools=self.tools,
                optimizer=self.optimizer,
                trajectory=trajectory,
                step_idx=step_idx,
                invoke_fn=self._invoke_tool_safely,
            )
            return True

        act_name, act_inp = self.extract_action(thought)
        await dispatch_text_fallback_action(
            action_name=act_name,
            action_input=act_inp,
            thought=thought,
            tools=self.tools,
            optimizer=self.optimizer,
            trajectory=trajectory,
            step_idx=step_idx,
            invoke_fn=self._invoke_tool_safely,
        )
        return True
