# Agora Workbench: Connector Gateway Policies & Dispatcher Routing

## Overview
- **Source Repository**: `https://github.com/microsoft/agora-workbench` (`a8ae030b`)
- **Primary Files**:
  - `src/agora_workbench/connector/models.py#L30-L49,L141-L160`
  - `src/agora_workbench/connector/gateway.py#L53-L160`
  - `src/agora_workbench/connector/dispatcher.py#L48-L120,L215-L342`

## Core Architecture & Invariants
1. **Cascading Proxy Suppression (`GatewayServer._setup_tools`)**: Blocking `parallel_execute` automatically suppresses its companion proxy tools (`poll`, `collect_batch`, `cancel`) so dead control tools are never advertised to agents.
2. **Defense-in-Depth Call Filtering & Sliding Window Rate Limit**: Prior to upstream dispatch, `execute_code_gateway` rejects code referencing any entry in `blocked_tools`, requires presence of an entry from `allowed_tools` when non-empty, and evaluates per-user timestamps over a 60.0-second window.
3. **Locked Worker Pool Selection (`DispatcherServer._select_worker`)**: Acquires `_routing_lock` to inspect `session_affinity_map`; healthy sticky workers handle subsequent calls without re-balancing. When an affine worker becomes unhealthy, `worker_failure_policy == "error"` fails closed while `"reroute"` clears affinity and falls back to `weighted round_robin` or `least_loaded`.
4. **Composite Session Keys (`_dispatcher_sessions`)**: Upstream sessions are keyed by `(connector_session_id, worker_name)` to prevent cross-tenant or cross-worker session collisions during reroutes.

## Decision Heuristics & Anti-Patterns
- **Never leave orphan batch control tools exposed when batch execution is blocked**.
- **Never share upstream session tokens across different workers without `(session, worker)` scoping**.
