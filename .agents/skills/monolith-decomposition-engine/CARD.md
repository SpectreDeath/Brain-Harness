```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: monolith-decomposition-engine                                 │
│ Category: developer_tooling / architecture                           │
│ Version: 1.0.0                                                       │
│ Invocation: /monolith-decomposition-engine                           │
│ Triggers: "monolith decomposition", "factor module", "slotted model",│
│           "single-seam resolver", "click consolidation"              │
│ Requires: "deep-skill-forge", "python-dataclass-architect"           │
│ Target: Decompose hotspots into slotted, single-seam subpackages <=200L│
└──────────────────────────────────────────────────────────────────────┘
```

# Monolith Decomposition Engine — Companion Summary Card

## Decomposition Recipes Table

| Archetype | Seam Boundary | Key Modules Created | Invariants Enforced |
|---|---|---|---|
| **Click CLI Commands** | Command dispatch & args | `group.py`, `<cmd>.py`, `converters.py` | Rule 6 (single-source), Rule 11 ($\le 200$L) |
| **Micro-Kernel Services** | IoC protocol & engines | `models.py`, `protocol.py`, `resolvers.py` | Rule 12 (slotted), Rule 58 (resolver) |
| **Harness Plugins** | Lifecycle & sandbox | `engine/`, `main.py`, `resolvers.py` | Rule 5 (sandbox), Rule 45 (singleton) |

---

## Mandatory Invariants Checklist

- [ ] **Strict Line Count Cap**: Every factored submodule must strictly remain $\le 200$ lines (Rule 11).
- [ ] **Slotted & Frozen Dataclasses**: High-volume models must use `slots=True, frozen=True` with `__post_init__` assertions (Rule 12 & 43).
- [ ] **Single-Seam Resolver**: Provide unified `resolve_<domain>()` with IoC resolution and local fallback (Rule 58).
- [ ] **Click Single-Source Consolidation**: Co-locate Click command registrations in a single block (Rule 6).
- [ ] **Plugin Singleton Export**: Export instantiated module-level `plugin` in plugin entrypoints (Rule 45).
- [ ] **Backward-Compatible Facade**: Re-export all public symbols with `__all__` in `__init__.py`.
