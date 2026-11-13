```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: proactive-ticket-orchestrator                                 │
│ Category: agent_orchestration / proactive-agents                     │
│ Version: 1.0.0                                                       │
│ Invocation: /proactive-ticket-orchestrator                           │
│ Triggers: "proactive ticket", "admission gate", "mandate routing",   │
│           "outbox delivery", "follow-up ownership"                   │
│ Requires: "agent-harness-architect"                                  │
│ Target: Deterministic gate, ticket follow-up routing & outbox plans  │
└──────────────────────────────────────────────────────────────────────┘
```

# Proactive Ticket Orchestrator — Companion Summary Card

## Pipeline Stages

| Stage | Operation | Output Model |
| --- | --- | --- |
| **1. Admission Gate** | `evaluate_admission_gate()` | `GateOutcome` (`explicit` \| `inferred` \| `ignore`) |
| **2. Trigger Routing** | `route_trigger_disposition()` | `TicketRouteOutcome` (`deliver_to_ticket` \| `queue_eval` \| `drop_ignored`) |
| **3. Outbox Planning** | `plan_outbox_delivery()` | `OutboxDeliveryPlan` (`ready_to_send`, `blocked_behind_head`) |

---

## Mandatory Invariants Checklist

- [ ] **Deterministic Gate First**: Evaluate sender allowlists and bot rules before any LLM assessment.
- [ ] **Bot Ceiling Invariant**: Bots never produce `explicit` requests; unlisted bots are always ignored.
- [ ] **Follow-Up Ownership**: Human replies on subscribed threads route to owning Ticket Executors; Main Session may only `stop`.
- [ ] **Per-Lane Outbox Ordering**: Outbound replies for the same `(ticket_id, channel_id)` never overtake an earlier pending message.
- [ ] **Slotted & Frozen Models**: All domain envelopes and outcomes use `slots=True, frozen=True` (Rule 12).
