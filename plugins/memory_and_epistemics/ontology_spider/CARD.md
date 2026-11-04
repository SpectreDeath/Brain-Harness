# Skill Card: ontology-spider

| Attribute | Value |
|---|---|
| **Plugin ID** | `plugin.ontology_spider` |
| **Category** | `memory_and_epistemics` |
| **Version** | `0.2.0` |
| **Interface** | IoC `ServiceKey[OntologySpiderService]("service.ontology_spider")` + Agent Skill |
| **Isolation** | `in_process` |
| **Reasoner** | SWI-Prolog with Pure-Python degraded fallback |

## Capabilities
1. **Multi-Hop Traversal**: Computes transitive closures across directed knowledge graphs.
2. **Proof Tracing**: Every derived answer carries its graph traversal path, inference rules fired, and base fact provenance.
3. **Schema Integrity**: Enforces acyclicity, domain/range types, and disjoint class memberships.
4. **Vault Interop**: Maps Brain Harness items, types, and edges through the `ModelSource` seam.
