"""Default context optimizer service implementation unifying compaction, strategies, and RepoMap."""

from __future__ import annotations

import sys
from typing import Any

import structlog

from harness.kernel.context import ServiceContext
from harness.services.llm import LLMMessage
from harness.services.unified_context import (
    UNIFIED_CONTEXT_PIPELINE_KEY,
    UnifiedContextRequest,
)
from harness.services.context_optimizer.compactor import MiddleOutObservationCompactor
from harness.services.context_optimizer.models import (
    ContextOptimizationConfig,
    ContextOptimizationResult,
    estimate_tokens,
)
from harness.services.context_optimizer.protocols import (
    ContextOptimizerService,
    ContextPruningStrategy,
    ObservationCompactorStrategy,
)
from harness.services.context_optimizer.strategies import (
    CompositeContextStrategy,
    RepoMapInjectionStrategy,
    SlidingWindowPruner,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = structlog.get_logger("harness.services.context_optimizer")


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


__all__ = [
    "DefaultContextOptimizerService",
]
