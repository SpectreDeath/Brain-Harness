"""Main entrypoint and plugin registration for Prompt Pruning Layer."""

from __future__ import annotations

import sys
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.context_optimizer import (
    CONTEXT_OPTIMIZER_SERVICE_KEY,
    DeterministicPromptPruner,
)
from plugins.memory_and_epistemics.prompt_pruning_layer.tools import (
    benchmark_pruning_workloads,
    build_prompt,
    estimate_prompt_reduction,
    generate_benchmark_corpus,
    prune_messages,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = structlog.get_logger("harness.plugins.prompt_pruning_layer")


class PromptPruningService:
    """Service provider for deterministic prompt pruning."""

    def prune(self, messages: list[dict[str, Any]], assemble_prompt: bool = True) -> dict[str, Any]:
        return prune_messages(messages, assemble_prompt=assemble_prompt)

    def build(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        return build_prompt(messages)

    def estimate(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        return estimate_prompt_reduction(messages)

    def benchmark(self, num_turns: int = 150, seed: int = 42) -> dict[str, Any]:
        return benchmark_pruning_workloads(num_turns=num_turns, seed=seed)


PROMPT_PRUNING_SERVICE_KEY = ServiceKey[PromptPruningService]("domain.prompt_pruning_layer")


class PromptPruningPlugin(HarnessPlugin):
    """Harness Plugin for compiler-style 3-pass prompt pruning (Rules 1, 3, 19, 45)."""

    name = "domain.prompt_pruning_layer"
    version = "1.2.0"
    description = "Deterministic 3-pass compiler prompt pruner with provable fixed-point idempotence"
    trusted = True

    def __init__(self, service: PromptPruningService | None = None) -> None:
        self._service = service or PromptPruningService()
        self._strategy = DeterministicPromptPruner()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [PROMPT_PRUNING_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(PROMPT_PRUNING_SERVICE_KEY, self._service, provider=self.name)

        # Non-invasive strategy injection into ContextOptimizerService (Rule 19)
        optimizer = ctx.optional(CONTEXT_OPTIMIZER_SERVICE_KEY)
        if optimizer is not None and hasattr(optimizer, "register_strategy"):
            optimizer.register_strategy(self._strategy)
            logger.info("DeterministicPromptPruner registered into ContextOptimizerService", plugin=self.name)

    async def on_enable(self) -> None:
        logger.info("PromptPruningPlugin enabled", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("PromptPruningPlugin disabled", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("PromptPruningPlugin unloaded", plugin=self.name)


# Authoritative module singleton export (Rule 45)
plugin = PromptPruningPlugin()

__all__ = [
    "PROMPT_PRUNING_SERVICE_KEY",
    "PromptPruningService",
    "PromptPruningPlugin",
    "plugin",
    "prune_messages",
    "build_prompt",
    "estimate_prompt_reduction",
    "generate_benchmark_corpus",
    "benchmark_pruning_workloads",
]
