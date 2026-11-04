---
name: ontology-spider
description: Query, traverse, validate, and explain Brain Harness knowledge vaults and domain ontologies using formal logic reasoning.
---

# Ontology-Spider Skill

The **Ontology-Spider** skill equips AI agents with formal logic reasoning over Brain Harness vaults, code architectures, and domain models. Unlike unstructured vector search or fuzzy heuristic lookup, Ontology-Spider provides deterministic graph traversals, inheritance reasoning, and mathematically provable explanations.

---

## When to Use This Skill

Activate this skill whenever the task involves:
- **Multi-Hop Dependency Tracing**: Finding all transitive dependencies or impact paths across modules, specs, or tasks (e.g. `query transitive depends_on from <module>`).
- **Taxonomic & Inheritance Navigation**: Querying class hierarchies, generalized concepts, or instance types (e.g. `query ancestors of <class>`).
- **Attribute-Constrained Recommendations**: Finding optimal candidate components or assets matching specific parameter constraints (e.g. `query recommend drone where payload=5`).
- **Formal Proof Tracing & Explanations**: Verifying exactly *why* a relation or dependency exists, including which base assertions fired, which inference rules ran, and what graph path was taken.
- **Architectural & Schema Integrity Validation**: Detecting circular dependencies (`acyclic`), domain/range typing mismatches, and mutually exclusive conflicts (`disjoint_with`).

---

## Query Syntax Reference

Queries follow the controlled `.dialog` language syntax:

| Query Type | Syntax | Description |
|---|---|---|
| **Fact Lookup** | `query what is <entity>?` | Retrieves all incoming and outgoing relations for `<entity>`. |
| **Transitive Traversal** | `query transitive <pred> from <entity>` | Follows transitive closure of `<pred>` (e.g. `depends_on`, `subclass_of`). |
| **Ancestors** | `query ancestors of <entity>` | Traverses combined `instance_of` and `subclass_of` taxonomy upward. |
| **Recommendation** | `query recommend <class> where <k>=<v>` | Matches instances of `<class>` conforming to key-value attribute filters. |
| **Pattern Triple** | `query <subj> <pred> ?` | Matches facts satisfying the triple pattern. |
| **Proof Explanation** | `explain` or `query ... explain` | Emits full rule trace, graph path, and assertion provenance for preceding query. |

---

## Python API Usage in Brain Harness

```python
from plugins.memory_and_epistemics.ontology_spider.service import OntologySpiderService

service = OntologySpiderService()

# 1. Execute a transitive dependency query over a vault export
result = service.query("vault_export.json", "query transitive depends_on from my_service")
print("Dependencies:", [a["value"] for a in result["answers"]])

# 2. Inspect the proof explanation
for ans in result["answers"]:
    print(f"Node: {ans['value']}, Path: {' -> '.join(ans['path'])}, Rules: {ans['rules_fired']}")

# 3. Validate structural schema integrity
violations = service.validate("vault_export.json")
if violations:
    print(f"Found {len(violations)} schema violations!")
```

---

## Boundaries & Constraints

- **Trusted Input**: Operates over structured JSON vault exports or on-disk `metadata.json` items. Unstructured markdown bodies remain referenced by URI.
- **Controlled Language**: Use the exact grammar specified above; do not construct free-form natural language query strings.
- **Performance**: Powered by SWI-Prolog with automatic bounded pure-Python degraded fallback when SWI-Prolog is not present on the host.
