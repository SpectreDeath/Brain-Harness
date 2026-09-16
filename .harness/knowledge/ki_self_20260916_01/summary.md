# Atomic Asynchronous Task Settlement Seam Invariant

## Executive Summary
This Knowledge Item documents the foundational architectural pattern for eliminating shallow pass-through wrappers around asynchronous task queues (e.g., Git worktree mailboxes in Orca, Celery ingestion pipelines in Paperless-NGX). It defines the **Atomic Asynchronous Task Settlement Seam Invariant** (Rule 53), which mandates providing high-leverage atomic settlement seams that absorb queue polling, backoff, and entity hydration.

## Architectural Mechanics
1. **The Shallow Fire-and-Forget Friction**:
   - When a plugin exposes only raw submission commands (`post_document`, `start_worker`), it returns a transient identifier (`task_id` or `dispatch_id`).
   - Every external caller (ReAct step loop, agent supervisor, CLI script) is forced to duplicate 15–25 lines of boilerplate: sleeping, checking status, filtering 15-second keepalive pulses, auto-acknowledging message delivery batches, and parsing output strings to find generated document IDs.
2. **The Atomic Settlement Seam**:
   - Provide high-leverage coordination methods (`coordinate_worker`, `ingest_and_await_document`) that absorb the entire asynchronous lifecycle behind an atomic, non-blocking invocation.
   - The seam encapsulates:
     1. Worktree provisioning or temporary upload dispatch.
     2. Context namespace binding (run ID, coordinator inbox).
     3. Non-blocking polling with bounded exponential backoff up to `timeout_seconds`.
     4. Keepalive heartbeat filtering to prevent mailbox flooding.
     5. Automatic ACK acknowledgment of consumed delivery batches.
     6. Automated entity hydration (extracting document IDs and querying full `DocumentSummary` records).
     7. Construction and return of a slotted, frozen settlement model (`OrcaTaskSettlement`, `IngestionReceipt`, Rule 12).
3. **Backward Compatibility Guarantee**:
   - Maintain the raw fire-and-forget submission methods for callers explicitly seeking detached asynchronous execution.

## Verifiable Isnad Lineage
- **Grounding Implementations**:
  - `plugins/agent_orchestration/orca_bridge/service.py:L362-L475` (`coordinate_worker`)
  - `src/harness/services/paperless_ngx.py:L400-L470` (`ingest_and_await_document`)
  - Commit `1b72bad`
- **Governing Rules**: `AGENTS.md` Rule 8 (Transactional Isolation), Rule 12 (Slotted Models), Rule 41 (Epistemic Isnad Audit), Rule 53 (Task Settlement Invariant).
