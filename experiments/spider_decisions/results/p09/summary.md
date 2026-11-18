# Phase 9 — Brain Harness Dependency-Safe Refactor Order

Analyzed **11** subpackages in `src/harness` (`52` `depends_on_project` edges).

## Detected Cycles
- **Spider `validate_model` cycles (1):** `ui -> commands -> ui`
- **Full Tarjan strongly connected components (`size > 1`):** `[['agent', 'bridges', 'commands', 'creator', 'events', 'ingestion', 'kernel', 'mcp', 'plugins', 'services', 'ui']]`
- **Note on blast radius:** `ontology_spider` `transitive` queries traverse forward `depends_on_project` edges; reverse reachability (**blast radius** = transitive dependents) was computed via reverse BFS in Python.

## Proposed Refactor Order

| Order | Unit | Py Files | Cycle? | Hub In-Deg | Blast Radius | Out-Deg | In `hotspots` KI? | In `deepening` KI? |
|---:|---|---:|---|---:|---:|---:|---|---|
| 1 | `commands` | 59 | Yes (size 2) | 2 | 10 | 10 | True | True |
| 2 | `ui` | 15 | Yes (size 2) | 1 | 10 | 8 | False | False |
| 3 | `mcp` | 11 | No | 1 | 10 | 4 | True | False |
| 4 | `agent` | 41 | No | 3 | 10 | 5 | True | True |
| 5 | `creator` | 39 | No | 4 | 10 | 5 | False | True |
| 6 | `bridges` | 6 | No | 2 | 10 | 3 | False | False |
| 7 | `services` | 59 | No | 8 | 10 | 2 | True | True |
| 8 | `plugins` | 18 | No | 9 | 10 | 4 | True | False |
| 9 | `ingestion` | 16 | No | 5 | 10 | 4 | False | False |
| 10 | `kernel` | 37 | No | 10 | 10 | 6 | False | False |
| 11 | `events` | 11 | No | 7 | 10 | 1 | False | False |

## Cross-Check Against Historical KIs (Top-10)

| Unit | Order | `ki-file-size-hotspots` | `ki-deepening-cycle-history` | Matched Signals |
|---|---:|---|---|---|
| `commands` | 1 | True | True | cli.py, reflection.py, commands/ |
| `mcp` | 3 | True | False | server.py |
| `agent` | 4 | True | True | archetypes.py, swarm.py, session.py, agent session |
| `creator` | 5 | False | True | creator package |
| `services` | 7 | True | True | compute_assessor.py, tools.py, validator.py, services/compute/ |
| `plugins` | 8 | True | False | cellcog.py |

## Checkpoint 9.5 Architectural Review Verdict

- **Verdict:** Sensible (`8.5 / 10`), approved by user (`"yes"`).
- **Caveat 1 (`ui -> commands -> ui` seam):** `src/harness/ui/server/routes/skills.py` imports `harness.commands` instead of `harness.services`; decoupling `#1 commands` and `#2 ui` breaks the explicit cycle immediately and leaves `#3 mcp` (`in_degree = 1`) as a peripheral leaf.
- **Caveat 2 (`kernel/runtime/` composition root & 11-unit SCC):** Every unit has `blast_radius = 10` because `src/harness/kernel/runtime/` (`defaults.py`, `factory.py`, `services.py`, `tools.py`, `plugins.py`) acts as the application composition root inside `kernel/`, importing `agent`, `bridges`, `ingestion`, `plugins`, and `services`.
- **Caveat 3 (`services/` upward leaks beyond 60-file snapshot cap):** Full AST inspection found `src/harness/services/skill_graph/joint_query.py` (`services -> commands`) and `src/harness/services/storage/vault_retrieval.py` (`services -> creator`).
