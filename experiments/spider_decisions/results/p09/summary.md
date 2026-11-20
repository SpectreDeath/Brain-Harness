# Phase 9 — Brain Harness Dependency-Safe Refactor Order

Analyzed **12** subpackages in `src/harness` (`57` `depends_on_project` edges).

## Detected Cycles
- **Spider `validate_model` cycles (1):** `services -> plugins -> services`
- **Full Tarjan strongly connected components (`size > 1`):** `[['creator', 'events', 'ingestion', 'kernel', 'plugins', 'services']]`
- **Note on blast radius:** `ontology_spider` `transitive` queries traverse forward `depends_on_project` edges; reverse reachability (**blast radius** = transitive dependents) was computed via reverse BFS in Python.

## Known Architectural Limitations
- 2026-11-19: Eliminated the services -> creator -> services edge by moving ReflectionDaemonWorker to src/harness/creator/reflection/worker.py and removing ALLOWED_SERVICES_TO_CREATOR (`depends_on_project` edges 58 -> 57). Because Spider `validate_model` emits one witness cycle per acyclic rule, breaking services -> creator exposed the pre-existing `services -> plugins -> services` 2-cycle inside the 6-unit core Tarjan SCC (`['creator', 'events', 'ingestion', 'kernel', 'plugins', 'services']`), alongside `kernel <-> events`, `kernel <-> plugins`, `creator <-> ingestion`, and `plugins <-> ingestion`.

## Proposed Refactor Order

| Order | Unit | Py Files | Cycle? | Hub In-Deg | Blast Radius | Out-Deg | In `hotspots` KI? | In `deepening` KI? |
|---:|---|---:|---|---:|---:|---:|---|---|
| 1 | `services` | 421 | Yes (size 2) | 8 | 11 | 4 | True | True |
| 2 | `plugins` | 23 | Yes (size 2) | 10 | 11 | 4 | True | False |
| 3 | `commands` | 106 | No | 0 | 0 | 11 | True | True |
| 4 | `ui` | 15 | No | 1 | 1 | 8 | False | False |
| 5 | `mcp` | 11 | No | 1 | 1 | 4 | True | False |
| 6 | `runtime` | 11 | No | 2 | 2 | 7 | False | False |
| 7 | `agent` | 41 | No | 3 | 3 | 5 | True | True |
| 8 | `bridges` | 6 | No | 2 | 3 | 3 | False | False |
| 9 | `creator` | 40 | No | 4 | 11 | 4 | False | True |
| 10 | `ingestion` | 16 | No | 6 | 11 | 4 | False | False |
| 11 | `kernel` | 27 | No | 11 | 11 | 2 | False | False |
| 12 | `events` | 11 | No | 9 | 11 | 1 | False | False |

## Cross-Check Against Historical KIs (Top-10)

| Unit | Order | `ki-file-size-hotspots` | `ki-deepening-cycle-history` | Matched Signals |
|---|---:|---|---|---|
| `services` | 1 | True | True | compute_assessor.py, tools.py, validator.py, services/compute/ |
| `plugins` | 2 | True | False | cellcog.py |
| `commands` | 3 | True | True | cli.py, reflection.py, commands/ |
| `mcp` | 5 | True | False | server.py |
| `agent` | 7 | True | True | archetypes.py, swarm.py, session.py, agent session |
| `creator` | 9 | False | True | creator package |

## Track 3.1 — Next-Cycle Scope Options (2026-11-20)

- **Live Model Confirmation (`validate_model` on `brain_harness_src.json`):** Confirmed witness cycle **`services -> plugins -> services`** (assertions `asrt_b0697c4a9fb0` and `asrt_d0e3e7b051e4`) inside the intact 6-unit Tarjan SCC (`['creator', 'events', 'ingestion', 'kernel', 'plugins', 'services']`), alongside `kernel <-> events`, `kernel <-> plugins`, `creator <-> ingestion`, and `plugins <-> ingestion`.
- **Live AST Seam Counts (`src/harness`):**
  - `plugins -> services` (`2` imports): `src/harness/plugins/sandboxed.py:198` (`ToolSpec`) and `src/harness/plugins/tool_mount.py:31` (`TOOL_REGISTRY_KEY`, `ToolRegistry`, `ToolSpec`) importing from `harness.services.tools`.
  - `services -> plugins` (`7` imports across `6` files): `services/compute/service.py:12`, `services/data_management/plugin.py:11-12`, `services/llm.py:18`, `services/skill_graph/plugin.py:10`, `services/storage/plugin.py:11`, and `services/tools/plugin.py:16` importing from `harness.plugins.{base,manifest}`.
- **Scope Options (Awaiting User Pick under Track 3.2):**
  1. **Fix next (dedicated follow-up plan):** Extract `ToolSpec` / `TOOL_REGISTRY_KEY` contracts out of `services.tools` to break the `plugins -> services` edge (`2` imports, low-to-moderate refactor cost), reducing `depends_on_project` edges `57 -> 56`. *Caveat:* the 6-unit Tarjan SCC remains intact and `validate_model` will immediately report the next witness cycle inside the SCC (`kernel <-> events`, `kernel <-> plugins`, `creator <-> ingestion`, or `plugins <-> ingestion`).
  2. **Accept the 6-unit core SCC:** Zero code churn; formally document the 6 micro-kernel core packages (`creator`, `events`, `ingestion`, `kernel`, `plugins`, `services`) as a co-dependent core layer while keeping all 6 outer packages (`commands`, `ui`, `mcp`, `runtime`, `agent`, `bridges`) acyclic.
  3. **Defer with a named trigger:** Retain current layer boundary tests (`services` never imports `commands`/`creator`; `kernel` only imports `events`/`plugins`) and defer breaking `services <-> plugins` until a named architectural trigger (e.g., extracting `harness-core` or splitting `ToolRegistry`).
