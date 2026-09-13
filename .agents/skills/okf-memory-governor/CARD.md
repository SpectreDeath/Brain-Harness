```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:        okf-memory-governor                      │
│ Category:     memory_and_epistemics                    │
│ Invocation:   /okf-memory-governor                     │
│ Triggers:     "okf memory", "memory governance",       │
│               "scope code path", "audit memory",       │
│               "bm25 knowledge search"                  │
│ Version:      1.0.0                                    │
│ Isolation:    subprocess                               │
│ Provides:     "service.okf_memory"                     │
├────────────────────────────────────────────────────────┤
│ Target:       Govern Git-native agent memory bundles,  │
│               enforce pre-edit code path scoping,      │
│               and validate normative OKF schemas.      │
└────────────────────────────────────────────────────────┘
```

# OKF Memory Governor — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
| --- | --- | --- | --- |
| **1. Pre-Edit Scoping** | Query knowledge bundle for path-scoped concepts before modifying source code | `governance_scope.json` | `Target code paths checked against code_refs and governance rules extracted` |
| **2. BM25 Search** | Sub-millisecond lexical search with governance boost and progressive disclosure | `search_results.json` | `Relevant concepts identified without blanket directory scanning` |
| **3. Atomic Mutation** | Create or update concepts with scalar sanitization and auto-bookkeeping | `concept_record.md` | `Concept written within root boundary and parent index/log updated` |
| **4. Relation Linking** | Link concepts bidirectionally in frontmatter with resolved target validation | `relations_graph.json` | `Bidirectional relations updated with zero dangling targets` |
| **5. Normative Validation** | Validate bundle against schema requirements and actor trust ordering | `validation_report.json` | `Bundle validation passes with zero errors and zero warnings` |

---

## Input & Output Schema Specification

### Input Schema

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `action` | string | Required | Operational action (`scope`, `search`, `show`, `create`, `update`, `relate`, `validate`) |
| `target_path` | string | Optional | Source file path to evaluate for governance scoping |
| `query` | string | Optional | Search query terms for BM25 lexical ranking |
| `concept_id` | string | Optional | Unique concept identifier for inspection or mutation |
| `limit` | integer | Optional | Maximum search results to return (default: 3) |
| `strict` | boolean | Optional | Whether to enforce zero-warning strict validation |

### Output Schema

| Field | Type | Description |
| --- | --- | --- |
| `status` | string | Execution status (`ok`, `error`) |
| `results_count` | integer | Number of matching concepts returned |
| `results` | array | List of ranked concept summaries with scores and governance |
| `valid` | boolean | Validation status indicator |
| `errors` | array | Critical normative validation failures |
| `warnings` | array | Non-blocking hygiene and schema warnings |

---

## Mandatory Invariants Checklist

- [ ] **Path Scoping Invariant**: Always execute `okf_search(for_path=...)` before proposing edits to files referenced in `code_refs`.
- [ ] **Anti-Blanket Scan Invariant**: Never run `list_dir` or `grep` on `knowledge/`; always use lexical BM25 with `limit <= 3`.
- [ ] **Trust Ordering Invariant**: Agent models must never self-attest as `human:` in verification metadata.
- [ ] **Path Traversal Invariant**: Target paths must resolve strictly within the designated bundle root directory.
- [ ] **Automatic Bookkeeping Invariant**: Concept mutations must automatically synchronize parent `index.md` tables and `log.md` ledgers.
