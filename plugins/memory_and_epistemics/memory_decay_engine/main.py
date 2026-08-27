"""Main entrypoint and typed tool registrations for Ebbinghaus Memory Decay Engine plugin."""

from __future__ import annotations

from typing import Any

import structlog

from harness.kernel.context import ServiceKey
from plugins.memory_and_epistemics.memory_decay_engine.decay_core import (
    DecaySessionStore,
    EbbinghausMemoryEngine,
    SessionConfig,
    run_simulation,
)

logger = structlog.get_logger()

# Global authoritative session store
_STORE = DecaySessionStore()


def memory_register(
    key: str,
    content: str,
    session_id: str = "default",
    stability: float = 5.0,
    is_foundational: bool = False,
    channel: str = "memory",
) -> dict[str, Any]:
    """Register a new memory item into the Ebbinghaus memory session.

    Args:
        key: Unique identifier for the memory item.
        content: Text content or representation of the memory.
        session_id: Session namespace (default: 'default').
        stability: Initial stability parameter in turns (default: 5.0).
        is_foundational: If True, item is immune to decay eviction.
        channel: Channel profile ('instruction', 'foundational', 'memory', 'evidence', 'tool_output').

    Returns:
        Structured item dictionary with initial retention and stability metrics.
    """
    try:
        engine = _STORE.get_or_create(session_id)
        item = engine.register(
            key=key,
            content=content,
            stability=stability,
            is_foundational=is_foundational,
            channel=channel,
        )
        return {
            "status": "ok",
            "session_id": session_id,
            "item": item.to_dict(engine.current_turn),
        }
    except Exception as e:
        logger.error("memory_register_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def memory_recall(key: str, session_id: str = "default") -> dict[str, Any]:
    """Recall a memory item, reinforcing its stability and resetting its elapsed decay clock.

    Args:
        key: Memory key to recall.
        session_id: Session namespace.

    Returns:
        Recalled item dictionary with reinforced stability, or not_found/evicted status.
    """
    try:
        engine = _STORE.get_or_create(session_id)
        item = engine.recall(key)
        if item is None:
            return {
                "status": "not_found",
                "key": key,
                "session_id": session_id,
                "message": "Item does not exist or has been evicted due to decay",
            }
        return {
            "status": "ok",
            "session_id": session_id,
            "item": item.to_dict(engine.current_turn),
        }
    except Exception as e:
        logger.error("memory_recall_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def memory_step(session_id: str = "default") -> dict[str, Any]:
    """Advance session time by one turn, applying decay and evicting items below retention threshold.

    Args:
        session_id: Session namespace.

    Returns:
        Turn transition summary, evicted keys list, and active working set count.
    """
    try:
        engine = _STORE.get_or_create(session_id)
        evicted = engine.step_turn()
        return {
            "status": "ok",
            "session_id": session_id,
            "current_turn": engine.current_turn,
            "evicted_count": len(evicted),
            "evicted_keys": evicted,
            "active_working_set_count": len(engine.working_set()),
        }
    except Exception as e:
        logger.error("memory_step_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def memory_query_working_set(
    session_id: str = "default",
    include_evicted: bool = False,
) -> dict[str, Any]:
    """Query all active items currently residing in the working memory set.

    Args:
        session_id: Session namespace.
        include_evicted: Whether to include evicted items.

    Returns:
        List of memory items with retention and recall statistics.
    """
    try:
        engine = _STORE.get_or_create(session_id)
        items = list(engine.items.values()) if include_evicted else engine.working_set()
        return {
            "status": "ok",
            "session_id": session_id,
            "current_turn": engine.current_turn,
            "total_items": len(items),
            "items": [item.to_dict(engine.current_turn) for item in items],
        }
    except Exception as e:
        logger.error("query_working_set_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def rank_working_set(
    session_id: str = "default",
    w_retention: float = 0.5,
    w_stability: float = 0.3,
    w_foundational: float = 0.2,
    limit: int | None = None,
) -> dict[str, Any]:
    """Query working memory set sorted by multi-criteria composite score."""
    try:
        engine = _STORE.get_or_create(session_id)
        ranked = engine.query_ranked_working_set(
            w_retention=w_retention,
            w_stability=w_stability,
            w_foundational=w_foundational,
            limit=limit,
        )
        return {
            "status": "ok",
            "session_id": session_id,
            "current_turn": engine.current_turn,
            "ranked_count": len(ranked),
            "items": ranked,
        }
    except Exception as e:
        logger.error("rank_working_set_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def export_memory_session(session_id: str = "default") -> dict[str, Any]:
    """Export snapshot serialization of an active memory session."""
    try:
        snapshot = _STORE.export_session(session_id)
        if not snapshot:
            return {"status": "error", "error": f"Session {session_id} not found"}
        return {"status": "ok", "snapshot": snapshot}
    except Exception as e:
        logger.error("export_session_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def import_memory_session(session_id: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    """Import snapshot serialization to restore a memory session."""
    try:
        engine = _STORE.import_session(session_id, snapshot)
        return {
            "status": "ok",
            "session_id": session_id,
            "current_turn": engine.current_turn,
            "total_items": len(engine.items),
            "working_set_count": len(engine.working_set()),
        }
    except Exception as e:
        logger.error("import_session_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def simulate_session_benchmark(
    num_turns: int = 100,
    total_memories: int = 30,
    recall_probability: float = 0.35,
    seed: int = 42,
) -> dict[str, Any]:
    """Run comparative simulation between Ebbinghaus memory decay and a fixed-window recency baseline.

    Args:
        num_turns: Number of interaction turns to simulate.
        total_memories: Total memory items registered over the session.
        recall_probability: Per-turn probability of memory access.
        seed: Random seed for deterministic simulation.

    Returns:
        Comparison metrics including missed recalls, working set size, and foundational memory loss.
    """
    try:
        cfg = SessionConfig(
            num_turns=num_turns,
            total_memories=total_memories,
            recall_probability=recall_probability,
            seed=seed,
        )
        res = run_simulation(cfg)
        return {
            "status": "ok",
            "simulation": res,
        }
    except Exception as e:
        logger.error("simulation_benchmark_failed", error=str(e))
        return {"status": "error", "error": str(e)}


class MemoryDecayService:
    """Service provider for Ebbinghaus Memory Decay and Retention Management."""

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
