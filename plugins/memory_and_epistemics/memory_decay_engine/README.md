# domain.memory_decay_engine (v1.1.0)

Ebbinghaus forgetting curve memory engine with channel multipliers, snapshot session persistence, and composite ranking

---

## Overview & Metadata

- **Plugin Directory**: `plugins/memory_and_epistemics/memory_decay_engine`
- **Isolation Mode**: `subprocess`
- **Services Provided**: None
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `memory_register` | `(key, content, session_id, stability, is_foundational, channel)` | Register a new memory item with retention tracking, channel multiplier, and foundational protection |
| `memory_recall` | `(key, session_id)` | Recall a memory item, reinforcing stability and resetting its elapsed decay clock |
| `memory_step` | `(session_id)` | Advance session time by one turn, applying decay and evicting items below retention threshold |
| `memory_query_working_set` | `(session_id, include_evicted)` | Query all active items currently residing in the working memory set |
| `rank_working_set` | `(session_id, w_retention, w_stability, w_foundational, limit)` | Query working memory set sorted by multi-criteria composite score |
| `export_memory_session` | `(session_id)` | Export snapshot serialization of an active memory session |
| `import_memory_session` | `(session_id, snapshot)` | Import snapshot serialization to restore a memory session |
| `simulate_session_benchmark` | `(num_turns, total_memories, recall_probability, seed)` | Run comparative simulation between Ebbinghaus memory decay and a fixed-window recency baseline |

---

## Key Modules & AST Symbols

### Module [`decay_core.py`](decay_core.py)

Core Ebbinghaus Memory Decay Engine: Retention Math, Channel Profiles, DecaySessionStore, and Baselines.

#### Classes

- `class MemoryItem`
  - `def retention(current_turn, decay_multiplier) -> float`
  - `def to_dict(current_turn, decay_multiplier) -> dict[str, Any]`
  - `def from_dict(cls, d) -> MemoryItem`
- `class EbbinghausMemoryEngine`
  Core memory engine tracking item retention, stability reinforcement, and eviction.
  - `def __init__(eviction_threshold, base_stability, reinforce_power, channel_multipliers)`
  - `def register(key, content, stability, channel, is_foundational) -> MemoryItem`
  - `def recall(key) -> MemoryItem | None`
  - `def step_turn() -> list[str]`
  - `def working_set() -> list[MemoryItem]`
  - `def query_ranked_working_set(w_retention, w_stability, w_foundational, limit) -> list[dict[str, Any]]`
  - `def to_dict() -> dict[str, Any]`
  - `def from_dict(cls, d) -> EbbinghausMemoryEngine`
- `class DecaySessionStore`
  Thread-safe authoritative store managing active and archived memory sessions.
  - `def __init__()`
  - `def get_or_create(session_id, eviction_threshold, base_stability) -> EbbinghausMemoryEngine`
  - `def export_session(session_id) -> dict[str, Any] | None`
  - `def import_session(session_id, data) -> EbbinghausMemoryEngine`
  - `def clear() -> None`
- `class RecencyOnlyBaseline`
  Fixed-window sliding capacity baseline for benchmark comparison.
  - `def __init__(capacity)`
  - `def register(key, content) -> None`
  - `def recall(key) -> bool`
  - `def step_turn() -> None`
  - `def working_set_keys() -> set[str]`
- `class SessionConfig`


#### Functions

- `def generate_session(config) -> list[tuple[str, str, Any]]`
- `def run_simulation(config) -> dict[str, Any]`


### Module [`main.py`](main.py)

Main entrypoint and typed tool registrations for Ebbinghaus Memory Decay Engine plugin.

#### Classes

- `class MemoryDecayService`
  Service provider for Ebbinghaus Memory Decay and Retention Management.
  - `def register(key, content, session_id, stability, is_foundational, channel) -> dict[str, Any]`
  - `def recall(key, session_id) -> dict[str, Any]`
  - `def step(session_id) -> dict[str, Any]`
  - `def query(session_id, include_evicted) -> dict[str, Any]`
  - `def rank(session_id, w_retention, w_stability, w_foundational, limit) -> dict[str, Any]`
  - `def export_session(session_id) -> dict[str, Any]`
  - `def import_session(session_id, snapshot) -> dict[str, Any]`
  - `def simulate(num_turns, total_memories, recall_probability, seed) -> dict[str, Any]`


#### Functions

- `def memory_register(key, content, session_id, stability, is_foundational, channel) -> dict[str, Any]`
  - Register a new memory item into the Ebbinghaus memory session.
- `def memory_recall(key, session_id) -> dict[str, Any]`
  - Recall a memory item, reinforcing its stability and resetting its elapsed decay clock.
- `def memory_step(session_id) -> dict[str, Any]`
  - Advance session time by one turn, applying decay and evicting items below retention threshold.
- `def memory_query_working_set(session_id, include_evicted) -> dict[str, Any]`
  - Query all active items currently residing in the working memory set.
- `def rank_working_set(session_id, w_retention, w_stability, w_foundational, limit) -> dict[str, Any]`
  - Query working memory set sorted by multi-criteria composite score.
- `def export_memory_session(session_id) -> dict[str, Any]`
  - Export snapshot serialization of an active memory session.
- `def import_memory_session(session_id, snapshot) -> dict[str, Any]`
  - Import snapshot serialization to restore a memory session.
- `def simulate_session_benchmark(num_turns, total_memories, recall_probability, seed) -> dict[str, Any]`
  - Run comparative simulation between Ebbinghaus memory decay and a fixed-window recency baseline.



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
