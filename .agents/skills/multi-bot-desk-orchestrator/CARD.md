```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: multi-bot-desk-orchestrator                                   │
│ Category: agent_orchestration / multi-bot                            │
│ Version: 1.0.0                                                       │
│ Invocation: /multi-bot-desk-orchestrator                             │
│ Triggers: "multi bot desk", "hop depth", "mcp approval",             │
│           "bot desktop lease", "serial bot queue"                    │
│ Requires: "agent-harness-architect"                                  │
│ Target: Hop-depth guards, in-band MCP approvals & desk leases        │
└──────────────────────────────────────────────────────────────────────┘
```

# Multi-Bot Desk Orchestrator — Companion Summary Card

## Pipeline Stages

| Stage | Operation | Output Model |
| --- | --- | --- |
| **1. Hop-Depth Guard** | `evaluate_bot_hop_dispatch()` | `BotHopDispatchOutcome` (`allowed`, `next_depth`, `target_bot_ids`) |
| **2. MCP Approval Gate** | `evaluate_mcp_tool_approval()` | `McpApprovalOutcome` (`auto_allow` \| `require_approval` \| `skipped`) |
| **3. Desk Lease** | `allocate_bot_desk_lease()` | `BotDeskLease` (`display_index`, `gateway_port`, `cdp_port`) |

---

## Mandatory Invariants Checklist

- [ ] **Hop-Depth Ceiling**: Reject bot-to-bot relays when `current_depth >= max_depth` (default 3).
- [ ] **In-Band MCP Gate**: Read-only tools auto-allow; write tools block unless `always_allowed` or interrupted.
- [ ] **Primary Non-Interference**: Never mutate or restart the host's primary agent gateway.
- [ ] **Unique Port & Display Leases**: Managed bots receive disjoint `display_index`, `gateway_port`, and `cdp_port`.
- [ ] **Slotted & Frozen Models**: All domain requests and outcomes use `slots=True, frozen=True` (Rule 12).
