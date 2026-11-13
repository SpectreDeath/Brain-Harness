---
name: proactive-ticket-orchestrator
description: Orchestrate proactive coding agent tickets using deterministic admission gates, follow-up ownership, and serialized transactional outbox delivery. Do not use for single-turn chat prompts or unauthenticated webhook injection.
---

# Proactive Ticket Orchestrator

`proactive-ticket-orchestrator` codifies the attention-minimizing proactive agent architecture distilled from `deepseek-ai/dsh-superagent-prototype`. It governs how external triggers (GitHub issues, pull requests, CI events, Feishu threads) are admitted, routed to isolated per-ticket Executors, and replied to without flooding human attention.

See [CARD.md](CARD.md) for the companion summary card and mandatory invariants checklist.
Consult `config.default.yaml` for baseline operational budgets and [../agent-harness-architect/SKILL.md](../agent-harness-architect/SKILL.md) for harness boundary design.

---

## 1. Deterministic Admission Gate

Evaluate every incoming `TriggerEnvelope` against an explicit `AdmissionRuleSet` before invoking semantic LLM assessment:

1. **Bot Guard**: Unlisted bots are dropped immediately; listed bots can at most produce `inferred` candidates when addressing the agent or reporting CI.
2. **Sender-Scope Matrix**: Classify `(listed vs unlisted, addressed vs unaddressed)` into `explicit`, `inferred`, or `ignore`.
3. **Accept Mode Enforcement**: When `accept_mode == "off"`, all `inferred` candidates are dropped; when `accept_mode == "record_only"`, `inferred` candidates are logged without dispatching side effects.

> **Completion criterion**: Every trigger receives a deterministic `GateOutcome` with `policy_version` recorded.

---

## 2. Follow-Up Ownership & Mandate Routing

Prevent duplicate tickets and authority creep on active threads:

1. **Executor Follow-Up Ownership**: Human replies on a Thread with active/resumable Ticket subscriptions route directly to those Ticket Executors (`deliver_to_ticket`), bypassing fresh Eval.
2. **Restricted Main-Session Control**: While an Executor owns a follow-up, the Main Session may only `stop` work; `accept`, `attach`, and `ignore` are refused.
3. **Single Hand-Back**: An Executor may hand back an out-of-scope follow-up once, releasing it to fresh Eval.

> **Completion criterion**: Trigger routed deterministically to `deliver_to_ticket`, `queue_eval`, or `drop_ignored`.

---

## 3. Transactional Outbox & Serialized Replies

Decouple synchronous domain mutations from asynchronous channel I/O:

1. **Synchronous Core + Post-Commit Effects**: Mutate Ticket/Thread state inside one atomic transaction and queue `OutboxReplyItem` payloads alongside state changes.
2. **Per-(Ticket, Channel) Serialization**: Serialize outbound messages within each `(ticket_id, channel_id)` lane so acknowledgements always precede results while unrelated tickets proceed in parallel.

> **Completion criterion**: Outbound replies partitioned into `ready_to_send` and `blocked_behind_head` lanes.

---

## The Three Foundational Pillars

### 1. Attention-Cost Minimization
Confirm once, stay silent while executing, ask one concrete structured question at a time, and stop by impact rather than effort.

### 2. Deterministic Gate Before Semantic Eval
Never let untrusted message bodies or prompt injections override allowlists, bot guards, or Mandate scope.

### 3. Synchronous State, Asynchronous Effects
Commit domain transitions synchronously and drain external Assessor, Executor, and Outbox side effects post-commit.

---

## Anti-Patterns

- **Unbounded Bot Fan-Out** — Treating bot comments or CI webhooks as `explicit` requests instead of capping them at `inferred` candidates.
- **Follow-Up Split-Brain** — Running fresh Eval on a human reply already owned by a live Ticket's Executor, spawning duplicate tickets.
- **Outbox Race Inversion** — Sending a final result or error before the Ticket's acknowledgement on the same conversation lane.
- **Monolithic Prompt Questions** — Burying blocking design questions inside long markdown reports instead of emitting one structured `Attention` field.
