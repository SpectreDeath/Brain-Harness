# Deterministic 3-Pass Prompt Pruning with Fixed-Point Idempotence

## Epistemic Seam (Mental Models & Heuristics)
1. **Compiler Optimization Analogy**: Prompt optimization should be structured as deterministic compiler optimization passes rather than heuristic LLM summarization. Each pass performs an order-independent transformation with a provable fixed point.
2. **Pass Order Invariant**:
   - **Pass 1 (Expired Tool Elimination)**: Keep only the latest output for any resource key (`resource_key` / `tool_call_id`). Earlier intermediate read outputs are discarded.
   - **Pass 2 (Duplicate Context Elimination)**: Normalized casing and whitespace hashing collapse duplicate retrieved chunks to the canonical first occurrence.
   - **Pass 3 (Dependency Restoration)**: Any discarded message that defines a token (`DEFINE:<key>`) required by a surviving message (`REF:<key>`) is automatically restored into the message sequence.
3. **Fixed-Point Idempotence**: `prune(prune(messages)) == prune(messages)`. Re-running optimization never alters the token stream once the fixed point is reached.

## Procedural Seam (Integration Architecture)
1. **ContextPruningStrategy Protocol**: `DeterministicPromptPruner` implements `ContextPruningStrategy` and integrates seamlessly into `CompositeContextStrategy` pipelines.
2. **Non-Invasive Strategy Injection (Rule 19)**: In `PromptPruningPlugin.on_load()`, the plugin resolves `CONTEXT_OPTIMIZER_SERVICE_KEY` and registers itself via `optimizer.register_strategy()`, leaving engine constructor contracts untouched.
