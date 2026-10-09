"""Tool call dispatching, observation compaction, and trajectory synchronization."""

from __future__ import annotations

import json
from typing import Any, Awaitable, Callable

from harness.agent.base import AgentStep, AgentTrajectory
from harness.agent.context_optimizer import AgentContextOptimizer
from harness.services.llm import LLMMessage
from harness.services.tools import ToolRegistry


async def dispatch_native_tool_calls(
    tool_calls: list[dict[str, Any]],
    thought: str,
    tools: ToolRegistry,
    optimizer: AgentContextOptimizer,
    trajectory: AgentTrajectory,
    step_idx: int,
    invoke_fn: Callable[[str, dict[str, Any]], Awaitable[Any]],
) -> None:
    """Process native structured LLM tool calls and synchronize trajectory state."""
    for tc in tool_calls:
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

        if action_name in tools:
            try:
                obs = await invoke_fn(action_name, action_input)
            except Exception as err:
                obs = {
                    "status": "error",
                    "error": f"Tool execution failed: {err}",
                }
            step.observation = obs
            compact_obs_str = optimizer.compact_observation(action_name, obs)
            trajectory.messages.append(
                LLMMessage(
                    role="assistant",
                    content=thought or f"Call: {action_name}",
                )
            )
            trajectory.messages.append(
                LLMMessage(
                    role="user",
                    content=f"Observation from {action_name}: {compact_obs_str}",
                    tool_call_id=tc.get("id"),
                )
            )
        else:
            obs = {
                "status": "error",
                "error": f"Tool '{action_name}' not found",
            }
            step.observation = obs
            compact_obs_str = optimizer.compact_observation(action_name, obs)
            trajectory.messages.append(
                LLMMessage(
                    role="assistant",
                    content=thought or f"Call: {action_name}",
                )
            )
            trajectory.messages.append(
                LLMMessage(
                    role="user",
                    content=f"Observation: {compact_obs_str}",
                )
            )

        trajectory.add_step(step)


async def dispatch_text_fallback_action(
    action_name: str | None,
    action_input: dict[str, Any],
    thought: str,
    tools: ToolRegistry,
    optimizer: AgentContextOptimizer,
    trajectory: AgentTrajectory,
    step_idx: int,
    invoke_fn: Callable[[str, dict[str, Any]], Awaitable[Any]],
) -> None:
    """Process text-extracted tool action fallback and synchronize trajectory state."""
    step = AgentStep(
        step_number=step_idx,
        thought=thought,
        action=action_name,
        action_input=action_input,
    )

    if action_name and action_name in tools:
        try:
            obs = await invoke_fn(action_name, action_input)
        except Exception as err:
            obs = {"status": "error", "error": f"Tool execution failed: {err}"}
        step.observation = obs
        compact_obs_str = optimizer.compact_observation(action_name, obs)
        trajectory.messages.append(LLMMessage(role="assistant", content=thought))
        trajectory.messages.append(
            LLMMessage(
                role="user",
                content=f"Observation from {action_name}: {compact_obs_str}",
            )
        )
    else:
        trajectory.messages.append(LLMMessage(role="assistant", content=thought))

    trajectory.add_step(step)
