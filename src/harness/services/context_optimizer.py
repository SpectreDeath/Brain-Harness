"""Context Optimizer Service, Composable Pruning Strategies, and Slotted Domain Models.

Provides an authoritative micro-kernel service for:
1. Composable pre-LLM message pruning strategies (sliding window, middle-out compaction, AST RepoMap).
2. Slotted, frozen configuration and diagnostic telemetry results (Rule 12 & Rule 43).
3. Pluggable observation compaction with character and JSON boundary controls.
4. Seamless fallback and IoC container integration (Rule 1, Rule 2, Rule 49, Rule 58).
5. 100% backward-compatible support for StepExecutionEngine and SwarmCoordinator.
"""

from __future__ import annotations

import json
import math
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.llm import LLMMessage
from harness.services.repomap import (
    REPO_MAP_SERVICE_KEY,
    DefaultRepoMapService,
    RepoMapService,
)
from harness.services.unified_context import (
    UNIFIED_CONTEXT_PIPELINE_KEY,
    UnifiedContextRequest,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = structlog.get_logger("harness.services.context_optimizer")


# =============================================================================
# Slotted & Frozen Domain Models (Rule 12 & Rule 43)
# =============================================================================

@dataclass(slots=True, frozen=True)
class ContextOptimizationConfig:
    """Slotted, frozen configuration knobs for agent context budgeting and compaction."""

    max_observation_chars: int = 4000
    max_total_messages: int = 30
    recent_messages_preserve: int = 6
    compact_json: bool = True
    enable_pruning: bool = True
    token_budget: int = 16000
    repo_map_root: str | None = None
    repo_map_budget_tokens: int = 1024

    def __post_init__(self) -> None:
        assert self.max_observation_chars > 0, "max_observation_chars must be positive"
        assert self.max_total_messages >= 2, "max_total_messages must be >= 2"
        assert self.recent_messages_preserve >= 1, "recent_messages_preserve must be >= 1"
        assert self.token_budget > 0, "token_budget must be positive"
        assert self.repo_map_budget_tokens >= 0, "repo_map_budget_tokens must be non-negative"

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_observation_chars": self.max_observation_chars,
            "max_total_messages": self.max_total_messages,
            "recent_messages_preserve": self.recent_messages_preserve,
            "compact_json": self.compact_json,
            "enable_pruning": self.enable_pruning,
            "token_budget": self.token_budget,
            "repo_map_root": self.repo_map_root,
            "repo_map_budget_tokens": self.repo_map_budget_tokens,
        }


@dataclass(slots=True, frozen=True)
class PruningMetric:
    """Diagnostic execution telemetry for a single pruning strategy pass."""

    strategy_name: str
    initial_count: int
    pruned_count: int
    estimated_tokens_before: int
    estimated_tokens_after: int
    duration_ms: float = 0.0

    def __post_init__(self) -> None:
        assert self.strategy_name, "strategy_name cannot be empty"
        assert self.initial_count >= 0, "initial_count must be non-negative"
        assert self.pruned_count >= 0, "pruned_count must be non-negative"

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy_name,
            "initial_messages": self.initial_count,
            "pruned_messages": self.pruned_count,
            "tokens_before": self.estimated_tokens_before,
            "tokens_after": self.estimated_tokens_after,
            "duration_ms": self.duration_ms,
        }


@dataclass(slots=True, frozen=True)
class ContextOptimizationResult:
    """Slotted, frozen evaluation result of a complete pre-LLM context optimization run."""

    status: str = "ok"
    messages: tuple[LLMMessage, ...] = field(default_factory=tuple)
    original_count: int = 0
    optimized_count: int = 0
    estimated_tokens: int = 0
    repo_map_injected: bool = False
    metrics: tuple[PruningMetric, ...] = field(default_factory=tuple)
    error: str | None = None

    def __post_init__(self) -> None:
        assert self.status in ("ok", "error"), f"Invalid status: {self.status}"
        assert self.original_count >= 0, "original_count must be non-negative"
        assert self.optimized_count >= 0, "optimized_count must be non-negative"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "original_count": self.original_count,
            "optimized_count": self.optimized_count,
            "estimated_tokens": self.estimated_tokens,
            "repo_map_injected": self.repo_map_injected,
            "metrics": [m.to_dict() for m in self.metrics],
            "error": self.error,
        }


# =============================================================================
# Helper Utilities
# =============================================================================

