## Micro-Kernel IoC Topo-Sort & Domain-Partitioned Plugin Synthesis

### Discovery
Brain Harness achieves extreme modularity by decoupling all domain capabilities into 105 separate plugins partitioned across 11 category subdirectories (`agent_orchestration`, `memory_and_epistemics`, `security_and_forensics`, `software_engineering`, `integration_and_io`, `data_engineering`, etc.). 

The micro-kernel provides zero hardcoded functionality. The `LifecycleManager` sorts plugins into a directed acyclic graph (DAG) by evaluating their declared `provides` and `requires` typed `ServiceKey[T]` collections.

### Architectural Invariant
1. **Everything is a Plugin (Rule 1)**: Core functionality is registered into `ServiceContext` via `context.provide(key, instance)` and resolved via `context.require(key)`.
2. **Topological Ordering (Rule 3)**: Plugins must declare explicit dependency keys. Dependency resolution runs via Kahn's topological sort algorithm before enabling plugins.
3. **Domain Partitioning (Rule 18)**: Multi-capability bridges or monorepo ingestions must never bundle disparate tools into a single monolithic plugin. Partition across co-located category directories.
4. **Singleton Provider Invariant (Rule 45)**: Every plugin module entrypoint must subclass `HarnessPlugin`, declare typed keys in `provides`, and export an instantiated module-level `plugin` singleton.

### Source References
- `src/harness/kernel/lifecycle.py`
- `src/harness/kernel/context.py`
- `src/harness/plugins/loader.py`
- `AGENTS.md#L3-L7`
- `AGENTS.md#L20`

### Rule Reference
Governed by AGENTS.md Rules 1, 3, 18, and 45.
