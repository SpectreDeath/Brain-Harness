# Orca Bridge Plugin

The **Orca Bridge Plugin** (`plugin.orca_bridge`) connects Brain Harness directly to the **Orca** agent orchestrator (`https://github.com/stablyai/orca`). It provides Git worktree isolation, multi-agent worker dispatching (OpenAI Codex CLI, Claude Code, OpenCode, Pi), FIFO coordinator inboxes, and PTY lifecycle management.

## Architectural Seam

- **Category**: `agent_orchestration`
- **Service Key**: `ServiceKey[OrcaBridgeService]("service.orca_bridge")`
- **Isolation**: Subprocess / Host CLI bridge with deterministic in-memory fallback
- **Provider**: `OrcaBridgePlugin` exported as module singleton `plugin`

## Key Capabilities

1. **Git Worktree Isolation**:
   - Creates isolated Git worktrees addressed strictly as `<repoId>::<worktreePath>`.
   - Prevents agent work collisions and file locking issues across parallel swarms.

2. **Injected Preamble Authority**:
   - Supervised workers are bound by injected prompts containing explicit `TASK_ID` and `DISPATCH_ID`.
   - Distinguishes fleet projection liveness from low-level PTY process health.

3. **FIFO Coordinator Inboxes**:
   - Coordinator terminals subscribe to structured mailboxes with atomic ACK batching and 15s keepalive pings.
   - Workers signal completion via explicit `worker_done` messages (`--outcome succeeded` or `--outcome failed`).

## Usage Example

```python
from harness.kernel.context import ServiceContext
from harness.services.orca_bridge import (
    ORCA_BRIDGE_KEY,
    OrcaRunConfig,
    OrcaWorkerConfig,
    OrcaWorktreeConfig,
)

# Resolve service from container
context: ServiceContext = ...
orca = context.require(ORCA_BRIDGE_KEY)

# 1. Create a worktree
wt = orca.create_worktree(OrcaWorktreeConfig(name="feature-auth", repo_id="repo-main"))

# 2. Bind a coordinator Run
run = orca.create_run(OrcaRunConfig(objective="Implement OAuth2 PKCE flow"))

# 3. Start a supervised worker
worker = orca.start_worker(
    OrcaWorkerConfig(
        spec="Add OAuth2 authorization code grant",
        agent="codex",
        worktree=wt.worktree_id,
    )
)

# 4. Check coordinator inbox
batch = orca.check_mailbox(wait=True, timeout_ms=30000)
for msg in batch.messages:
    print(f"Received {msg['type']}: {msg['subject']}")
```
