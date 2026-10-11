"""Protocols and typed service keys for context optimizer service (Rule 2)."""

from __future__ import annotations

import sys
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey
from harness.services.llm import LLMMessage
from harness.services.context_optimizer.models import (
    ContextOptimizationConfig,
    ContextOptimizationResult,
    PruningMetric,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


@runtime_checkable
class ContextPruningStrategy(Protocol):
    """Protocol for modular pre-LLM message sequence pruning strategies."""

    @property
    def name(self) -> str:
        """Unique identifier of the pruning strategy."""
        ...

    def prune(
        self,
        messages: list[LLMMessage],
        *,
        config: ContextOptimizationConfig,
    ) -> tuple[list[LLMMessage], PruningMetric | None]:
        """Prune input messages and return (optimized_messages, metric)."""
        ...


@runtime_checkable
class ObservationCompactorStrategy(Protocol):
    """Protocol for compacting and truncating high-volume tool observations."""

    @property
    def name(self) -> str:
        """Unique identifier of the compaction strategy."""
        ...

    def compact(
        self,
        action_name: str,
        observation: Any,
        *,
        max_chars: int,
        compact_json: bool = True,
    ) -> str:
        """Compact raw tool observation into a bounded string representation."""
        ...


@runtime_checkable
class ContextOptimizerService(Protocol):
    """Authoritative protocol for agent context optimization, compaction, and budgeting."""

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

    def optimize_context(
        self,
        messages: list[LLMMessage],
        *,
        config: ContextOptimizationConfig | None = None,
        query_context: str | None = None,
    ) -> ContextOptimizationResult:
        """Execute complete multi-strategy optimization pipeline returning telemetry."""
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

    def register_strategy(self, strategy: ContextPruningStrategy) -> None:
        """Register a custom pruning strategy into the optimization pipeline."""
        ...


# Service Keys (Rule 2)
CONTEXT_OPTIMIZER_SERVICE_KEY: ServiceKey[ContextOptimizerService] = ServiceKey("service.context_optimizer")
AGENT_CONTEXT_OPTIMIZER_KEY: ServiceKey[ContextOptimizerService] = ServiceKey("agent.context_optimizer")

__all__ = [
    "AGENT_CONTEXT_OPTIMIZER_KEY",
    "CONTEXT_OPTIMIZER_SERVICE_KEY",
    "ContextOptimizerService",
    "ContextPruningStrategy",
    "ObservationCompactorStrategy",
]
