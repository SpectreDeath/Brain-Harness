# Skill Knowledge Graph Catalog Summary & Match Key Standardization

**ID:** `ki_self_20260903_02`  
**Category:** `skill_routing_and_discovery`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `transcript.jsonl#step-164-182`, `plugins/memory_and_epistemics/skill_knowledge_graph/main.py`, `AGENTS.md#Rule35`

## Executive Summary
The Skill Knowledge Graph (`plugins.memory_and_epistemics.skill_knowledge_graph.main`) serves two distinct operational functions: catalog re-indexing and embedding/keyword routing. Callers frequently conflate the return type of `index_skill_catalog()` (which returns an indexing summary statistics dictionary) with the catalog itself, or expect `query_skill_router()` match dicts to be keyed by `'skill'` instead of `'skill_name'`.

## Architectural Invariants & Rules
1. `index_skill_catalog()` returns a metadata summary dictionary (`status`, `indexed_skills`, `total_nodes`, `total_edges`, `domains`).
2. Authoritative registered skill nodes reside on the graph singleton: access them via `graph.nodes` or `_GRAPH_INSTANCE.nodes`.
3. `query_skill_router(prompt)` returns match records keyed strictly by `'skill_name'` (e.g. `match['skill_name']`), never `'skill'`.
4. Consumers must use `match.get("skill_name") or match.get("name")` to defend against schema variance.
5. Codified in repository rule `AGENTS.md` Rule 35.
