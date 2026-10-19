"""Main entrypoint and plugin registration for Ebbinghaus Memory Decay Engine."""

from __future__ import annotations

import sys
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.memory_decay import (
    MEMORY_DECAY_SERVICE_KEY as MICRO_KEY,
    DefaultMemoryDecayService,
    MemoryDecayService as MicroService,
)
from plugins.memory_and_epistemics.memory_decay_engine.tools import (
    export_memory_session,
    import_memory_session,
    memory_query_working_set,
    memory_recall,
    memory_register,
    memory_step,
    rank_working_set,
    simulate_session_benchmark,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = structlog.get_logger("harness.plugins.memory_decay_engine")


class MemoryDecayService:
    """Service facade for backward compatibility and domain calls."""

    def __init__(self, micro_service: MicroService | None = None) -> None:
        self._micro_service = micro_service or DefaultMemoryDecayService()

    def register(
        self,
        key: str,
        content: str,
        session_id: str = "default",
        stability: float = 5.0,
        is_foundational: bool = False,
        channel: str = "memory",
    ) -> dict[str, Any]:
        return memory_register(
            key=key,
            content=content,
            session_id=session_id,
            stability=stability,
            is_foundational=is_foundational,
            channel=channel,
        )

    def recall(self, key: str, session_id: str = "default") -> dict[str, Any]:
        return memory_recall(key=key, session_id=session_id)

    def step(self, session_id: str = "default") -> dict[str, Any]:
        return memory_step(session_id=session_id)

    def query(self, session_id: str = "default", include_evicted: bool = False) -> dict[str, Any]:
        return memory_query_working_set(session_id=session_id, include_evicted=include_evicted)

    def rank(
        self,
        session_id: str = "default",
        w_retention: float = 0.5,
        w_stability: float = 0.3,
        w_foundational: float = 0.2,
        limit: int | None = None,
    ) -> dict[str, Any]:
        return rank_working_set(
            session_id=session_id,
            w_retention=w_retention,
            w_stability=w_stability,
            w_foundational=w_foundational,
            limit=limit,
        )

    def export_session(self, session_id: str = "default") -> dict[str, Any]:
        return export_memory_session(session_id=session_id)

    def import_session(self, session_id: str, snapshot: dict[str, Any]) -> dict[str, Any]:
        return import_memory_session(session_id=session_id, snapshot=snapshot)

    def simulate(
        self,
        num_turns: int = 100,
        total_memories: int = 30,
        recall_probability: float = 0.35,
        seed: int = 42,
    ) -> dict[str, Any]:
        return simulate_session_benchmark(
            num_turns=num_turns,
            total_memories=total_memories,
            recall_probability=recall_probability,
            seed=seed,
        )


MEMORY_DECAY_SERVICE_KEY = ServiceKey[MemoryDecayService]("domain.memory_decay_engine")


class MemoryDecayPlugin(HarnessPlugin):
    """Harness Plugin for cognitive Ebbinghaus memory decay (Rules 1, 3, 45)."""

    name = "domain.memory_decay_engine"
    version = "1.2.0"
    description = "Ebbinghaus memory decay with non-linear recall reinforcement and cognitive eviction"
    trusted = True

    def __init__(self, service: MemoryDecayService | None = None) -> None:
        self._service = service or MemoryDecayService()
        self._micro_service = DefaultMemoryDecayService()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [MEMORY_DECAY_SERVICE_KEY, MICRO_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(MEMORY_DECAY_SERVICE_KEY, self._service, provider=self.name)
        ctx.provide(MICRO_KEY, self._micro_service, provider=self.name)
        logger.info("MemoryDecayService registered into IoC context", plugin=self.name)

    async def on_enable(self) -> None:
        logger.info("MemoryDecayPlugin enabled", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("MemoryDecayPlugin disabled", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("MemoryDecayPlugin unloaded", plugin=self.name)


# Authoritative module singleton export (Rule 45)
plugin = MemoryDecayPlugin()

__all__ = [
    "MEMORY_DECAY_SERVICE_KEY",
    "MemoryDecayService",
    "MemoryDecayPlugin",
    "plugin",
    "memory_register",
    "memory_recall",
    "memory_step",
    "memory_query_working_set",
    "rank_working_set",
    "export_memory_session",
    "import_memory_session",
    "simulate_session_benchmark",
]
