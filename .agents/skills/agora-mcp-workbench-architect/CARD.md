```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: agora-mcp-workbench-architect                                 │
│ Category: agent_orchestration / mcp_workbench                        │
│ Version: 1.0.0                                                       │
│ Invocation: /agora-mcp-workbench-architect                           │
│ Triggers: "agora-workbench", "SidecarManager", "StateGraph",         │
│           "GatewayServer", "DispatcherServer", "object_transfer"     │
│ Requires: "agent-harness-architect"                                  │
│ Target: MCP sidecars, state graphs, connector proxies & data lakes   │
└──────────────────────────────────────────────────────────────────────┘
```

# Agora MCP Workbench Architect — Companion Summary Card

## Pipeline Stages

| Stage | Operation | Output Model |
| --- | --- | --- |
| **1. Sidecar Audit** | `audit_sidecar_config()` | `SidecarAuditReport` (`valid`, `locked_host`, `locked_port`) |
| **2. State Graph Plan** | `plan_state_graph_workflow()` | `StateGraphPlanResult` (`reachable`, `steps`, `bridges_used`) |
| **3. Connector Eval** | `evaluate_connector_call()` | `ConnectorRoutingDecision` (`allowed`, `selected_worker`) |
| **4. Transfer Guard** | `validate_datalake_and_transfer()` | `DataLakeTransferReport` (`valid`, `cursor_rejected`, `envelope_valid`) |

---

## Mandatory Invariants Checklist

- [ ] **Loopback & Env Lock**: Sidecar health bind locks `SIDECAR_HOST` and `SIDECAR_PORT` last and rejects non-loopback hosts.
- [ ] **Bridge Validation**: Every synthetic cross-server `BridgeEdge` connects an existing produced state to a required state.
- [ ] **Gateway Cascade & Dispatcher Lock**: Blocking `parallel_execute` suppresses companion proxies and respects `worker_failure_policy`.
- [ ] **Cursor Scope & Bounded Stream**: Pagination cursors fail if authorized `source_ids` shrink and transfers cap at `256 MB` / `64 KB` headers without duplicate keys.
- [ ] **Slotted & Frozen Models**: All report and decision structures use `slots=True, frozen=True` (Rule 12).
