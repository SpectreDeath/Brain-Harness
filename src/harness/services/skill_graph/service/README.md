# Skill Registry Service Implementation

The `harness.services.skill_graph.service` package provides the authoritative in-memory skill registry service, graph query execution, cluster grouping, and IoC resolution seams.

---

## Architectural Invariants

- **Typed IoC Provision (`Rule 2`)**: Exposes `SKILL_REGISTRY_SERVICE_KEY` and registers `BuiltinSkillRegistryService` into the micro-kernel.
- **Single-Seam Resolution (`Rule 49`, `Rule 58`)**: Callers resolve through `resolve_skill_registry(context)`.

---

## Module Reference

| Module | Core Classes / Symbols | Description |
|---|---|---|
| [`registry.py`](registry.py) | `BuiltinSkillRegistryService` | Core registry maintaining the indexed skill graph and execution chain pathfinder. |
| [`resolvers.py`](resolvers.py) | `resolve_skill_registry` | IoC container single-seam resolver returning the configured registry instance. |
| [`graph.py`](graph.py) | `SkillGraphEngine` | Graph query and topological sort executor. |
| [`clustering.py`](clustering.py) | `cluster_skills_by_domain` | Semantic domain clustering partitioning skills into operational categories. |
| [`gating.py`](gating.py) | `evaluate_skill_gate` | Runtime tool approval and activation gate evaluator. |
| [`scanner_ops.py`](scanner_ops.py) | `execute_catalog_scan` | Async filesystem catalog scanner loading metadata models. |

