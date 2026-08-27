"""Core Ebbinghaus Memory Decay Engine: Retention Math, Channel Profiles, DecaySessionStore, and Baselines."""

from __future__ import annotations

import math
import random
import threading
from dataclasses import dataclass, field
from typing import Any

# Default channel decay multipliers (lower multiplier = slower decay / longer retention)
DEFAULT_CHANNEL_MULTIPLIERS: dict[str, float] = {
    "instruction": 0.25,   # System instructions decay very slowly
    "foundational": 0.35,  # Foundational domain facts
    "memory": 1.0,         # Standard conversation memory
    "evidence": 0.70,      # RAG / retrieved evidence
    "tool_output": 1.75,   # Volatile / ephemeral tool outputs
}


@dataclass
class MemoryItem:
    key: str
    content: str
    created_turn: int
    last_recalled_turn: int
    recall_count: int = 0
    stability: float = 5.0
    half_life: float = 5.0
    evicted: bool = False
    channel: str = "memory"
    is_foundational: bool = False

    def retention(self, current_turn: int, decay_multiplier: float = 1.0) -> float:
        """Compute current retention score using Ebbinghaus exponential decay."""
        elapsed = max(0, current_turn - self.last_recalled_turn)
        effective_stability = max(0.01, self.stability / decay_multiplier)
        return math.exp(-elapsed / effective_stability)

    def to_dict(self, current_turn: int | None = None, decay_multiplier: float = 1.0) -> dict[str, Any]:
        ret = self.retention(current_turn, decay_multiplier=decay_multiplier) if current_turn is not None else 1.0
        return {
            "key": self.key,
            "content": self.content,
            "created_turn": self.created_turn,
            "last_recalled_turn": self.last_recalled_turn,
            "recall_count": self.recall_count,
            "stability": round(self.stability, 2),
            "half_life": round(self.half_life, 2),
            "retention": round(ret, 4),
            "evicted": self.evicted,
            "channel": self.channel,
            "is_foundational": self.is_foundational,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> MemoryItem:
        return cls(
            key=d["key"],
            content=d["content"],
            created_turn=int(d["created_turn"]),
            last_recalled_turn=int(d["last_recalled_turn"]),
            recall_count=int(d.get("recall_count", 0)),
            stability=float(d.get("stability", 5.0)),
            half_life=float(d.get("half_life", 5.0)),
            evicted=bool(d.get("evicted", False)),
            channel=d.get("channel", "memory"),
            is_foundational=bool(d.get("is_foundational", False)),
        )


class EbbinghausMemoryEngine:
    """Core memory engine tracking item retention, stability reinforcement, and eviction."""

    def __init__(
        self,
        eviction_threshold: float = 0.20,
        base_stability: float = 5.0,
        reinforce_power: float = 1.0,
        channel_multipliers: dict[str, float] | None = None,
    ):
        self.eviction_threshold = eviction_threshold
        self.base_stability = base_stability
        self.reinforce_power = reinforce_power
        self.channel_multipliers = dict(channel_multipliers or DEFAULT_CHANNEL_MULTIPLIERS)
        self.items: dict[str, MemoryItem] = {}
        self.current_turn = 0

    def _get_multiplier(self, channel: str) -> float:
        return self.channel_multipliers.get(channel, 1.0)

    def register(
        self,
        key: str,
        content: str,
        stability: float | None = None,
        channel: str = "memory",
        is_foundational: bool = False,
    ) -> MemoryItem:
        stab = stability if stability is not None else self.base_stability
        item = MemoryItem(
            key=key,
            content=content,
            created_turn=self.current_turn,
            last_recalled_turn=self.current_turn,
            recall_count=0,
            stability=stab,
            half_life=stab * math.log(2),
            evicted=False,
            channel=channel,
            is_foundational=is_foundational,
        )
        self.items[key] = item
        return item

    def recall(self, key: str) -> MemoryItem | None:
        if key not in self.items:
            return None
        item = self.items[key]
        if item.evicted:
            return None

        # Stability reinforcement: S_new = S_old * (1 + ln(1 + n))
        item.recall_count += 1
        reinforcement_factor = 1.0 + math.log(1.0 + item.recall_count)
        item.stability = item.stability * reinforcement_factor
        item.half_life = item.stability * math.log(2)
        item.last_recalled_turn = self.current_turn
        return item

    def step_turn(self) -> list[str]:
        """Advance time by one turn and evict items falling below the retention threshold."""
        self.current_turn += 1
        evicted_keys = []
        for item in self.items.values():
            if item.evicted or item.is_foundational:
                continue
            mult = self._get_multiplier(item.channel)
            ret = item.retention(self.current_turn, decay_multiplier=mult)
            if ret < self.eviction_threshold:
                item.evicted = True
                evicted_keys.append(item.key)
        return evicted_keys

    def working_set(self) -> list[MemoryItem]:
        return [item for item in self.items.values() if not item.evicted]

    def query_ranked_working_set(
        self,
        w_retention: float = 0.5,
        w_stability: float = 0.3,
        w_foundational: float = 0.2,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Query working set sorted by composite multi-criteria importance score."""
        active = self.working_set()
        scored: list[tuple[float, MemoryItem, float]] = []

        for item in active:
            mult = self._get_multiplier(item.channel)
            ret = item.retention(self.current_turn, decay_multiplier=mult)
            norm_stab = min(1.0, item.stability / 50.0)
            found_bonus = 1.0 if item.is_foundational else 0.0

            score = (w_retention * ret) + (w_stability * norm_stab) + (w_foundational * found_bonus)
            scored.append((score, item, ret))

        scored.sort(key=lambda triple: -triple[0])
        if limit is not None:
            scored = scored[:limit]

        results = []
        for score, item, ret in scored:
            d = item.to_dict(self.current_turn, decay_multiplier=self._get_multiplier(item.channel))
            d["composite_score"] = round(score, 4)
            results.append(d)
        return results

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_turn": self.current_turn,
            "eviction_threshold": self.eviction_threshold,
            "base_stability": self.base_stability,
            "channel_multipliers": dict(self.channel_multipliers),
            "items": {k: item.to_dict(self.current_turn, decay_multiplier=self._get_multiplier(item.channel)) for k, item in self.items.items()},
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> EbbinghausMemoryEngine:
        engine = cls(
            eviction_threshold=d.get("eviction_threshold", 0.20),
            base_stability=d.get("base_stability", 5.0),
            channel_multipliers=d.get("channel_multipliers"),
        )
        engine.current_turn = d.get("current_turn", 0)
        items_dict = d.get("items", {})
        for k, v in items_dict.items():
            engine.items[k] = MemoryItem.from_dict(v)
        return engine


class DecaySessionStore:
    """Thread-safe authoritative store managing active and archived memory sessions."""

    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: dict[str, EbbinghausMemoryEngine] = {}

    def get_or_create(self, session_id: str, eviction_threshold: float = 0.20, base_stability: float = 5.0) -> EbbinghausMemoryEngine:
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = EbbinghausMemoryEngine(
                    eviction_threshold=eviction_threshold,
                    base_stability=base_stability,
                )
            return self._sessions[session_id]

    def export_session(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            engine = self._sessions.get(session_id)
            if not engine:
                return None
            return {
                "session_id": session_id,
                "engine": engine.to_dict(),
            }

    def import_session(self, session_id: str, data: dict[str, Any]) -> EbbinghausMemoryEngine:
        engine_dict = data.get("engine", data)
        engine = EbbinghausMemoryEngine.from_dict(engine_dict)
        with self._lock:
            self._sessions[session_id] = engine
        return engine

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()


class RecencyOnlyBaseline:
    """Fixed-window sliding capacity baseline for benchmark comparison."""

    def __init__(self, capacity: int = 10):
        self.capacity = capacity
        self.items: dict[str, tuple[str, int]] = {}  # key -> (content, last_access)
        self.current_turn = 0

    def register(self, key: str, content: str) -> None:
        self.items[key] = (content, self.current_turn)
        self._enforce_capacity()

    def recall(self, key: str) -> bool:
        if key in self.items:
            content, _ = self.items[key]
            self.items[key] = (content, self.current_turn)
            return True
        return False

    def step_turn(self) -> None:
        self.current_turn += 1

    def _enforce_capacity(self) -> None:
        if len(self.items) > self.capacity:
            sorted_items = sorted(self.items.items(), key=lambda kv: kv[1][1])
            excess = len(self.items) - self.capacity
            for i in range(excess):
                del self.items[sorted_items[i][0]]

    def working_set_keys(self) -> set[str]:
        return set(self.items.keys())


@dataclass
class SessionConfig:
    num_turns: int = 100
    total_memories: int = 30
    foundational_keys: list[str] = field(default_factory=list)
    recall_probability: float = 0.35
    seed: int = 42


def generate_session(config: SessionConfig) -> list[tuple[str, str, Any]]:
    rng = random.Random(config.seed)
    events: list[tuple[str, str, Any]] = []

    all_keys = [f"mem_{i}" for i in range(config.total_memories)]
    foundational_set = set(config.foundational_keys or all_keys[:5])

    for k in all_keys:
        is_found = k in foundational_set
        events.append(("register", k, {"is_foundational": is_found, "content": f"Fact about {k}"}))

    registered_so_far = []
    for turn in range(1, config.num_turns + 1):
        if all_keys and len(registered_so_far) < len(all_keys):
            next_k = all_keys[len(registered_so_far)]
            registered_so_far.append(next_k)

        if registered_so_far and rng.random() < config.recall_probability:
            if rng.random() < 0.60 and foundational_set:
                target_k = rng.choice(list(foundational_set))
            else:
                target_k = rng.choice(registered_so_far)
            events.append(("recall", target_k, {}))

        events.append(("step", f"turn_{turn}", {}))

    return events


def run_simulation(config: SessionConfig) -> dict[str, Any]:
    events = generate_session(config)

    ebbinghaus = EbbinghausMemoryEngine(eviction_threshold=0.20, base_stability=5.0)
    recency = RecencyOnlyBaseline(capacity=12)

    ebbinghaus_recalls_missed = 0
    recency_recalls_missed = 0
    foundational_evictions_ebbinghaus = 0
    foundational_evictions_recency = 0
    foundational_set = set(config.foundational_keys or [f"mem_{i}" for i in range(5)])

    for op, key, meta in events:
        if op == "register":
            ebbinghaus.register(key, meta["content"], is_foundational=meta.get("is_foundational", False))
            recency.register(key, meta["content"])
        elif op == "recall":
            eb_res = ebbinghaus.recall(key)
            if eb_res is None:
                ebbinghaus_recalls_missed += 1

            rec_ok = recency.recall(key)
            if not rec_ok:
                recency_recalls_missed += 1
        elif op == "step":
            evicted = ebbinghaus.step_turn()
            for ek in evicted:
                if ek in foundational_set:
                    foundational_evictions_ebbinghaus += 1
            recency.step_turn()

    rec_working = recency.working_set_keys()
    for fk in foundational_set:
        if fk not in rec_working:
            foundational_evictions_recency += 1

    return {
        "num_turns": config.num_turns,
        "total_memories": config.total_memories,
        "ebbinghaus_engine": {
            "working_set_count": len(ebbinghaus.working_set()),
            "missed_recalls": ebbinghaus_recalls_missed,
            "foundational_lost": foundational_evictions_ebbinghaus,
        },
        "recency_baseline": {
            "working_set_count": len(recency.working_set_keys()),
            "missed_recalls": recency_recalls_missed,
            "foundational_lost": foundational_evictions_recency,
        },
    }
