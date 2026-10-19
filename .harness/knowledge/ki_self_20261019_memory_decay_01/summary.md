# Ebbinghaus Forgetting Curves & Cognitive Working Memory Retention

## Epistemic Seam (Mental Models & Heuristics)
1. **Turn-Based Logical Clocks**: Real-time wall clocks introduce non-deterministic race conditions across distributed agent workers. Memory decay must strictly depend on logical conversation turn steps ($t_{\text{turn}}$) to guarantee 100% reproducible eviction decisions.
2. **Non-Linear Stability Reinforcement**: Each recall reinforcement provides diminishing returns ($S_{\text{new}} = S_{\text{old}} \times (1 + \alpha \ln(1 + n))$). This mirrors cognitive spaced repetition: frequently verified facts resist decay, while ephemeral scratch outputs decay rapidly.
3. **Foundational Immunity**: System instructions, safety rules, and foundational context must carry permanent immunity flags (`is_foundational=True`) or large baseline stabilities ($S \ge 100$) to prevent catastrophic context drift.

## Procedural Seam (Integration Architecture)
1. **Slotted Dataclasses**: High-volume node structures (`MemoryNode`, `DecayConfig`, `EvictionDecision`) are declared with `slots=True, frozen=True` to eliminate dictionary overhead and prevent accidental in-flight mutations.
2. **Micro-Kernel Protocol**: Service operations are defined in `@runtime_checkable Protocol MemoryDecayService` with typed key `ServiceKey[MemoryDecayService]("service.memory_decay")`.
3. **Plugin Staging**: `MemoryDecayPlugin` provides typed keys during `on_load(context)` and co-locates `config.default.yaml` for zero-fork configuration.
