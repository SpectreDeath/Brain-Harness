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
from harness.services.repomap import REPO_MAP_SERVICE_KEY, DefaultRepoMapService, RepoMapService
from harness.services.unified_context import (
    UNIFIED_CONTEXT_PIPELINE_KEY,
    UnifiedContextPipelineService,
    UnifiedContextRequest,
)

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
    repo_map_root: str | None = None
    repo_map_budget_tokens: int = 1024


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

    def inject_repo_map(
        self,
        messages: list[LLMMessage],
        *,
        query_context: str | None = None,
        config: ContextOptimizationConfig | None = None,
    ) -> list[LLMMessage]:
        """Inject ranked AST repo map into the system prompt if repo_map_root is set."""
        ...


class DefaultContextOptimizer:
    """Standard context optimizer implementing token budgeting, json compaction, and windowing."""

    def __init__(
        self,
        config: ContextOptimizationConfig | None = None,
        context: ServiceContext | None = None,
    ) -> None:
        self.config = config or ContextOptimizationConfig()
        self.context: ServiceContext = context if context is not None else ServiceContext()

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
        """Apply multi-pass progressive context optimization across conversation history."""
        cfg = config or self.config
        if not cfg.enable_pruning or len(messages) <= cfg.max_total_messages:
            return list(messages)

        # Check if an authoritative UnifiedContextPipeline is registered in context
        if self.context.has(UNIFIED_CONTEXT_PIPELINE_KEY):
            try:
                ucp = self.context.require(UNIFIED_CONTEXT_PIPELINE_KEY)
                dict_msgs = [{"role": m.role, "content": m.content} for m in messages]
                req = UnifiedContextRequest(
                    messages=dict_msgs,
                    token_budget=cfg.token_budget,
                    max_observation_chars=cfg.max_observation_chars,
                    recent_messages_preserve=cfg.recent_messages_preserve,
                    repo_map_root=cfg.repo_map_root,
                    repo_map_budget_tokens=cfg.repo_map_budget_tokens,
                )
                res = ucp.process_context(req)
                if res.status == "ok" and res.assembled_messages:
                    return [
                        LLMMessage(role=m.get("role", "user"), content=m.get("content", ""))
                        for m in res.assembled_messages
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

    def inject_repo_map(
        self,
        messages: list[LLMMessage],
        *,
        query_context: str | None = None,
        config: ContextOptimizationConfig | None = None,
    ) -> list[LLMMessage]:
        """Inject a PageRanked AST repo map into the system prompt if repo_map_root is set."""
        cfg = config or self.config
        if not cfg.repo_map_root or not messages:
            return messages

        repo_map_svc: RepoMapService = self.context.optional(REPO_MAP_SERVICE_KEY) or DefaultRepoMapService()

        # Extract query context from last user message if not passed
        eff_query = query_context
        if not eff_query:
            for m in reversed(messages):
                if m.role == "user":
                    eff_query = m.content
                    break

        map_res = repo_map_svc.get_repo_map(
            cfg.repo_map_root,
            query_context=eff_query,
            max_tokens=cfg.repo_map_budget_tokens,
        )

        if map_res.status != "ok" or not map_res.formatted_map or map_res.formatted_map.startswith("No indexed"):
            return messages

        new_msgs = list(messages)
        first = new_msgs[0]
        if first.role == "system":
            enhanced_sys = (
                f"{first.content}\n\n"
                f"### Repository Map:\n"
                f"```\n{map_res.formatted_map}\n```"
            )
            new_msgs[0] = LLMMessage(role="system", content=enhanced_sys)
        return new_msgs


__all__ = [
    "AGENT_CONTEXT_OPTIMIZER_KEY",
    "AgentContextOptimizer",
    "ContextOptimizationConfig",
    "DefaultContextOptimizer",
]
