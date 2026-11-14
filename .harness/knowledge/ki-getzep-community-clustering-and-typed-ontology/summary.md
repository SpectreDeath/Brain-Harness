# GetZep: Community Label Propagation, Group Queues & Typed Ontology Builder

## Overview
- **Source Repositories**:
  - `https://github.com/getzep/graphiti` (`ed231965`)
  - `https://github.com/getzep/zep-python` (`305d8b3a`)
- **Primary Files**:
  - `graphiti_core/utils/maintenance/community_operations.py#L96-L171`
  - `mcp_server/src/services/queue_service.py#L28-L160`
  - `src/zep_cloud/ontology.py#L71-L217`

## Core Architecture & Invariants
1. **Weighted Label Propagation (`label_propagation`)**: Initializes each node into its own community ID, accumulates neighbor community votes weighted by `edge_count`, adopts a neighbor community when `candidate_rank > 1` (else `max(community_candidate, curr_community)`), and iterates until convergence.
2. **Per-Group Sequential Queue Serialization (`QueueService`)**: Allocates one `asyncio.Queue` and single worker coroutine per `group_id` so concurrent episodes across distinct groups run in parallel while writes within a single `group_id` never race during entity dedup or contradiction resolution.
3. **Class-Declared Typed Ontologies (`build_ontology`)**: Compiles `EntityModel` and `EdgeModel` subclasses into wire definitions supporting `text`, `int`, `float`, and `boolean` (`PropertyType`), rejects missing model docstrings or field `Field(description=...)` metadata loudly, honors `Excluded` fields, and attaches `Identity` markers strictly to entity types (edges carry no identity properties).

## Decision Heuristics & Anti-Patterns
- **Never allow concurrent episode ingestion on the same `group_id`**: Serialize per group to keep entity resolution and temporal invalidation race-free.
- **Never register ontology types without prompt descriptions or mark edge fields as `Identity`**: Prompt quality depends on docstrings and dedup identity applies only to nodes.
