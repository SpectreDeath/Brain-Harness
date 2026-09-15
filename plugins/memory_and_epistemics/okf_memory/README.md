# plugin.okf_memory (v1.0.0)

Git-native agent memory governor providing BM25 search, pre-edit governance scoping, concept mutations, and trust ordering validation

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/memory_and_epistemics/okf_memory` |
| Category | `memory_and_epistemics` |
| Isolation Mode | `in_process` |
| Services Provided | `service.okf_memory` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `okf_search` | `(query, for_path, limit, bundle_dir)` | Search knowledge bundle using BM25 lexical ranking or evaluate for-path governance constraints before modifying code |
| `okf_show` | `(concept_id, bundle_dir)` | Retrieve full markdown content, frontmatter metadata, and governance rules for a specific concept |
| `okf_create` | `(concept_id, title, concept_type, description, body, governance, code_refs, bundle_dir)` | Create a new concept document with frontmatter sanitization and automatic parent index and log updating |
| `okf_update` | `(concept_id, title, description, body, governance, code_refs, bundle_dir)` | Update an existing concept document with automatic parent index and audit log synchronization |
| `okf_relate` | `(source_id, target_id, description, bundle_dir)` | Link two concepts together bidirectionally in frontmatter relations |
| `okf_validate` | `(strict, bundle_dir)` | Validate knowledge bundle against OKF normative schema, link consistency, and actor trust ordering |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

OKF Agent Memory Plugin for Brain Harness.

Implements the Open Knowledge Framework (OKF v0.2) protocol:
- Git-native plain text knowledge bundle management
- Sub-millisecond BM25 lexical ranking with governance boosting
- Pre-edit governance scoping for target code paths
- Atomic concept mutation with auto-updating parent indexes and audit logs
- Actor trust ordering invariants and normative schema validation

#### Classes

- `class OKFMemoryEngine` — In-memory and filesystem engine for OKF v0.2 knowledge bundles.
  - `def __init__(default_root) -> None`
  - `def search(query, for_path, limit, bundle_dir) -> dict[str, Any]` — Search knowledge bundle via BM25 lexical scoring or path-scoped governance matching.
  - `def show(concept_id, bundle_dir) -> dict[str, Any] | None` — Retrieve full concept record by id.
  - `def create(concept_id, title, concept_type, description, body, governance, code_refs, bundle_dir) -> dict[str, Any]` — Create a new concept with sanitized frontmatter and auto-synced bookkeeping.
  - `def update(concept_id, title, description, body, governance, code_refs, bundle_dir) -> dict[str, Any]` — Update an existing concept file and sync bookkeeping.
  - `def relate(source_id, target_id, description, bundle_dir) -> dict[str, Any]` — Bidirectionally relate two concepts in frontmatter.
  - `def validate(strict, bundle_dir) -> dict[str, Any]` — Validate knowledge bundle against OKF normative schema and trust ordering rules.
- `class OKFMemoryPlugin` — Harness Plugin providing Open Knowledge Framework (OKF v0.2) memory governance services.
  - `def __init__(engine) -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def okf_search(query, for_path, limit, bundle_dir) -> OKFSearchResult`
  - `def okf_search_async(query, for_path, limit, bundle_dir) -> OKFSearchResult`
  - `def okf_show(concept_id, bundle_dir) -> OKFConceptRecord | None`
  - `def okf_show_async(concept_id, bundle_dir) -> OKFConceptRecord | None`
  - `def okf_create(concept_id, title, concept_type, description, body, governance, code_refs, bundle_dir) -> OKFConceptRecord`
  - `def okf_create_async(concept_id, title, concept_type, description, body, governance, code_refs, bundle_dir) -> OKFConceptRecord`
  - `def okf_update(concept_id, title, description, body, governance, code_refs, bundle_dir) -> OKFConceptRecord`
  - `def okf_update_async(concept_id, title, description, body, governance, code_refs, bundle_dir) -> OKFConceptRecord`
  - `def okf_relate(source_id, target_id, description, bundle_dir) -> dict[str, Any]`
  - `def okf_relate_async(source_id, target_id, description, bundle_dir) -> dict[str, Any]`
  - `def okf_validate(strict, bundle_dir) -> OKFValidationReport`
  - `def okf_validate_async(strict, bundle_dir) -> OKFValidationReport`


#### Functions

- `def okf_search(query, for_path, limit, bundle_dir) -> dict[str, Any]` — Search knowledge bundle using BM25 lexical ranking or evaluate for-path governance constraints.
- `def okf_show(concept_id, bundle_dir) -> dict[str, Any]` — Retrieve full markdown content, frontmatter metadata, and governance rules for a specific concept.
- `def okf_create(concept_id, title, concept_type, description, body, governance, code_refs, bundle_dir) -> dict[str, Any]` — Create a new concept document with frontmatter sanitization and automatic parent index updating.
- `def okf_update(concept_id, title, description, body, governance, code_refs, bundle_dir) -> dict[str, Any]` — Update an existing concept document with automatic parent index and audit log synchronization.
- `def okf_relate(source_id, target_id, description, bundle_dir) -> dict[str, Any]` — Link two concepts together bidirectionally in frontmatter relations.
- `def okf_validate(strict, bundle_dir) -> dict[str, Any]` — Validate knowledge bundle against OKF normative schema, link consistency, and actor trust ordering.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.okf_memory.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
