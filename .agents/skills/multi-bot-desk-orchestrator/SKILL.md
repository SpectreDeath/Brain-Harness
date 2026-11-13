---
name: multi-bot-desk-orchestrator
description: Orchestrate multi-bot agent teams with per-bot serial turn queues, bounded hop-depth guards, in-band MCP tool approvals, and isolated display/gateway leases. Do not use for single-bot stateless chat or raw VNC tunneling.
---

# Multi-Bot Desk Orchestrator

`multi-bot-desk-orchestrator` distills the multi-agent desktop orchestration architecture from `bot-hq`. It governs how multiple persistent bots collaborate on a shared host without colliding on browsers, corrupting primary agent configs, entering infinite bot-to-bot loops, or bypassing human tool approvals.

See [CARD.md](CARD.md) for the companion summary card and mandatory invariants checklist.
Consult `config.default.yaml` for baseline operational budgets and [../agent-harness-architect/SKILL.md](../agent-harness-architect/SKILL.md) for harness isolation design.

---

## 1. Per-Bot Serial Queue & Hop-Depth Guard

Serialize turns per `bot_id` and bound multi-bot chatter:

1. **Serial Turn Queue**: Execute one turn per bot at a time so browser/desktop state never races.
2. **Hop-Depth Cap**: Track `current_depth` across `send_to_bot` relays and reject dispatches once `current_depth >= max_depth` (default `3`).
3. **Room Fan-Out Bound**: In group rooms, route to `@mentioned` members or cap unmentioned broadcasts at 3 members.

> **Completion criterion**: `BotHopDispatchOutcome` returned with bounded `next_depth` and `target_bot_ids`.

---

## 2. In-Band MCP Approval Gate

Enforce human-in-the-loop safety inside the MCP tool endpoint:

1. **Read-Only Fast Path**: Read-only tools and explicitly `always_allowed_tools` execute immediately (`auto_allow`).
2. **Blocking Write Card**: Mutating tools suspend the turn (`require_approval`) until the user approves or refuses.
3. **User Interrupt Supersession**: A new user message immediately supersedes pending approval cards as `skipped`.

> **Completion criterion**: `McpApprovalOutcome` classifies every tool call without engine-specific forks.

---

## 3. Primary-vs-Managed Home & Screen Isolation

Isolate managed bots while preserving the host's primary agent:

1. **Primary Non-Interference**: Never restart, stop, or rewrite the primary bot's config (`mutates_primary_config = False`).
2. **Dedicated Resource Leases**: Assign each managed bot a unique `display_index` (1–3), `gateway_port` (`8650 + slot`), and `cdp_port` (`9200 + slot`).

> **Completion criterion**: `BotDeskLease` allocated with zero port or display collisions.

---

## The Three Foundational Pillars

### 1. Bounded Multi-Bot Collaboration
Cap bot-to-bot hops at 3 and room fan-outs at 3 so teams collaborate without runaway ping-pong loops.

### 2. In-Band MCP Safety Boundary
Gate mutating tools inside the MCP endpoint so every channel and engine shares one approval contract.

### 3. Non-Destructive Primary Coexistence
Run managed bots in isolated homes, ports, and displays without mutating the primary host agent.

---

## Anti-Patterns

- **Unbounded Bot Ping-Pong** — Allowing `send_to_bot` relays without a strict `max_depth` ceiling, causing infinite turn loops.
- **Shared Browser Helper Collision** — Launching multiple managed bots against the same `BH_HOME` or Chrome DevTools port.
- **Primary Config Clobbering** — Restarting or overwriting the host's primary agent `config.yaml` when adding companion bots.
- **Stale Approval Deadlock** — Leaving a pending tool approval card active after the user has already sent a new message or interrupted the turn.
