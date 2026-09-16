# Orca Multi-Agent Orchestration Engine & Worktree Sandboxing

## Context
Running multiple AI agents (Codex CLI, Claude Code, OpenCode, Pi) side-by-side inside a single repository checkout causes severe filesystem contention, race conditions during tool file edits, and untracked git mutations. Furthermore, coordinating parallel agents requires durable message passing and unequivocal settlement authority rather than unstructured chat or prompt polling.

## Distilled Learnings & Mental Models

1. **Composite Worktree Addressing**:
   - Worktrees are uniquely addressed as `<repoId>::<worktreePath>`.
   - Truncating to bare repo IDs breaks target resolution across multi-repo workspaces.
   - Each agent operates in its own isolated worktree branch (`--no-parent` for independent tasks, `--parent-worktree active` for stacked PRs).

2. **Injected Preamble Authority**:
   - Worker authority comes strictly from injected environment preambles containing explicit `TASK_ID` and `DISPATCH_ID`.
   - Contact loss is not process death; preserve the three-way verdict `live` / `unverifiable` / `exited`.
   - Liveness is layered: fleet projection liveness (`projection.liveness`) measures agent state; PTY observation status (`observation.status`) measures terminal process state only.

3. **FIFO Mailbox Coordination & Keepalive Telemetry**:
   - Coordinator inboxes process unread messages in ordered FIFO batches.
   - Subscriptions block cleanly via `--wait` with periodic 15s keepalive pings (`_keepalive`), preventing busy-wait CPU thrashing.
   - Whole batches must be processed before emitting `--ack <delivery_id>`, preventing message replay loops.

4. **Structured Task Settlement**:
   - Workers emit `worker_done` containing a 3-sentence summary, modified files list, report path, and explicit `--outcome succeeded` or `--outcome failed`.
   - Coordinators reuse, retain, or release worker terminals via explicit post-settlement actions (`worker-release` or `worker-abandon`).

## Triggers & Seam Choices
- **Trigger**: Multi-agent coding swarms, parallel worktree branching, or cross-agent coordinator loops.
- **Seam Choice**: Integrated into Brain Harness via `plugins/agent_orchestration/orca_bridge/` providing `ServiceKey[OrcaBridgeService]("service.orca_bridge")` and `.agents/skills/orca-orchestrator/`.
