# Agora Workbench: Data Lake Policy Enforcement & Streaming Object Transfer

## Overview
- **Source Repository**: `https://github.com/microsoft/agora-workbench` (`a8ae030b`)
- **Primary Files**:
  - `src/agora_workbench/data_lake/policy.py#L50-L280`
  - `src/agora_workbench/code_execution/object_transfer.py#L45-L245`

## Core Architecture & Invariants
1. **Strict Policy Mode Parity (`PolicyEnforcedCatalogProvider.__init__`)**: `CatalogPolicyMode.PER_ARTIFACT` mandates a non-None `per_artifact_enforcer`, whereas `HOMOGENEOUS_SOURCE` forbids attaching one, preventing silent security mode confusion.
2. **Cursor Scope Binding (`_constrain_request`)**: Effective `source_ids` are intersected with caller permissions and provider capabilities *before* query execution. If a pagination `cursor` is supplied when `effective_sources != requested_sources`, an `InvalidRequestError` forces the client to restart pagination safely.
3. **Non-Enumerable Denial Masking (`get` / `resolve`)**: Unauthorized source or artifact lookups call `_raise_not_found(operation)` instead of leaking existence via distinct permission errors.
4. **Bounded Streaming Envelopes (`object_transfer.py`)**: Enforces `MAX_TRANSFER_SIZE_BYTES = 256 * 1024 * 1024`, `_MAX_STREAMING_ENVELOPE_BYTES = 64 * 1024`, strict `STREAMING_TRANSFER_VERSION = "2"` equality, `_CORRELATION_ID_RE`, duplicate JSON key rejection (`_reject_duplicate_streaming_keys`), and 4-byte aligned incremental base64 decoding.

## Decision Heuristics & Anti-Patterns
- **Never allow pagination cursors to outlive a change in authorized source scope**.
- **Never distinguish unauthorized from nonexistent artifacts in read/resolve error responses**.
- **Never parse JSON envelopes using last-key-wins semantics on streaming transfer prefixes/suffixes**.
