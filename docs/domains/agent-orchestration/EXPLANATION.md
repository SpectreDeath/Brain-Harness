# Agent Orchestration Domain Architecture

The Agent Orchestration domain governs multi-agent coordination, hierarchical task decomposition, dialectical debate, quality evaluation, and human governance.

---

## Domain Scope & Boundaries

This domain coordinates autonomous agent execution loops and multi-agent systems:
- **In Scope**: ReAct step engines, swarm thread DAGs, dialectical debate loops, Aquinas-style reflection checkpoints, consensus deliberation, and context budget optimization.
- **Out of Scope**: Direct OS system socket administration (Security & Forensics), raw database indexing (Data Engineering), or low-level Git plumbing (Software Engineering).

---

## Ubiquitous Language & Core Terminology

- **Supervisor**: A coordination node that decomposes high-level goals into DAG waves and delegates them to specialized workers. (*Avoid*: Manager, master, boss)
- **Debater**: A dual-agent dialectical loop where a Generator node and a Critic node challenge each other's assertions until consensus or timeout. (*Avoid*: Arguer, combatant, discussion loop)
- **Critic**: An evaluation agent that scores proposals against explicit criteria and searches for edge-case vulnerabilities. (*Avoid*: Reviewer, judge, grader)
- **Task Plan**: A directed acyclic graph (DAG) of discrete execution steps with explicit dependencies and completion gates. (*Avoid*: Todo list, checklist, schedule)
- **Checkpoint**: A blocking pause in execution that mandates explicit human review before proceeding with irreversible actions. (*Avoid*: Breakpoint, pause, stop sign)
- **Questio Check**: An Aquinas-style adversarial reflection step that formulates objections and answers before executing destructive or structural operations. (*Avoid*: Self-review, sanity check, pre-flight inspection)

---

## Architectural Invariants & Patterns

- **Transactional Tool Isolation (Rule 8)**: Agent tool invocations execute inside atomic context transactions with automated Git rollback on failure.
- **Deterministic Pre-LLM Context Optimization (Rule 9)**: Step engines apply deterministic multi-pass context pruning (whitespace reduction, middle-out tool reduction) before LLM invocation.
- **Authoritative Thread DAG (Rule 17 & Rule 36)**: Swarm nodes track lifecycle states (`Open`, `Closed`, `Completed`, `Failed`) keyed by composite IDs (`f"{run_id}_{node_id}"`).
- **Dynamic 5D Compute Complexity (Rule 25)**: Multi-agent swarms scoring composite 5D complexity $\ge 0.75$ lock reasoning budgets to High and subprocess timeouts to 300s+.

---

## Co-Located Plugins & Micro-Kernel Services

- **ReAct Execution Engine**: [`src/harness/agent/react.py`](../../../src/harness/agent/react.py) providing `ReActAgentLoop` and `StepExecutionEngine`.
- **Swarm Coordinator**: [`src/harness/agent/swarm.py`](../../../src/harness/agent/swarm.py) providing `SwarmCoordinator` and `ConsensusEngine`.
- **Session DAG Store**: [`src/harness/services/agent_graph.py`](../../../src/harness/services/agent_graph.py) providing `AgentExecutionGraphService` (`AGENT_GRAPH_STORE_KEY`).
- **Deterministic Validation Loop Plugin**: [`plugins/agent_orchestration/deterministic_validation_loop/`](../../../plugins/agent_orchestration/deterministic_validation_loop/README.md).
- **Tau Harness Bridge**: [`plugins/agent_orchestration/tau_harness_bridge/`](../../../plugins/agent_orchestration/tau_harness_bridge/README.md).

---

## Associated Agent Skills

- [`ai-agent-engineer`](../../../.agents/skills/ai-agent-engineer/SKILL.md): Scopes, composes, and evaluates production autonomous systems.
- [`game-theoretic-swarm-deliberator`](../../../.agents/skills/game-theoretic-swarm-deliberator/SKILL.md): Orchestrates multi-persona swarms to resolve payoff matrices.
- [`orca-orchestrator`](../../../.agents/skills/orca-orchestrator/SKILL.md): Coordinates supervised workers across parallel git worktrees.
- [`questio-reflection`](../../../.agents/skills/questio-reflection/SKILL.md): Aquinas-style adversarial objection and reflection gates.
