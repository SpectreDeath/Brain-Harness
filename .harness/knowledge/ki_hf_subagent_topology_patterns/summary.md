# Multi-Agent Subagent Coordination Topologies & The 10+ Files Context Boundary

**ID:** `ki_hf_subagent_topology_patterns`  
**Category:** `agent_orchestration`  
**Origin:** *The Context Course: Unit 4 (Subagents)* (Hugging Face)  
**Provenance Lineage:** Units 4.1-4.4, Hugging Face, 2026.

## Executive Summary

Single-agent workflows degrade rapidly as repository context expands. As an agent reads dozens of files and executes sequential commands, its context window fills with verbose outputs (terminal logs, intermediate diffs, failed searches). This context bloat causes "lost in the middle" degradation, instruction forgetfulness, and runaway token costs.

Subagents solve this by partitioning tasks into isolated execution threads with independent context windows, returning only concise synthesized summaries to the parent orchestrator.

### The 4 Authoritative Coordination Patterns
1. **Fan-Out / Fan-In**: Parent partitions independent tasks (e.g. reviewing 5 different modules) across $K$ parallel subagents. Results fan in to an aggregator agent that compiles a final synthesized verdict.
2. **Pipeline (Sequential Handoff)**: Linear stage-gate processing where Agent A (Planner) outputs a spec to Agent B (Implementer), who passes code to Agent C (Tester).
3. **Supervisor (Hierarchical Delegation)**: Central coordinator dispatches work, monitors progress, verifies intermediate checkpoints, and handles retries upon child failure.
4. **Swarm (Peer Collaboration)**: Decentralized dynamic delegation where agents hand off execution directly via shared thread DAG state.

### The "10+ Files" Heuristic
The curriculum establishes an empirical trigger rule: **Whenever an engineering task touches, reads, or audits 10 or more files, single-agent execution is an anti-pattern.** Agents must immediately fan out to specialized subagents partitioned by directory or domain boundary.

## Operational Deployment Invariants

1. **Context Boundary Isolation**: Subagents must inherit only the minimal necessary task prompt, not the parent's entire accumulated message history.
2. **Deterministic Settlement Contract**: Subagents must terminate with structured, schema-validated summary payloads (e.g., Markdown table, JSON status) rather than free-form chatting.
3. **Bounded Swarm Concurrency**: Always bound maximum concurrent subagent proactors ($\le 5$) to prevent local CPU/pipe exhaustion and model API rate-limit throttling.
