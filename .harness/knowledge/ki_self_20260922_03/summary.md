# Strict Directed Graph Reachability & YAML Frontmatter Precedence in Skill Knowledge Graphs

## Problem
In autonomous agent swarms, capability discovery and skill chaining depend on BFS pathfinding across a directed skill knowledge graph. If the routing engine (`BuiltinSkillRegistryService.get_chain()`) synthesizes an artificial 2-hop direct edge `[start, target]` with `status: "ok"` whenever BFS discovers no path, calling agents are deceived into believing a viable pipeline exists between completely disconnected capability domains. This causes downstream ReAct loops to fail in-flight due to unsatisfied implicit assumptions. Furthermore, relying purely on text-similarity heuristic discovery to infer cross-skill dependencies introduces routing drift when skills declare explicit contractual prerequisites.

## Solution
1. **Strict Reachability Semantics**: In `BuiltinSkillRegistryService.get_chain()`, enforce `fallback_direct: bool = False` by default. When no directed path exists, return `SkillChainResult(status="no_path", chain=[], length=0)`. Allow callers to explicitly opt-in to heuristic synthetic fallback if desired.
2. **Explicit YAML Frontmatter Dependencies**: During skill card discovery in both `BuiltinSkillRegistryService` and `SkillCardParser`, inspect `SKILL.md` YAML frontmatter for explicit `dependencies: [...]` lists and inject these directed edges into the knowledge graph adjacency table.
3. **Canonical Pipeline Seeding**: Pre-seed the adjacency graph with established production pipeline pairs (e.g. data scout → topology mapper → epistemic isnad audit → architecture deepening) to establish verified baseline reachability.
4. **Configurable Intent Thresholding**: Support a configurable `min_confidence` parameter in `route_intent()` (default `0.20`), eliminating noisy, low-scoring candidate recommendations.

## Operational Guideline
- Always return explicit `no_path` results when graph reachability fails; never hallucinate synthetic hops without explicit caller opt-in.
- Declare cross-skill dependencies declaratively in `SKILL.md` YAML frontmatter for deterministic graph construction.
- Enforce `AGENTS.md` Rule 55 in all graph routing and capability orchestration services.

## Provenance
- Source files: `src/harness/services/skill_graph.py`, `plugins/memory_and_epistemics/skill_knowledge_graph/parser.py`
- Verification suite: `tests/test_architecture_hardening.py`, `tests/test_deepened_skill_registry.py`
- Repository Standard: `AGENTS.md` Rule 55
