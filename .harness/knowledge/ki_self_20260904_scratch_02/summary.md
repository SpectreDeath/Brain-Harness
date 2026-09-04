# Swarm Execution Composite Thread Keying & Session Manager Interface Contracts

**ID:** `ki_self_20260904_scratch_02`  
**Category:** `agent_orchestration`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `scratch/inspect_session_mgr.py`, `src/harness/agent/swarm.py`, `tests/test_agent_graph_store.py`, `AGENTS.md#Rule36`

## Executive Summary
When orchestrating multi-agent swarms with `SwarmCoordinator` and recording wave executions into `AgentExecutionGraphService` or `AgentSessionManager`, wave node execution threads are identified by a composite key `child_sid = f"{actual_run_id}_{node_id}"`. Looking up a thread using only the bare `node_id` returns `None`. Furthermore, `AgentSessionManager` public methods follow strict positional and keyword contracts that differ from generic ReAct loop terms.

## Architectural Invariants & Rules
1. **Composite Thread Keying:** Querying swarm execution threads in `AgentExecutionGraphService.export_graph().nodes` must use `f"{run_id}_{node_id}"` (e.g. `swarm_84ec411e_scan`).
2. **`create_session` Contract:** First positional argument is `task: str` (`create_session(task: str, *, session_id=..., metadata=..., parent_session_id=..., node_id=..., role=...)`). Never pass `agent_name` or `goal`.
3. **`complete_session` Contract:** Requires `final_answer: str` (`complete_session(session_id: str, final_answer: str, *, total_tokens: int = 0)`). Never pass `summary`.
4. **`fail_session` Contract:** Requires `error_message: str` (`fail_session(session_id: str, error_message: str)`). Never pass `error`.
5. Codified in `AGENTS.md` Rule 36.
