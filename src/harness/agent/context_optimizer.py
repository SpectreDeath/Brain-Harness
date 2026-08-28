"""Agent context optimization, message budgeting, and compaction seam.

Provides pluggable context pruning, observation compaction, turn windowing,
and optional AST code skeletonization for autonomous agent loops.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.llm import LLMMessage

logger = structlog.get_logger()

AGENT_CONTEXT_OPTIMIZER_KEY: ServiceKey[AgentContextOptimizer] = ServiceKey("agent.context_optimizer")


@dataclass
class ContextOptimizationConfig:
    """Configuration knobs for agent context budgeting and compaction."""

    max_observation_chars: int = 4000
    max_total_messages: int = 30
    recent_messages_preserve: int = 6
    compact_json: bool = True
    enable_pruning: bool = True
    token_budget: int = 16000


@runtime_checkable
class AgentContextOptimizer(Protocol):
    """Protocol for pluggable agent context optimization and budgeting."""

    def compact_observation(
        self,
        action_name: str,
        observation: Any,
        *,
        max_chars: int | None = None,
    ) -> str:
        """Compact a raw tool observation into a token-efficient representation."""
        ...

    def optimize_messages(
        self,
        messages: list[LLMMessage],
        *,
        config: ContextOptimizationConfig | None = None,
    ) -> list[LLMMessage]:
        """Prune and budget messages before sending to the LLM completion endpoint."""
        ...


class DefaultContextOptimizer:
    """Standard context optimizer implementing token budgeting, json compaction, and windowing."""

    def __init__(
        self,
        config: ContextOptimizationConfig | None = None,
        context: ServiceContext | None = None,
    ) -> None:
        self.config = config or ContextOptimizationConfig()
        self.context = context

    def compact_observation(
        self,
        action_name: str,
        observation: Any,
        *,
        max_chars: int | None = None,
    ) -> str:
        """Compact tool observations, collapsing deep JSON structures and truncating huge outputs."""
        eff_max_chars = max_chars or self.config.max_observation_chars

        if observation is None:
            return "Observation: None"

        if isinstance(observation, str):
            text = observation.strip()
            if len(text) > eff_max_chars:
                head = text[: eff_max_chars // 2]
                tail = text[-eff_max_chars // 2 :]
                omitted = len(text) - len(head) - len(tail)
                return f"{head}\n... [TRUNCATED {omitted} CHARS] ...\n{tail}"
            return text

        if isinstance(observation, (dict, list)):
            try:
                if self.config.compact_json:
                    text = json.dumps(observation, separators=(",", ":"), default=str)
                else:
                    text = json.dumps(observation, indent=2, default=str)
            except Exception:
                text = str(observation)

            if len(text) > eff_max_chars:
                head = text[: eff_max_chars // 2]
                tail = text[-eff_max_chars // 2 :]
                omitted = len(text) - len(head) - len(tail)
                return f"{head}\n... [TRUNCATED JSON {omitted} CHARS] ...\n{tail}"
            return text

        return str(observation)

    def optimize_messages(
        self,
        messages: list[LLMMessage],
        *,
        config: ContextOptimizationConfig | None = None,
    ) -> list[LLMMessage]:
        """Apply deterministic windowing and pruning while preserving system and task anchors."""
        cfg = config or self.config
        if not cfg.enable_pruning or len(messages) <= cfg.max_total_messages:
            return list(messages)

        # Check if an external UnifiedContextPipeline or ContextCompactor is registered in context
        if self.context is not None:
            try:
                # Try domain.unified_context_pipeline key lookup
                ucp_key = ServiceKey[Any]("domain.unified_context_pipeline")
                if hasattr(self.context, "has") and self.context.has(ucp_key):
                    ucp = self.context.require(ucp_key)
                    if hasattr(ucp, "process"):
                        # Format as dict list and process
                        dict_msgs = [
                            {"id": f"m_{i}", "role": m.role, "content": m.content}
                            for i, m in enumerate(messages)
                        ]
                        res = ucp.process("agent_ctx_opt", dict_msgs, advance_turn=False)
                        # Reconstitute into LLMMessage list
                        # If assembled prompt available, return anchor system + user prompt
                        if res.assembled_prompt:
                            return [
                                LLMMessage(role="system", content=messages[0].content if messages else ""),
                                LLMMessage(role="user", content=res.assembled_prompt),
                            ]
            except Exception as err:
                logger.debug("unified_pipeline_delegation_fallback", error=str(err))

        # Built-in deterministic sliding window:
        # Preserve: First 2 messages (system + initial user task prompt)
        # Preserve: Last N recent messages (cfg.recent_messages_preserve)
        if len(messages) <= 2:
            return list(messages)

        header = messages[:2]
        tail_count = max(2, cfg.recent_messages_preserve)
        tail = messages[-tail_count:]

        # Check if tail overlaps with header
        if len(header) + len(tail) >= len(messages):
            return list(messages)

        middle_count = len(messages) - len(header) - len(tail)
        summary_msg = LLMMessage(
            role="system",
            content=f"[CONTEXT PRUNING: {middle_count} intermediate reasoning steps and observations omitted for brevity]",
        )

        return [*header, summary_msg, *tail]


__all__ = [
    "AGENT_CONTEXT_OPTIMIZER_KEY",
    "AgentContextOptimizer",
    "ContextOptimizationConfig",
    "DefaultContextOptimizer",
]
