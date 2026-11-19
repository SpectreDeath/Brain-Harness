# Phase 9 — Brain Harness Dependency-Safe Refactor Order

Analyzed **12** subpackages in `src/harness` (`58` `depends_on_project` edges).

## Detected Cycles
- **Spider `validate_model` cycles (1):** `services -> creator -> services`
- **Full Tarjan strongly connected components (`size > 1`):** `[['creator', 'events', 'ingestion', 'kernel', 'plugins', 'services']]`
- **Note on blast radius:** `ontology_spider` `transitive` queries traverse forward `depends_on_project` edges; reverse reachability (**blast radius** = transitive dependents) was computed via reverse BFS in Python.

## Proposed Refactor Order

| Order | Unit | Py Files | Cycle? | Hub In-Deg | Blast Radius | Out-Deg | In `hotspots` KI? | In `deepening` KI? |
|---:|---|---:|---|---:|---:|---:|---|---|
| 1 | `services` | 421 | Yes (size 2) | 8 | 11 | 5 | True | True |
| 2 | `creator` | 39 | Yes (size 2) | 5 | 11 | 4 | False | True |
| 3 | `commands` | 106 | No | 0 | 0 | 11 | True | True |
| 4 | `ui` | 15 | No | 1 | 1 | 8 | False | False |
| 5 | `mcp` | 11 | No | 1 | 1 | 4 | True | False |
| 6 | `runtime` | 11 | No | 2 | 2 | 7 | False | False |
| 7 | `agent` | 41 | No | 3 | 3 | 5 | True | True |
| 8 | `bridges` | 6 | No | 2 | 3 | 3 | False | False |
| 9 | `ingestion` | 16 | No | 6 | 11 | 4 | False | False |
| 10 | `plugins` | 23 | No | 10 | 11 | 4 | True | False |
| 11 | `kernel` | 26 | No | 11 | 11 | 2 | False | False |
| 12 | `events` | 11 | No | 9 | 11 | 1 | False | False |

## Cross-Check Against Historical KIs (Top-10)

| Unit | Order | `ki-file-size-hotspots` | `ki-deepening-cycle-history` | Matched Signals |
|---|---:|---|---|---|
| `services` | 1 | True | True | compute_assessor.py, tools.py, validator.py, services/compute/ |
| `creator` | 2 | False | True | creator package |
| `commands` | 3 | True | True | cli.py, reflection.py, commands/ |
| `mcp` | 5 | True | False | server.py |
| `agent` | 7 | True | True | archetypes.py, swarm.py, session.py, agent session |
| `plugins` | 10 | True | False | cellcog.py |
