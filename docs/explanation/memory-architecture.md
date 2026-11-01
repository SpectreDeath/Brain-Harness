# Memory Architecture: The 5-Store Partitioned Federation

## Overview

Brain Harness avoids the anti-pattern of a monolithic "one-size-fits-all" memory database. Different cognitive tasks require radically different data models, temporal horizons, and consistency guarantees. 

The harness explicitly partitions memory across five specialized, single-responsibility stores unified behind a deterministic router seam (`harness memory route <question>`).

---

## The 5-Store Partition Table

| Store Identifier | Component / Plugin | Underlying Paradigm | Architectural Scope | Authoritative CLI Seam | Service Key |
|---|---|---|---|---|---|
| **`okf_memory`** | `plugins/memory_and_epistemics/okf_memory` | Normative Git concept bundle (OKF v0.2) | Path-based pre-edit governance, strict architectural rules, actor trust hierarchy | `harness okf scope <path>` | `service.okf_memory` |
| **`memgraphrag`** | `plugins/memory_and_epistemics/memgraphrag` | Unstructured passage GraphRAG | Entity-relation-entity triple extraction from raw texts, semantic contradiction detection | `harness doc` / `harness knowledge` | `service.memgraphrag` |
| **`graphiti_memory`** | `plugins/memory_and_epistemics/graphiti_memory` | Bi-temporal episodic interaction graph | Multi-turn conversational episodes, temporal state evolution, invalidation of superseded facts | `harness trajectory` / `harness session` | `service.graphiti_memory` |
| **`memory_decay_engine`** | `plugins/memory_and_epistemics/memory_decay_engine` | Channel-weighted Ebbinghaus decay curve | In-flight conversational working-memory retention, soft eviction ($R(t) < 0.20$), non-linear stability reinforcement | `harness memory working-set` | `service.memory_decay` |
| **`knowledge_vault`** | `src/harness/services/storage/` | Canonical dual-file directory (`Rule 40`) | Long-term verified truths, cryptographic Isnad provenance chains, architectural invariants | `harness knowledge query` | `service.knowledge_vault` |

---

## Conceptual & Architectural Boundaries

```
                   ┌────────────────────────────────────────┐
                   │        Developer / Agent Query         │
                   └───────────────────┬────────────────────┘
                                       │
                         harness memory route <query>
                                       │
        ┌───────────────┬──────────────┼──────────────┬───────────────┐
        ▼               ▼              ▼              ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────────┐ ┌─────────────┐
│  okf_memory  │ │ memgraphrag  │ │ graphiti │ │ decay_engine │ │    vault    │
├──────────────┤ ├──────────────┤ ├──────────┤ ├──────────────┤ ├─────────────┤
│ Normative    │ │ Triple       │ │ Episodic │ │ Ebbinghaus   │ │ Canonical   │
│ Code Rules   │ │ Passages     │ │ Timeline │ │ Working Set  │ │ Dual-File   │
└──────────────┘ └──────────────┘ └──────────┘ └──────────────┘ └─────────────┘
```

### 1. Normative Rules vs Epistemic Facts
- **`okf_memory`** is *prescriptive*: It enforces what an agent **must or must not do** when modifying paths (e.g. `src/harness/kernel/` requires Maintainer trust).
- **`knowledge_vault`** is *descriptive*: It records verified empirical discoveries, isnad lineage, and research heuristics.

### 2. Episodic Timeline vs Working Memory
- **`graphiti_memory`** maintains *temporal history*: It records what happened across sessions, tracking when a past fact became invalidated by a newer observation.
- **`memory_decay_engine`** maintains *transient focus*: It governs what fits in the active LLM context window right now, soft-evicting noisy tool outputs.

### 3. Unstructured Triples vs Formatted KIs
- **`memgraphrag`** extracts ad-hoc graph structures from raw prose or scraped documentation to identify conflicts.
- **`knowledge_vault`** stores curated, human/model-refined dual-file entries (`metadata.json` + `summary.md`).

---

## Unified Routing CLI

Inspect store status and route inquiries directly:
```bash
# View all 5 memory stores and their configurations
harness memory status --json

# Route inquiries to the authoritative store
harness memory route "what rules govern editing src/harness/kernel" --json
harness memory route "what changed in yesterday's session episodes" --json
harness memory route "which items were soft-evicted this turn" --json
harness memory route "check raw passages for conflicting entity claims" --json
```

See the [Learning Core Lifecycle](./learning-core-lifecycle.md) and [CLI Reference](../reference/cli.md) for full details.