def estimate_tokens(messages: list[LLMMessage] | tuple[LLMMessage, ...]) -> int:
    """Fast character-based heuristic token estimator (~4 chars per token)."""
    total_chars = sum(len(m.content or "") for m in messages)
    return max(1, total_chars // 4) if messages else 0


# =============================================================================
# Strategy Protocols & Service Interfaces
# =============================================================================

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


# =============================================================================
# Built-in Strategy Implementations
# =============================================================================

class MiddleOutObservationCompactor:
    """Default observation compactor with progressive middle-out string and JSON truncation."""

    @property
    def name(self) -> str:
        return "middle_out_compactor"

    def compact(
        self,
        action_name: str,
        observation: Any,
        *,
        max_chars: int,
        compact_json: bool = True,
    ) -> str:
        if observation is None:
            return "Observation: None"

        if isinstance(observation, str):
            text = observation.strip()
            if len(text) > max_chars:
                head = text[: max_chars // 2]
                tail = text[-max_chars // 2 :]
                omitted = len(text) - len(head) - len(tail)
                return f"{head}\n... [TRUNCATED {omitted} CHARS] ...\n{tail}"
            return text

        if isinstance(observation, (dict, list)):
            try:
                if compact_json:
                    text = json.dumps(observation, separators=(",", ":"), default=str)
                else:
                    text = json.dumps(observation, indent=2, default=str)
            except Exception:
                text = str(observation)

            if len(text) > max_chars:
                head = text[: max_chars // 2]
                tail = text[-max_chars // 2 :]
                omitted = len(text) - len(head) - len(tail)
                return f"{head}\n... [TRUNCATED JSON {omitted} CHARS] ...\n{tail}"
            return text

        return str(observation)


class SlidingWindowPruner:
    """Sliding-window pruner preserving system/user prompt anchors and recent turns."""

    @property
    def name(self) -> str:
        return "sliding_window_pruner"

    def prune(
        self,
        messages: list[LLMMessage],
        *,
        config: ContextOptimizationConfig,
    ) -> tuple[list[LLMMessage], PruningMetric | None]:
        t0 = time.perf_counter()
        initial_count = len(messages)
        tokens_before = estimate_tokens(messages)

        if not config.enable_pruning or initial_count <= config.max_total_messages:
            return list(messages), None

        if initial_count <= 2:
            return list(messages), None

        header = messages[:2]
        tail_count = max(2, config.recent_messages_preserve)
        tail = messages[-tail_count:]

        # If overlap, no pruning possible
        if len(header) + len(tail) >= initial_count:
            return list(messages), None

        middle_count = initial_count - len(header) - len(tail)
        summary_msg = LLMMessage(
            role="system",
            content=f"[CONTEXT PRUNING: {middle_count} intermediate reasoning steps and observations omitted for brevity]",
        )

        pruned = [*header, summary_msg, *tail]
        tokens_after = estimate_tokens(pruned)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        metric = PruningMetric(
            strategy_name=self.name,
            initial_count=initial_count,
            pruned_count=len(pruned),
            estimated_tokens_before=tokens_before,
            estimated_tokens_after=tokens_after,
            duration_ms=elapsed_ms,
        )

        return pruned, metric


class RepoMapInjectionStrategy:
    """Injects PageRanked AST Repo Map into system prompt if repo_map_root is set (Rule 9)."""

    def __init__(self, context: ServiceContext | None = None) -> None:
        self.context = context

    @property
    def name(self) -> str:
        return "repo_map_injection"

    def _resolve_repomap_service(self) -> RepoMapService:
        if self.context is not None and hasattr(self.context, "has") and self.context.has(REPO_MAP_SERVICE_KEY):
            return self.context.require(REPO_MAP_SERVICE_KEY)
        return DefaultRepoMapService()

    def inject(
        self,
        messages: list[LLMMessage],
        *,
        config: ContextOptimizationConfig,
        query_context: str | None = None,
    ) -> tuple[list[LLMMessage], bool]:
        if not config.repo_map_root or not messages:
            return messages, False

        repo_map_svc = self._resolve_repomap_service()

        eff_query = query_context
        if not eff_query:
            for m in reversed(messages):
                if m.role == "user":
                    eff_query = m.content
                    break

        map_res = repo_map_svc.get_repo_map(
            config.repo_map_root,
            query_context=eff_query,
            max_tokens=config.repo_map_budget_tokens,
        )

        if map_res.status != "ok" or not map_res.formatted_map or map_res.formatted_map.startswith("No indexed"):
            return messages, False

        new_msgs = list(messages)
        first = new_msgs[0]
        if first.role == "system":
            enhanced_sys = (
                f"{first.content}\n\n"
                f"### Repository Map:\n"
                f"```\n{map_res.formatted_map}\n```"
            )
            new_msgs[0] = LLMMessage(role="system", content=enhanced_sys)
            return new_msgs, True

        return messages, False


class CompositeContextStrategy:
    """Sequentially applies a chain of registered ContextPruningStrategy instances."""

    def __init__(self, strategies: list[ContextPruningStrategy] | None = None) -> None:
        self._strategies: list[ContextPruningStrategy] = list(strategies or [])

    @property
    def name(self) -> str:
        return "composite_context_strategy"

    def add_strategy(self, strategy: ContextPruningStrategy) -> None:
        self._strategies.append(strategy)

    def prune_pipeline(
        self,
        messages: list[LLMMessage],
        *,
        config: ContextOptimizationConfig,
    ) -> tuple[list[LLMMessage], list[PruningMetric]]:
        current_messages = list(messages)
        metrics: list[PruningMetric] = []

        for strat in self._strategies:
            current_messages, metric = strat.prune(current_messages, config=config)
            if metric is not None:
                metrics.append(metric)

        return current_messages, metrics


# =============================================================================
# Default Context Optimizer Service Implementation
# =============================================================================

class DefaultContextOptimizerService:
    """Authoritative micro-kernel service uniting observation compaction, strategies, and RepoMap."""

    def __init__(
        self,
        config: ContextOptimizationConfig | None = None,
        context: ServiceContext | None = None,
        compactor: ObservationCompactorStrategy | None = None,
        strategies: list[ContextPruningStrategy] | None = None,
    ) -> None:
        self.config = config or ContextOptimizationConfig()
        self.context: ServiceContext = context if context is not None else ServiceContext()
        self.compactor: ObservationCompactorStrategy = compactor or MiddleOutObservationCompactor()
        self.repo_map_strategy = RepoMapInjectionStrategy(context=self.context)

        # Default strategy chain
        initial_strategies = strategies if strategies is not None else [SlidingWindowPruner()]
        self.composite_pipeline = CompositeContextStrategy(initial_strategies)

    def register_strategy(self, strategy: ContextPruningStrategy) -> None:
        """Register an additional pruning strategy into the pipeline."""
        self.composite_pipeline.add_strategy(strategy)

    def compact_observation(
        self,
        action_name: str,
        observation: Any,
        *,
        max_chars: int | None = None,
    ) -> str:
        eff_max = max_chars or self.config.max_observation_chars
        return self.compactor.compact(
            action_name,
            observation,
            max_chars=eff_max,
            compact_json=self.config.compact_json,
        )

    def optimize_messages(
        self,
        messages: list[LLMMessage],
        *,
        config: ContextOptimizationConfig | None = None,
    ) -> list[LLMMessage]:
        cfg = config or self.config
        if not cfg.enable_pruning or len(messages) <= cfg.max_total_messages:
            return list(messages)

        # Delegate to UNIFIED_CONTEXT_PIPELINE_KEY if present in IoC context
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

        # Built-in strategy pipeline execution
        pruned_msgs, _ = self.composite_pipeline.prune_pipeline(messages, config=cfg)
        return pruned_msgs

    def optimize_context(
        self,
        messages: list[LLMMessage],
        *,
        config: ContextOptimizationConfig | None = None,
        query_context: str | None = None,
    ) -> ContextOptimizationResult:
        cfg = config or self.config
        original_count = len(messages)

        try:
            # Step 1: Pruning pipeline
            pruned_msgs, metrics = self.composite_pipeline.prune_pipeline(messages, config=cfg)

            # Step 2: RepoMap injection
            enhanced_msgs, repo_map_injected = self.repo_map_strategy.inject(
                pruned_msgs,
                config=cfg,
                query_context=query_context,
            )

            est_tokens = estimate_tokens(enhanced_msgs)

            return ContextOptimizationResult(
                status="ok",
                messages=tuple(enhanced_msgs),
                original_count=original_count,
                optimized_count=len(enhanced_msgs),
                estimated_tokens=est_tokens,
                repo_map_injected=repo_map_injected,
                metrics=tuple(metrics),
            )
        except Exception as err:
            logger.error("context_optimization_failed", error=str(err))
            return ContextOptimizationResult(
                status="error",
                messages=tuple(messages),
                original_count=original_count,
                optimized_count=original_count,
                estimated_tokens=estimate_tokens(messages),
                error=str(err),
            )

    def inject_repo_map(
        self,
        messages: list[LLMMessage],
        *,
        query_context: str | None = None,
        config: ContextOptimizationConfig | None = None,
    ) -> list[LLMMessage]:
        cfg = config or self.config
        enhanced_msgs, _ = self.repo_map_strategy.inject(
            messages,
            config=cfg,
            query_context=query_context,
        )
        return enhanced_msgs


# =============================================================================
# Single-Seam Resolution Factory (Rule 58)
# =============================================================================

def resolve_context_optimizer(
    ctx: ServiceContext | None = None,
    config: ContextOptimizationConfig | None = None,
) -> ContextOptimizerService:
    """Resolve ContextOptimizerService from IoC container with fallback to DefaultContextOptimizerService."""
    if ctx is not None:
        try:
            svc = ctx.optional(CONTEXT_OPTIMIZER_SERVICE_KEY)
            if svc is not None:
                return svc
            legacy_svc = ctx.optional(AGENT_CONTEXT_OPTIMIZER_KEY)
            if legacy_svc is not None:
                return legacy_svc
        except Exception as err:
            logger.debug("Failed resolving context optimizer from context: %s", err)

    return DefaultContextOptimizerService(config=config, context=ctx)


__all__ = [
    "AGENT_CONTEXT_OPTIMIZER_KEY",
    "CONTEXT_OPTIMIZER_SERVICE_KEY",
    "CompositeContextStrategy",
    "ContextOptimizationConfig",
    "ContextOptimizationResult",
    "ContextOptimizerService",
    "ContextPruningStrategy",
    "DefaultContextOptimizerService",
    "MiddleOutObservationCompactor",
    "ObservationCompactorStrategy",
    "PruningMetric",
    "RepoMapInjectionStrategy",
    "SlidingWindowPruner",
    "estimate_tokens",
    "resolve_context_optimizer",
]
