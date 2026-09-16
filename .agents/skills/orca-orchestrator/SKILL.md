---
name: orca-orchestrator
description: Coordinate supervised Orca workers across parallel git worktrees, threaded FIFO inboxes, injected preambles, and structured worker_done settlements. Do not use for non-Orca single-agent tasks.
---

# Orca Orchestrator: Multi-Agent Worktree & Swarm Supervisor

`orca-orchestrator` coordinates parallel autonomous agent swarms (Codex CLI, Claude Code, OpenCode, Pi) within isolated Git worktrees. It enforces authoritative Dispatch preambles, layered liveness detection, FIFO coordinator mailboxes with 15s keepalives, and explicit settlement gates.

See [CARD.md](CARD.md) for the companion summary card, 5D complexity radar, and invariants checklist.
Consult `orca_bridge` plugin in `plugins/agent_orchestration/orca_bridge/` for programmatic IoC container resolution.

---

## The Three Foundational Pillars

### 1. Visual Brief & Telemetry Pillar
Every multi-agent swarm run can render an interactive HTML visual brief in `%TEMP%\orca-orchestrator-<timestamp>.html` detailing worktree topologies, worker placement DAGs, and mailbox delivery queues.

### 2. Mandatory Checkpoint & Governance Pillar
Coordinators must never dispatch destructive swarm actions or release unresolved resources without presenting an `implementation_plan.md` artifact with `RequestFeedback: true` to obtain explicit operator authorization.

### 3. Anti-Pattern Invariants
Rigid architectural guardrails prevent unacknowledged message storms, detached worktrees, and ambiguous task settlement.

---

## 5-Stage Progression Matrix

```
[1. Surface & Role Classification] ──► [2. Worktree & Worker Placement]
                                                 │
                                                 ▼
[5. Settlement & Worktree Cleanup] ◄── [4. Supervised Mailbox Coordination] ◄── [3. Injected Dispatch Preamble]
```

---

## 1. Surface & Role Classification

Classify the operational boundary and user intent before launching terminals or worktrees:

1. **Role Identification**:
   - **Coordinator**: User requests supervision, progress tracking, DAG coordination, or decision gates. Binds an orchestration Run.
   - **Dispatched Worker**: Current prompt has an injected preamble with `TASK_ID` and `DISPATCH_ID`. Follow worker obligations and idle after `worker_done`.
   - **Handoff Owner**: User requests full transfer of ownership ("handoff", "give this to another agent"). Launch independent worktree with `--no-parent` and stop.
2. **Path & Environment Verification**:
   - Confirm repo path and resolve the authoritative `orca` CLI executable.
   - Ensure execution host capabilities match required models (`gpt-6-astra`, `claude-3-7-sonnet`).

> **Completion criterion**: Role determined, operational mode selected, and CLI runtime verified.

---

## 2. Worktree & Worker Placement

Provision isolated Git worktrees to prevent workspace lock contention across parallel agents:

1. **Worktree Provisioning**:
   - Format worktree identifier strictly as `<repoId>::<worktreePath>`.
   - For independent tasks: `orca worktree create --name <task-name> --no-parent --json`.
   - For stacked work: specify `--parent-worktree active`.
2. **Worker Dispatch Placement**:
   - Dispatch workers with:
     ```bash
     orca orchestration worker-start --task <task_id> --worktree <wt_id> --agent codex --model <model> --effort <level> --json
     ```
   - Distinguish fleet projection liveness (`projection.liveness`) from physical PTY observation status (`observation.status`).

> **Completion criterion**: Dedicated worktree created, worker dispatched, and Dispatch ID recorded.

---

## 3. Injected Dispatch Preamble

Inject immutable authority into worker terminals:

1. **Authority Construction**:
   - Construct authoritative preamble containing:
     - `TASK_ID`: Unique task node identifier.
     - `DISPATCH_ID`: Authoritative attempt identifier.
     - `COORDINATOR_MAILBOX`: Run mailbox address (`run:<id>`).
2. **Worker Obligations**:
   - Worker must do ONLY the specified task.
   - For blocking questions, send `orca orchestration reply` rather than opening a local TUI.
   - Send heartbeats only at the cadence specified in the preamble.
   - Never encode completion or failure in freeform prose; always emit structured `worker_done`.

> **Completion criterion**: Preamble delivered to worker PTY and acknowledged.

---

## 4. Supervised Mailbox Coordination

Manage the asynchronous coordinator inbox to track progress without busy-waiting:

1. **FIFO Mailbox Ingestion**:
   - Check messages with:
     ```bash
     orca orchestration check --wait --timeout-ms 60000 --json
     ```
   - Ignore `_keepalive` telemetry lines (emitted every 15s to verify process liveness).
2. **Batch Acknowledgment**:
   - Process every message in the delivery batch before acknowledging with `--ack <delivery_id>`.
   - Answer worker questions promptly via:
     ```bash
     orca orchestration reply --id <msg_id> --body "<answer>" --json
     ```

> **Completion criterion**: All delivery batches processed and acknowledged with zero dropped messages.

---

## 5. Settlement & Worktree Cleanup

Conclude the orchestration cycle with explicit verification and resource reclamation:

1. **Settlement Verification**:
   - Worker transmits terminal settlement signal:
     ```bash
     orca orchestration send --type worker_done --outcome succeeded --files-modified "<csv>" --report-path "<path>" --json
     ```
   - Verify outcome is explicitly `succeeded` or `failed`.
2. **Resource Release & Retention**:
   - On success: merge or archive branch, and release worker terminal via `orca orchestration worker-release --dispatch <dispatch_id>`.
   - On failure: preserve worktree for inspection (`worker-abandon`), retaining all diagnostic logs.

> **Completion criterion**: Final task outcome reported to user with evidence, and settled resources reclaimed.

---

## Invariant Checklist

- [ ] All worktrees strictly addressed as `<repoId>::<worktreePath>`.
- [ ] Coordinator inbox polled with `--wait` and acknowledged in atomic FIFO batches.
- [ ] `worker_done` messages contain explicit `--outcome succeeded` or `--outcome failed`.
- [ ] No local TUI question prompts spawned in headless worker terminals.
- [ ] Slotted domain models (`slots=True`, `frozen=True`) used for all internal coordination records.

---

## Anti-Patterns

- **Ambiguous Worktree Addressing** — Truncating worktree IDs to raw repo IDs instead of using the two-part `<repoId>::<worktreePath>` format causes target resolution failures.
- **Prose-Only Failure Encoding** — Describing task errors in markdown text without emitting an explicit `--outcome failed` flag prevents coordinator automated error handling.
- **Unacknowledged Batch Thrashing** — Polling coordinator inboxes without acknowledging previous delivery batches via `--ack` causes identical message replays.
- **Premature Worktree Deletion** — Deleting worktree directories before verifying worker exit status discards diagnostic test logs and uncommitted git diffs.
- **Busy Polling Main Loops** — Polling the coordinator inbox in a tight sleep loop instead of using `--wait` with 15s keepalive streams burns excessive CPU cycles.
