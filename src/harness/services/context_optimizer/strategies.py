"""Composable context pruning and AST RepoMap injection strategies (Rule 9)."""

from __future__ import annotations

import sys
import time
from typing import Any

from harness.kernel.context import ServiceContext
from harness.services.llm import LLMMessage
from harness.services.repomap import (
    REPO_MAP_SERVICE_KEY,
    DefaultRepoMapService,
    RepoMapService,
)
from harness.services.context_optimizer.models import (
    ContextOptimizationConfig,
    PruningMetric,
    estimate_tokens,
)
from harness.services.context_optimizer.protocols import ContextPruningStrategy

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


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


__all__ = [
    "CompositeContextStrategy",
    "RepoMapInjectionStrategy",
    "SlidingWindowPruner",
]
