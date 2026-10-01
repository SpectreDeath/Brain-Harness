# Brain Harness Reference Catalog

The reference documentation provides factual, comprehensive technical specifications for all components of the Brain Harness micro-kernel and runtime ecosystem.

---

## Reference Pages

| Reference Document | Scope & Contents |
|---|---|
| [Micro-Kernel Reference](kernel.md) | `ServiceContext`, `ServiceKey[T]`, `DependencyGraph`, `PluginLifecycleManager`, and `StateReconciler`. |
| [Agent Reasoning Reference](agent.md) | `ReActAgentLoop`, `StepExecutionEngine`, `SwarmCoordinator`, and `DefaultContextOptimizer`. |
| [Ingestion Pipeline Reference](ingestion.md) | `UniversalSourceRegistry`, `RepoFetcher`, `RepoInspector`, and `RepoConverter`. |
| [Core Services Catalog](services.md) | Complete directory of 70+ authoritative typed `ServiceKey[T]` tokens and protocol interfaces. |
| [Click CLI Command Reference](cli.md) | Comprehensive command specification for all 41 command groups, subcommands, and flags. |
| [Plugin Manifest Reference](plugin-manifest.md) | Schema specification for `plugin.json`, dependency declarations, lifecycle states, and sandboxing. |

---

## Invariant Compliance Checklist

All reference entities in this section conform to core repository standards:
- Slotted & Frozen Dataclasses (Rule 12): Internal models declare `slots=True` and `frozen=True`.
- Typed Service Resolution (Rule 2): All micro-kernel dependencies resolve through `ServiceKey[T]`.
- Zero-Synthetic Path Routing (Rule 55): Graph algorithms return explicit empty paths rather than fabricated shortcuts.
- Single-Source Click Consolidation (Rule 6): Command groups are declared once in `src/harness/cli.py`.
