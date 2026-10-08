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

## Architecture & Subpackage Decomposition

The OKF memory plugin engine is partitioned into dedicated domain submodules under `engine/` for single-responsibility isolation, while maintaining a lean backward-compatible facade in `main.py`:

- **[engine/utils.py](engine/utils.py)**: Path normalization (`_normalize_path`), traversal guards (`_ensure_within_root`), tokenization (`_tokenize`), and YAML frontmatter extraction/serialization (`_extract_frontmatter`, `_serialize_concept`).
- **[engine/search.py](engine/search.py)**: BM25 lexical ranking engine with term frequency boosting, corpus document frequency calculations, and path-scoped governance constraint evaluation (`execute_search`).
- **[engine/crud.py](engine/crud.py)**: Atomic concept CRUD operations (`execute_create`, `execute_update`, `execute_relate`, `execute_show`) with automatic parent `index.md` table regeneration and append-only `log.md` audit synchronization (`sync_index_and_log`).
- **[engine/validation.py](engine/validation.py)**: Normative OKF v0.2 bundle schema validation, broken relation checks, and actor trust ordering invariant enforcement (`execute_validate`).
- **[engine/core.py](engine/core.py)**: Coordinator `OKFMemoryEngine` unifying storage operations, lexical ranking, and governance evaluations.
- **[main.py](main.py)**: Lean coordinator facade re-exporting public symbols, defining Click/runtime tool entrypoints (`okf_search`, `okf_show`, `okf_create`, `okf_update`, `okf_relate`, `okf_validate`), implementing `OKFMemoryPlugin(HarnessPlugin, OKFMemoryService)`, and exporting module singleton `plugin` (Rule 45).

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

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.okf_memory.main import plugin, OKFMemoryEngine

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)

# Direct engine usage
engine = OKFMemoryEngine()
results = engine.search(query="rate limiting")
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), zero-fork YAML configuration (Rule 44), and single-source plugin exports (Rule 45).
