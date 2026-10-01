# Harness Agent Reasoning & Execution (`harness.agent`)

The `harness.agent` package provides the core reasoning engines, autonomous step loops, context optimizers, and multi-agent swarm coordinators powering Brain Harness.

---

## Central Function & Capabilities

The agent package orchestrates the lifecycle of autonomous tasks:
1. **ReAct Step Execution**: Implements the iterative Thought $\rightarrow$ Action $\rightarrow$ Observation reasoning loop with in-flight tool repair and transactional rollback.
2. **Context Optimization**: Deterministic multi-pass context pruning (whitespace reduction, middle-out tool output truncation, PageRanked AST repo map injection) to prevent context window blowout.
3. **Session Tree Management**: Branchable, append-only conversation session trees tracking checkpoints, tool transcripts, and execution tokens.
4. **Hierarchical Swarm Coordination**: Direct acyclic graph (DAG) swarm orchestration with dynamic token governance, parallel subagent wave spawning, and multi-agent consensus voting.

---

## Architectural Invariants

- **Transactional Step Isolation (Rule 8)**: Tool invocations run within `context.transaction()`. Errors trigger automatic rollback and workspace restoration (`rollback_transaction()`).
- **Deterministic Pre-LLM Pruning (Rule 9)**: The `StepExecutionEngine` prunes redundant whitespace and middle-out truncates oversized observation payloads before token budgeting.
- **In-Flight Self-Repair (Rule 16 & Rule 21)**: Tool calls normalize code fences, auto-repair trailing JSON commas, and verify syntax diagnostics via in-flight linter feedback before committing.
- **Authoritative Thread DAG (Rule 17 & Rule 36)**: Swarm node threads use composite keys `f"{run_id}_{node_id}"` with tracked lifecycle states (`Open`, `Closed`, `Completed`, `Failed`).

---

## Key Modules & Symbols

| Module | Core Classes / Symbols | Description |
|---|---|---|
| [`base.py`](base.py) | `AgentLoopService`, `AgentStep`, `AgentTaskResult`, `AGENT_LOOP_KEY` | Abstract service protocol and slotted value objects for agent reasoning loops. |
| [`context_optimizer.py`](context_optimizer.py) | `AgentContextOptimizer`, `ContextOptimizationConfig`, `DefaultContextOptimizer` | Prunes context tokens, injects AST repo maps, and bounds LLM input budgets. |
| [`react.py`](react.py) | `ReActAgentLoop`, `StepExecutionEngine`, `ReActAgentPlugin` | Primary autonomous ReAct engine with transactional checkpointing and tool execution. |
| [`session.py`](session.py) | `AgentSessionManager`, `AgentSession`, `SessionTreeNode`, `AGENT_SESSION_MANAGER_KEY` | Branchable tree DAG session manager with append-only step storage. |
| [`swarm.py`](swarm.py) | `SwarmCoordinator`, `SwarmDAG`, `SwarmNode`, `ConsensusEngine`, `SWARM_COORDINATOR_KEY` | Multi-agent DAG swarm coordinator with token governance and consensus deliberation. |

---

## Programmatic Usage Example

```python
import asyncio
from harness.kernel.runtime import HarnessRuntime
from harness.agent.base import AGENT_LOOP_KEY
from harness.agent.session import AGENT_SESSION_MANAGER_KEY

async def run_agent_task(prompt: str) -> str:
    async with HarnessRuntime.create() as runtime:
        ctx = runtime.context
        
        # 1. Resolve agent loop and session manager from IoC container
        agent_loop = ctx.require(AGENT_LOOP_KEY)
        session_mgr = ctx.require(AGENT_SESSION_MANAGER_KEY)
        
        # 2. Initialize a branchable session
        session = await session_mgr.create_session(task=prompt)
        
        # 3. Execute autonomous reasoning loop
        result = await agent_loop.run(
            task=prompt,
            session_id=session.session_id,
            max_steps=25,
        )
        return result.final_answer
```

---

## Related Documentation

- [Step Execution Architecture Guide](../../../docs/EXPLANATION.md#2-react-agent-step-engine--context-optimization)
- [How-To: Run Multi-Agent Swarms](../../../docs/HOWTO.md#orchestrating-multi-agent-swarms)
- [Agent Reference](../../../docs/reference/agent.md)
- [Micro-Kernel Architecture](../kernel/README.md)
