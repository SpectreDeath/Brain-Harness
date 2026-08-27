# 🧠 Skill Summary Card: `memory_decay_engine`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        memory_decay_engine                       │
│ Category:    memory_and_epistemics                     │
│ Archetype:   service_provider / tool_provider          │
│ Isolation:   subprocess                                │
│ Status:      Verified & Sandboxed                      │
├────────────────────────────────────────────────────────┤
│ Target:      Ebbinghaus Decay & Reinforcement Engine   │
└────────────────────────────────────────────────────────┘
```

## Tools
- `memory_register(session_id, mem_id, content, current_turn, is_foundational, baseline_stability, eviction_threshold)`: Registers new item.
- `memory_recall(session_id, mem_id, current_turn)`: Spaced-repetition reinforcement.
- `memory_step(session_id, current_turn)`: Turn advance & exponential decay eviction.
- `memory_query_working_set(session_id, current_turn)`: Query active working set.
- `simulate_session_benchmark(session_length, num_foundational, noise_per_turn, seed)`: Decay vs sliding window benchmark.
