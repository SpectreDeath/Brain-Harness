# Stage Artifact Contracts, Dynamic Directed FEEDS Edge Synthesis & Cycle Prevention

## Problem
In modular skill knowledge graphs:
1. Inter-skill handoffs (e.g. code generation -> lint verification -> adversarial test review) are frequently hardcoded or lost, forcing agent planners to guess which skill to invoke next.
2. If the knowledge graph naively connects skills whenever stage inputs and outputs match by name, mutual dependencies (e.g. Skill A produces diff consumed by Skill B, while Skill B produces report consumed by Skill A) create directed cycles. Cycles break topological sorting, BFS shortest-path algorithms, and cause infinite loops during multi-agent DAG execution.

## Solution
1. **Stage Contract Syntax**:
   - `SkillCardParser` scans `SKILL.md` stage sections for `Produces artifact: <name>` and `Consumes artifact(s): <name1>, <name2>`.
   - Extracted into slotted `SkillStageDefinition.primary_artifact` and `SkillStageDefinition.consumes`.
2. **Dynamic FEEDS Edge Synthesis**:
   - During catalog indexing, the graph matches producer skills with consumer skills and synthesizes directed `EdgeType.FEEDS` edges.
3. **DFS Acyclicity Guard**:
   - Before inserting any synthesized edge `src -> dst`, `_would_create_cycle(adj, src, dst)` runs a depth-first search from `dst`. If `src` is reachable from `dst`, the edge is rejected and logged, preserving a strict Directed Acyclic Graph.

## Operational Guideline
- Always declare input and output artifacts using standard tags: `Produces artifact: <name>` and `Consumes artifact(s): <name>`.
- Verify acyclicity in graph test suites using `test_feeds_edge_acyclicity`.
- When querying skill chains via `route_intent()`, prioritize DAG paths along `FEEDS` edges for compound multi-stage tasks.

## Provenance
- Source files: `src/harness/services/skill_parser.py`, `src/harness/services/skill_graph.py`
- Test contracts: `tests/test_skill_graph_hardening.py::test_contract_edge_synthesis`, `test_feeds_edge_acyclicity`
- Verification: 42/42 tests passing
