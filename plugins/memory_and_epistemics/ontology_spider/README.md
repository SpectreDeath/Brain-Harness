# Ontology-Spider Brain Harness Plugin

A domain-partitioned plugin integrating the **Ontology-Spider** ontological reasoning engine into Brain Harness (`memory_and_epistemics` category).

## Architecture

This plugin implements the thin adapter layer across the `ModelSource` seam:

```mermaid
flowchart LR
    Vault[(Brain Harness Vault)] -->|JSON / Items| Adapter[HarnessVaultModelSource]
    Adapter -->|ModelSource.load| Engine[Ontology-Spider Engine]
    Engine -->|Prolog / Fallback Reasoner| Answers[Query Answers + Proof Traces]
    Answers --> Service[OntologySpiderService]
    Service --> Plugin[OntologySpiderPlugin]
    Plugin --> IoC[Brain Harness IoC Container]
```

## Features

- **Seam Boundary**: Zero brain-harness code is imported by `ontology_spider`. The adapter lives entirely inside this plugin and depends on the engine.
- **Transitive Reasoning**: Multi-hop reachability over typed edges (`depends_on`, `subclass_of`, etc.).
- **Proof Explanations**: Answers include complete graph paths and inference rule audit logs.
- **Dual-Mode Execution**: High-performance reasoning via SWI-Prolog with automatic pure-Python fallback.

## Testing

```bash
pytest plugins/memory_and_epistemics/ontology_spider/test_ontology_spider_plugin.py -v
```
