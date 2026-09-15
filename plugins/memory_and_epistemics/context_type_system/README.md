# plugin.context_type_system (v1.1.0)

Context provenance, type channel separation, origin ledger verification, token budgeting, and prompt assembly engine

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/memory_and_epistemics/context_type_system` |
| Category | `memory_and_epistemics` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `context_add` | `(session_id, context_type, content, source, priority)` | Register a typed context item into a session, checking origin ledger against protected channels |
| `context_transform` | `(session_id, request_id, to_type, source)` | Explicitly transition a context item across permitted policy boundaries, recording derivation lineage |
| `context_validate_tool_output` | `(session_id, tool_request_id, strict_mode)` | Validate raw tool execution output and elevate it to evidence if passing validation criteria |
| `context_assemble_prompt` | `(session_id, section_order, custom_labels, max_tokens, channel_quotas)` | Render typed context items into ordered prompt sections with optional token budgeting and channel quotas |
| `context_inspect_ledger` | `(session_id, filter_type)` | Audit provenance records, origin types, transition history, and ledger keys for a context session |
| `context_get_lineage` | `(session_id, request_id)` | Trace the full multi-hop derivation chain back to the root observation (Isnad lineage audit) |
| `context_export_session` | `(session_id)` | Export session state as a portable snapshot dictionary |
| `context_import_session` | `(session_id, data)` | Restore a session from a snapshot dictionary |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Context Type System Plugin & HarnessPlugin Service Implementation.

#### Classes

- `class ContextTypeSystemPlugin` — Harness Plugin implementing ContextTypeService and registering CONTEXT_TYPE_SYSTEM_KEY.
  - `def __init__() -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def add_context(session_id, context_type, content, source, priority) -> ContextAddResult`
  - `def transform_context(session_id, request_id, to_type, source) -> ContextTransformResult`
  - `def validate_tool_output(session_id, tool_request_id, strict_mode) -> ContextValidateResult`
  - `def assemble_prompt(session_id, section_order, custom_labels, max_tokens, channel_quotas) -> ContextPromptResult`
  - `def inspect_ledger(session_id, filter_type) -> ContextLedgerResult`
  - `def get_lineage(session_id, request_id) -> ContextLineageResult`
  - `def export_session(session_id) -> ContextSnapshotResult`
  - `def import_session(session_id, data) -> ContextSnapshotResult`


#### Functions

- `def context_add(session_id, context_type, content, source, priority) -> dict[str, Any]` — Register a typed context item into a session, checking origin ledger against protected channels.
- `def context_transform(session_id, request_id, to_type, source) -> dict[str, Any]` — Explicitly transition a context item across permitted policy boundaries, recording derivation lineage.
- `def context_validate_tool_output(session_id, tool_request_id, strict_mode) -> dict[str, Any]` — Validate raw tool execution output and elevate it to evidence if passing validation criteria.
- `def context_assemble_prompt(session_id, section_order, custom_labels, max_tokens, channel_quotas) -> dict[str, Any]` — Render typed context items into ordered prompt sections with token budgeting and channel quotas.
- `def context_inspect_ledger(session_id, filter_type) -> dict[str, Any]` — Audit provenance records, origin types, transition history, and ledger keys for a context session.
- `def context_get_lineage(session_id, request_id) -> dict[str, Any]` — Trace the full multi-hop derivation chain back to the root observation (Isnad lineage audit).
- `def context_export_session(session_id) -> dict[str, Any]` — Export session state as a portable snapshot dictionary.
- `def context_import_session(session_id, data) -> dict[str, Any]` — Restore a session from a snapshot dictionary.

### Module [__init__.py](__init__.py)

Context Type System Plugin for Brain Harness.
### Module [engine.py](engine.py)

Core engine for Context Type System provenance, ledger verification, token budgeting, and prompt assembly.

#### Classes

- `class ContextType` — Semantic context channel types.
- `class ContextTypeError` — Raised when an illegal context type transition or channel insertion occurs.
- `class ContextItem` — A typed unit of context with provenance metadata.
  - `def describe() -> str`
  - `def estimate_tokens(char_per_token) -> int` — Estimate token cost of this item's text content.
  - `def to_dict() -> dict[str, Any]`
  - `def from_dict(cls, data) -> ContextItem`
- `class ContextObserver` — Observer protocol for monitoring context lifecycle events.
  - `def on_item_added(item) -> None`
  - `def on_item_transformed(old_item, new_item) -> None`
  - `def on_rejection(context_type, content, reason) -> None`
- `class BudgetConfig` — Configuration for token budgeting across context channels.
- `class ContextAssembler` — Groups typed context items by channel into a structured, token-budgeted prompt.
  - `def assemble(items, section_order, custom_labels, max_tokens, channel_quotas) -> str`
  - `def assemble_detailed(items, section_order, custom_labels, max_tokens, channel_quotas, char_per_token) -> dict[str, Any]` — Assemble prompt with token budgeting, channel allocation quotas, and pruning telemetry.
- `class ContextStore` — Runtime boundary enforcing provenance, type channel protection, and O(1) indexed lookups.
  - `def __init__() -> None`
  - `def add_observer(observer) -> None` — Register a lifecycle observer.
  - `def add_context(context_type, content, source, priority, _via_transform, _derived_from) -> ContextItem`
  - `def transform(item, to_type, source) -> ContextItem` — Explicitly move content across an allowed boundary.
  - `def get_item(request_id) -> Optional[ContextItem]` — O(1) indexed item lookup.
  - `def get_lineage(request_id) -> List[ContextItem]` — Trace the full multi-hop derivation chain back to the root observation (Isnad audit).
  - `def items() -> List[ContextItem]`
  - `def items_of_type(context_type) -> List[ContextItem]`
  - `def get_ledger() -> List[dict[str, str]]`
  - `def export_state() -> dict[str, Any]` — Export internal state to a serializable dictionary.
  - `def from_dict(cls, data) -> ContextStore` — Construct a ContextStore from a serialized snapshot.
- `class ContextSessionManager` — Manages independent ContextStore sessions by session_id with snapshot persistence.
  - `def __init__() -> None`
  - `def get_session(session_id) -> ContextStore`
  - `def reset_session(session_id) -> None`
  - `def list_sessions() -> List[str]`
  - `def export_session(session_id) -> dict[str, Any]` — Export session state as a portable snapshot.
  - `def import_session(session_id, data) -> None` — Restore a session from a snapshot dictionary.


#### Functions

- `def transition_allowed(from_type, to_type) -> bool` — Check whether explicit transition between two context channels is allowed.
- `def validate_tool_result(store, tool_item, strict_mode) -> ContextItem` — Promote a TOOL_OUTPUT item to EVIDENCE with validation checking.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.context_type_system.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
