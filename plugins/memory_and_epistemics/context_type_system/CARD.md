# Context Type System Plugin — Summary Card

## Archetype & Invariants

- **Archetype**: `service_provider` + `tool_provider`
- **Isolation**: `in_process` (zero subprocess IPC overhead, pure Python typed verification)
- **IoC Service Key**: `ServiceKey[ContextTypeService]("service.context_type_system")`

```
+-------------------------------------------------------------------------+
|                         ALLOWED TRANSITIONS                             |
|                                                                         |
|  [ TOOL_OUTPUT ] ───( validate_tool_result )───> [ EVIDENCE ]           |
|                                                         │               |
|                                                         ▼ ( transform ) |
|                                                    [ MEMORY ]           |
|                                                                         |
|  [ INSTRUCTION ] <─── PROTECTED CHANNEL (Direct promotion blocked)      |
+-------------------------------------------------------------------------+
```

## Mandatory Invariants

1. **Origin Immutability**: The provenance ledger records the channel of first observation. Future attempts to re-add the same normalized text into `INSTRUCTION` without an approved transform are rejected with `ContextTypeError`.
2. **Derivation Traceability**: Transformed items maintain explicit `derived_from` request IDs, enabling multi-hop DAG traversal (`get_lineage`) back to the origin observation.
3. **Session Encapsulation**: Context stores are strictly partitioned by `session_id`, with full snapshot export/import fidelity.
4. **Token Budget Determinism**: Prompts respect token ceilings (`max_tokens`) and channel quotas, dropping lower-priority items deterministically.

## Tool Registry

| Tool | Signature | Purpose |
|---|---|---|
| `context_add` | `(session_id, context_type, content, source?, priority?)` | Register typed item; enforce ledger invariants |
| `context_transform` | `(session_id, request_id, to_type, source?)` | Transition item across allowed boundary |
| `context_validate_tool_output` | `(session_id, tool_request_id, strict_mode?)` | Validate and elevate tool output to evidence |
| `context_assemble_prompt` | `(session_id, section_order?, custom_labels?, max_tokens?, channel_quotas?)` | Render structured semantic prompt with token budgeting |
| `context_inspect_ledger` | `(session_id, filter_type?)` | Audit provenance records and item ledger |
| `context_get_lineage` | `(session_id, request_id)` | Trace multi-hop Isnad derivation chain back to root |
| `context_export_session` | `(session_id)` | Export session state as portable snapshot |
| `context_import_session` | `(session_id, data)` | Restore session state from snapshot dictionary |
