---
name: ontology-spider
description: Query, traverse, validate, and explain Brain Harness knowledge vaults and domain ontologies using formal logic reasoning, entropy ranking, and Gruber audits. Do not use for fuzzy text search or ungrounded vector clustering.
---

# Ontology-Spider Skill

The **Ontology-Spider** skill equips AI agents with formal logic reasoning over Brain Harness Knowledge Vaults, code architectures, and domain models. Powered by SWI-Prolog with an automatic bounded Python BFS fallback, it provides deterministic graph traversals, Phase-5 path/negation/cardinality queries, Shannon/Laya attribute entropy ranking, and Gruber 5-criteria competency evaluation.

See [CARD.md](CARD.md) for the companion summary card, stage progression table, and mandatory invariants checklist.

---

## When to Use This Skill

Activate this skill whenever the task involves:
- **Multi-Hop Dependency & Shortest-Path Tracing**: Tracing transitive closures (`query transitive depends_on from <module>`) or explicit shortest paths (`query path [via <pred>] from <X> to <Y>`).
- **Taxonomic, Negation & Cardinality Checks**: Navigating `instance_of`/`subclass_of` ancestors, closed-world negation (`query not <S> <P> <O>`), and answer counting (`query count <inner_query>`).
- **Attribute-Constrained Recommendations & Entropy Ranking**: Finding matching candidates (`query recommend <class> where <k>=<v>`) and ranking attributes by information gain (`rank_attributes`).
- **Canonical Knowledge Vault Epistemic Audits**: Auditing `.harness/knowledge/` canonical `edges`, `isnad` provenance verification claims, and bi-temporal (`as_of`) validity windows.
- **Competency Evaluation & Schema Integrity Validation**: Measuring Gruber clarity/coherence/extendibility/minimal-commitment scores and detecting `acyclic`, `domain`/`range`, and `disjoint_with` violations.

---

## Query Syntax Reference

Queries follow the controlled `.dialog` language syntax:

| Query Type | Syntax | Description |
|---|---|---|
| **Fact Lookup** | `query what is <entity>?` | Retrieves incoming and outgoing relations for `<entity>`. |
| **Transitive Traversal** | `query transitive <pred> from <entity>` | Follows transitive closure of `<pred>` (e.g. `references_code`, `depends_on`). |
| **Ancestors** | `query ancestors of <entity>` | Traverses combined `instance_of` and `subclass_of` taxonomy upward. |
| **Shortest Path** | `query path [via <pred>] from <X> to <Y>` | Finds shortest directed proof path between two nodes. |
| **Closed-World Negation** | `query not <S> <P> <O>` | Returns `true` when no matching triple exists (supports `?`, `*`, `_`). |
| **Cardinality Aggregation** | `query count <inner_query>` | Counts answers returned by `<inner_query>`. |
| **Recommendation** | `query recommend <class> where <k>=<v>` | Matches class instances satisfying quoted or bare attribute filters. |
| **Proof Explanation** | `explain` or `query ... explain` | Emits rule trace, traversal path, and assertion provenance. |

---

## Micro-Kernel Service & Headless Runner Usage

### In-Memory Micro-Kernel (`Rule 49`)

```python
from pathlib import Path
from harness.services.ontology_spider import OntologySpiderKernelService

svc = OntologySpiderKernelService()
vault = Path(".harness/knowledge")

# 1. Execute transitive traversal with hop-distance reranking
res = svc.query(vault, "query transitive references_code from ki_5d_complexity_baseline", rank_by_distance=True)

# 2. Evaluate Gruber 5-criteria competency scorecard & federated epistemic audit
scorecard = svc.evaluate_competency(vault, ["query not ki_5d_complexity_baseline depends_on unknown_node"])
audit = svc.audit_vault_epistemics(vault, min_confidence=0.8)
print(audit.status, len(audit.unverified_entity_ids), audit.top_discriminating_attributes[:3])
```

### Headless CLI Runner (`Rule 57`)

```bash
python .agents/skills/ontology-spider/scripts/ontology_spider_runner.py --vault .harness/knowledge --audit-epistemics
python .agents/skills/ontology-spider/scripts/ontology_spider_runner.py --vault .harness/knowledge --query "query count ancestors of ki_5d_complexity_baseline" --rank-entropy
```

---

## Cross-Skill Integration Patterns

- Combine structural closure & cycle checks here with SHACL-AF PolicyFilter and PROV-O dual named-graph lineage in [trustgraph-ontology-governor](../trustgraph-ontology-governor/SKILL.md).
- Combine `as_of` bi-temporal edge slicing (`HarnessVaultModelSource(as_of=...)`) and `rank_by_distance=True` with temporal invalidation and RRF/MMR reranking in [graphiti-zep-memory-governor](../graphiti-zep-memory-governor/SKILL.md).

---

## Anti-Patterns

- **Free-Form Prompt Injection** — Passing unstructured conversational queries instead of controlled `.dialog` grammar.
- **Ungrounded Vector Approximation** — Using fuzzy semantic embedding searches when exact logical closures are required.
- **Ignoring Inference Fallback** — Assuming SWI-Prolog binary is universally installed without handling the pure-Python reasoner.
- **Unverified Traversal Claims** — Accepting transitive deductions without inspecting `path`, `rules_fired`, and `isnad_verified` status.
- **Legacy Dependency-Only Vault Scans** — Ignoring canonical `edges` and `isnad` metadata when loading `.harness/knowledge/` directories.
- **Unbounded Cycle Traversal** — Running transitive queries without validating acyclicity constraints first.
