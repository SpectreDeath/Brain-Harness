# Phase 9 — Checkpoint 9.5 Architectural Review

- **Verdict:** Sensible (`8.5 / 10`), approved by user (`"yes"`).

## Key Structural Caveats

1. **`ui -> commands -> ui` cycle (`size 2`) is a single-file seam violation:** `commands` legitimately imports `ui` to start the server, while `src/harness/ui/server/routes/skills.py` reaches sideways into `harness.commands` instead of `harness.services`. Refactoring `#1 commands` and `#2 ui` first breaks this cycle cleanly and leaves `#3 mcp` (`in_degree = 1`) as a true peripheral leaf.
2. **All 11 subpackages share `Blast Radius = 10` (11-unit Tarjan SCC) due to `kernel/runtime/`:** Pure kernel primitives (`context/core.py`, `lifecycle/transitions.py`) only touch `events` and `plugins`, whereas `src/harness/kernel/runtime/` (`defaults.py`, `factory.py`, `services.py`, `tools.py`, `plugins.py`) acts as the application composition root inside `kernel/` and imports `agent`, `bridges`, `ingestion`, `plugins`, and `services`.
3. **Upward leaks inside `services/` missed by the 60-file snapshot cap:** Full AST scan surfaced `src/harness/services/skill_graph/joint_query.py` (`services -> commands`) and `src/harness/services/storage/vault_retrieval.py` (`services -> creator`).
