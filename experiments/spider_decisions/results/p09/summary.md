# Phase 9 — Brain Harness Dependency-Safe Refactor Order

Analyzed **11** subpackages in `src/harness` (`50` `depends_on_project` edges).

## Detected Cycles
- **Spider `validate_model` cycles (1):** `services -> kernel -> services`
- **Full Tarjan strongly connected components (`size > 1`):** `[['agent', 'bridges', 'creator', 'events', 'ingestion', 'kernel', 'plugins', 'services']]`
- **Note on blast radius:** `ontology_spider` `transitive` queries traverse forward `depends_on_project` edges; reverse reachability (**blast radius** = transitive dependents) was computed via reverse BFS in Python.

## Proposed Refactor Order

| Order | Unit | Py Files | Cycle? | Hub In-Deg | Blast Radius | Out-Deg | In `hotspots` KI? | In `deepening` KI? |
|---:|---|---:|---|---:|---:|---:|---|---|
| 1 | `services` | 59 | Yes (size 2) | 8 | 10 | 2 | True | True |
| 2 | `kernel` | 37 | Yes (size 2) | 10 | 10 | 6 | False | False |
| 3 | `commands` | 59 | No | 0 | 0 | 10 | True | True |
| 4 | `ui` | 15 | No | 1 | 1 | 7 | False | False |
| 5 | `mcp` | 11 | No | 1 | 1 | 4 | True | False |
| 6 | `agent` | 41 | No | 3 | 10 | 5 | True | True |
| 7 | `bridges` | 6 | No | 2 | 10 | 3 | False | False |
| 8 | `creator` | 39 | No | 4 | 10 | 4 | False | True |
| 9 | `plugins` | 18 | No | 9 | 10 | 4 | True | False |
| 10 | `ingestion` | 16 | No | 5 | 10 | 4 | False | False |
| 11 | `events` | 11 | No | 7 | 10 | 1 | False | False |

## Cross-Check Against Historical KIs (Top-10)

| Unit | Order | `ki-file-size-hotspots` | `ki-deepening-cycle-history` | Matched Signals |
|---|---:|---|---|---|
| `services` | 1 | True | True | compute_assessor.py, tools.py, validator.py, services/compute/ |
| `commands` | 3 | True | True | cli.py, reflection.py, commands/ |
| `mcp` | 5 | True | False | server.py |
| `agent` | 6 | True | True | archetypes.py, swarm.py, session.py, agent session |
| `creator` | 8 | False | True | creator package |
| `plugins` | 9 | True | False | cellcog.py |
