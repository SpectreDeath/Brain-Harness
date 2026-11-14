---
name: agora-mcp-workbench-architect
description: Architect, audit, and orchestrate Agora Workbench MCP servers, loopback sidecars, unified state graphs, gateway/dispatcher connectors, and policy-enforced data lakes. Do not use for static frontend CSS styling or non-MCP desktop GUI automation.
---

# Agora MCP Workbench Architect

`agora-mcp-workbench-architect` distills the co-located sidecar lifecycle manager, unified cross-server `StateGraph`, `GatewayServer`/`DispatcherServer` connector proxies, and `PolicyEnforcedCatalogProvider` + v2 streaming object transfer patterns from `microsoft/agora-workbench` (`a8ae030b`).

See [CARD.md](CARD.md) for the companion summary card, pipeline stages, and mandatory invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline operational budgets and limit defaults.

---

## 1. Co-Located Sidecar Lifecycle & Kernel Isolation

Share heavy global models across isolated execution kernels without duplicating memory or relaxing loopback containment:

1. **Enforce Socket & Env Locks (`audit_sidecar_config`)**: Validate unique sidecar names, positive ports, `/`-prefixed health endpoints, loopback binding (`localhost`, `127.0.0.1`, `::1`), and detect caller `SIDECAR_HOST`/`SIDECAR_PORT` env override attempts.
2. **Isolate Lifecycle & Shutdown Escalation**: Launch sidecars in dedicated process groups sharing the kernel environment Python (`use_env_python=True`), roll back partial startup sets on failure, and escalate `SIGTERM` to `SIGKILL` after `10.0s`.

> **Completion criterion**: `SidecarAuditReport` returns `valid=True` with loopback binding confirmed and `SIDECAR_HOST`/`SIDECAR_PORT` locked.

---

## 2. Unified State Graph & Connector Network Topologies

Discover cross-server workflows and proxy MCP calls behind policy gates and load-balanced worker pools:

1. **Plan Cross-Server Workflows (`plan_state_graph_workflow`)**: Validate `BridgeEdge(from_state, to_state)` links against upstream tool produced/required state vocabularies, find shortest BFS transition paths, and detect cross-upstream duplicate skill collisions.
2. **Enforce Gateway & Dispatcher Routing (`evaluate_connector_call`)**: Cascade `parallel_execute` blocks in `GatewayServer` to suppress `poll_batch`, `collect_batch`, and `cancel_batch` companion proxies, enforce 60s rate limits, and route `DispatcherServer` pools across `round_robin`, `least_loaded`, and `sticky_session` with `"reroute"` or `"error"` failure handling.

> **Completion criterion**: `StateGraphPlanResult` verifies reachability/bridges and `ConnectorRoutingDecision` resolves deterministic allow/deny/worker selection.

---

## 3. Data Lake Policy Governance & Streaming Object Transfer

Prevent unauthorized data enumeration, cursor scope escape, and memory exhaustion during cross-kernel transfer:

1. **Bind Policy Mode & Cursor Scope (`validate_datalake_and_transfer`)**: Enforce exact `per_artifact` vs `homogeneous_source` enforcer parity, intersect permitted `source_ids` before pagination, invalidate reused cursors on scope shift, and mask unauthorized artifact lookups as not-found.
2. **Enforce Bounded v2 Streaming Envelopes**: Restrict payloads to `256 MB`, v2 metadata envelopes to `64 KB`, correlation IDs to `128` safe chars, and reject duplicate JSON keys across envelope boundaries.

> **Completion criterion**: `DataLakeTransferReport` validates policy parity, cursor scope, and bounded streaming invariants.

---

## The Three Foundational Pillars

### 1. Shared Heavy-Resource Sidecars with Hard Control Locks
Keep heavy runtime dependencies in loopback-bound helper daemons sharing the kernel Python environment while locking `SIDECAR_HOST`/`SIDECAR_PORT` against caller env overrides.

### 2. Explicit State Contracts & Stateless Proxy Separation
Model cross-server capabilities through explicit state tokens, validated synthetic bridge edges, policy-enforcing gateways, and affinity-preserving dispatchers decoupled from execution kernels.

### 3. Pre-Pagination Authorization & Bounded Streaming I/O
Evaluate source/artifact authorization before pagination, invalidate stale cursors on capability shifts, mask forbidden reads as absent, and stream objects under strict byte and duplicate-key bounds.

---

## Anti-Patterns

- **Caller Env Redirects on Internal Sidecars** — Allowing `spec.env` overrides to alter `SIDECAR_HOST` or `SIDECAR_PORT` detaches the daemon from the health-polled socket and breaks readiness checks.
- **Silent Upstream Skill Shadowing** — Letting duplicate skill names across RouterServer upstreams resolve arbitrarily instead of returning explicit upstream disambiguation choices causes unpredictable execution.
- **Orphaned Batch Control Proxies** — Blocking `parallel_execute` in `GatewayServer` while continuing to advertise `poll_batch`, `collect_batch`, or `cancel_batch` leaks non-functional tools to agents.
- **Post-Pagination Auth & Permission Side-Channels** — Filtering data-lake results after issuing cursors, reusing cursors after source scope drops, or raising distinct permission errors on `get`/`resolve` leaks existence oracle signals.
