# plugin.agentwikis (v1.0.0)

AgentWikis knowledge discovery, boundary triage, and offline documentation slicing

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/integration_and_io/agentwikis` |
| Category | `integration_and_io` |
| Isolation Mode | `in_process` |
| Services Provided | `service.agentwikis` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `agentwikis_list` | `(category, tag, query)` | List wikis filtered by category, tag, or text query |
| `agentwikis_scope` | `(wiki)` | Inspect declared scope boundaries, exclusions, and freshness date for a wiki |
| `agentwikis_match` | `(query, limit)` | Match user task prompt to in-scope wikis and skills with calibrated abstention |
| `agentwikis_search` | `(query, wiki, limit)` | Search documentation corpus across documents and metadata with calibrated confidence |
| `agentwikis_read` | `(doc_path, section, remote)` | Extract exact Markdown document or sub-section slice offline or with remote fallback |
| `agentwikis_pack` | `(query, max_tokens)` | Prepare a one-shot token-bounded Markdown context pack ready for LLM injection |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

AgentWikis Plugin — IoC Micro-Kernel Provider for Documentation, Boundary Triage & Knowledge Slicing.

#### Classes

- `class AgentWikisPlugin` — Harness Plugin providing AgentWikis documentation, triage, and offline slicing capabilities.
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def list_wikis(category, tag, query) -> list[WikiEntity]` — List wikis filtered by category, tag, or text query.
  - `def get_scope(wiki_slug) -> WikiScope | None` — Get declared scope and boundaries for a specific wiki.
  - `def match_intent(query, limit) -> MatchResult` — Evaluate task intent against wiki scopes and skills with calibrated abstention.
  - `def search(query, wiki, limit) -> tuple[SearchHit, ...]` — Search documentation corpus with calibrated confidence.
  - `def extract_document(doc_path, section_heading, force_remote) -> DocumentSlice` — Extract exact Markdown document section offline or via remote fallback.
  - `def prepare_context_pack(query, max_tokens) -> str` — One-shot intent triage, document retrieval, and token-bounded context assembly.
  - `def validate_contract(contract_path) -> ContractValidationReport` — Validate corpus against Open Data Contract (ODCS) schema (Stage 2).
  - `def generate_visual_brief(output_path, query, wiki_slug) -> Path` — Generate interactive HTML visual brief with Mermaid DAG and blast radius (Stage 3).
  - `def profile_data_quality(min_passing_score) -> QualityScorecard` — Run DAMA-DMBOK 6-dimension data quality profiling across corpus (Stage 4).


#### Functions

- `def get_engine() -> AgentWikisEngine` — Returns singleton instance of AgentWikisEngine.
- `def agentwikis_list(category, tag, query) -> list[dict[str, Any]]` — List wikis filtered by category, tag, or text query.
- `def agentwikis_scope(wiki) -> dict[str, Any] | None` — Inspect declared scope boundaries, exclusions, and freshness date for a wiki.
- `def agentwikis_match(query, limit) -> dict[str, Any]` — Match user task prompt to in-scope wikis and skills with calibrated abstention.
- `def agentwikis_search(query, wiki, limit) -> list[dict[str, Any]]` — Search documentation corpus across documents and metadata with calibrated confidence.
- `def agentwikis_read(doc_path, section, remote) -> dict[str, Any]` — Extract exact Markdown document or sub-section slice offline or with remote fallback.
- `def agentwikis_pack(query, max_tokens) -> str` — Prepare a one-shot token-bounded Markdown context pack ready for LLM injection.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.integration_and_io.agentwikis.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
