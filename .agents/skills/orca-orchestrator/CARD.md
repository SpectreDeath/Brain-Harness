# Skill Summary Card: `orca-orchestrator`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:        orca-orchestrator                         │
│ Category:    agent_orchestration / swarm_coordination  │
│ Invocation:  /orca-orchestrator                        │
│ Trigger:     "orca worktree", "orca orchestrator",     │
│              "supervised swarm", "injected preamble"   │
│ Version:     1.0.0                                     │
│ Requires:    "orca_bridge", "agent-orchestration"      │
│ Provides:    "supervised_worktree_swarm_coordination"  │
├────────────────────────────────────────────────────────┤
│ Target:      Supervise multi-agent coding swarms in    │
│              isolated Git worktrees using FIFO inboxes │
│              and authoritative injected preambles.     │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Orchestration Progression

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Surface & Role** | Classify Coordinator vs Worker vs Handoff | Runtime & Role declaration | CLI verified & role identified |
| **2. Placement** | Create `<repoId>::<path>` isolated worktree | Dedicated git worktree | Worktree ID & PTY handle recorded |
| **3. Preamble** | Inject `TASK_ID` & `DISPATCH_ID` into worker PTY | Authoritative preamble | Preamble delivered & acknowledged |
| **4. Coordination** | Query FIFO mailbox with 15s keepalive streaming | Unread delivery batch | Atomic `--ack` batch processing |
| **5. Settlement** | Verify `worker_done` outcome & release resources | Task report & resource release | Outcome proven & resources reclaimed |

---

## 5D Complexity Radar

- **Ambiguity**: 0.30 (Strict Zod schemas and CLI contract parameters)
- **Span**: 0.92 (Cross-platform PTY multiplexing, worktrees, and IPC)
- **Depth**: 0.90 (Injected preamble lifecycle and layered liveness verdicts)
- **Rigor**: 0.95 (Reliability ratchets and Playwright CDP verification)
- **Concurrency**: 0.94 (Parallel worktree swarms and FIFO coordinator mailboxes)

---

## Invariants & Guardrails

- [ ] **Address Integrity**: Strictly address worktrees as `<repoId>::<worktreePath>`.
- [ ] **Atomic ACK**: Always process full FIFO delivery batches before emitting `--ack`.
- [ ] **Explicit Outcome**: Require explicit `--outcome succeeded` or `--outcome failed` on `worker_done`.
- [ ] **No Local TUIs**: Workers use `orchestration reply` instead of interactive question prompts.
- [ ] **Slotted Data Models**: Internal coordination entities must use `@dataclass(slots=True, frozen=True)`.
