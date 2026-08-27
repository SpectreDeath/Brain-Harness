# 🧠 Skill Summary Card: `prompt_pruning_layer`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        prompt_pruning_layer                      │
│ Category:    memory_and_epistemics                     │
│ Archetype:   tool_provider / service_provider          │
│ Isolation:   subprocess                                │
│ Status:      Verified & Sandboxed                      │
├────────────────────────────────────────────────────────┤
│ Target:      Deterministic 3-Pass Prompt Optimizer     │
└────────────────────────────────────────────────────────┘
```

## Tools
- `prune_messages(messages, assemble_prompt=True)`: Runs the 3 deterministic optimization passes.
- `build_prompt(messages)`: Formats messages into an ordered prompt.
- `estimate_prompt_reduction(messages)`: Token reduction diagnostics.
- `generate_benchmark_corpus(num_turns, workload, seed)`: Synthetic multi-turn dialogue generator.
- `benchmark_pruning_workloads(num_turns, seed)`: Workload comparative evaluation suite.
