---
name: ebbinghaus-memory-governor
description: Govern conversational agent working memory retention using Ebbinghaus forgetting curves, channel decay multipliers, and non-linear recall stability reinforcement. Do not use for permanent database storage or ungrounded cache purges.
---

# Ebbinghaus Memory Governor

The Ebbinghaus Memory Governor provides mathematical forgetting curve retention management for agent memory items. By modeling stability growth upon repeated recall, foundational rules remain protected while ephemeral scratch notes decay predictably.

## Operational Workflow

1. **Register Observation**: Track agent observations, instructions, and tool outputs with initial stability and channel weighting.
2. **Reinforce on Recall**: When a stored memory is referenced in dialogue or context assembly, reinforce its stability non-linearly ($S_{\text{new}} = S_{\text{old}} \times (1 + \alpha \ln(1 + n))$).
3. **Turn-Based Decay Evaluation**: At each dialogue step, evaluate exponential decay $R(t) = e^{-\Delta t / S}$.
4. **Cognitive Eviction Advisory**: Candidate memories scoring below the retention threshold are evicted from the active working set.

## Anti-Patterns

- **Recency-Only Purging** — Evicting frequently recalled foundational facts simply because they were not touched in the most recent turn.
- **Unbounded Memory Accumulation** — Allowing unbounded observation nodes to fill working memory without exponential decay thresholds.
- **Wall-Clock Decay Coupling** — Relying on real-time wall clocks instead of logical conversation turn steps for deterministic reproducibility.

## Diagnostic Verification

Verify decay calculations and retention scores using the micro-kernel service `harness.services.memory_decay` or the CLI plugin tools `memory_step` and `rank_working_set`.
