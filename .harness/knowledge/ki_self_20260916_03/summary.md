# In-Memory Mock Fallback Schema Parity Invariant

## Executive Summary
This Knowledge Item defines the **In-Memory Mock Fallback Schema Parity Invariant** (Rule 55), codifying the requirement that in-memory simulation engines in Harness plugins must exhibit full dictionary schema parity with live CLI and REST network payloads.

## Architectural Mechanics
1. **The Mock Schema Drift Friction**:
   - In accordance with **Rule 7** (Lazy Subprocess Staging) and zero-dependency developer loop speed, Harness service implementations provide deterministic in-memory fallback modes when third-party binaries (`orca`, `docker`, Paperless-NGX servers) are absent from CI or developer machines.
   - When authors implement `send_message` or `post_document` in-memory branches, they often record a simplified dictionary subset (e.g. only `id`, `subject`, `to`, `body`).
   - Downstream consumers (such as `coordinate_worker` or `ingest_and_await_document`) that inspect the mailbox for structured fields (`files_modified`, `report_path`, `document_type`) fail to resolve those keys, falling back to empty tuples `()` or defaults.
   - This causes contract assertions (e.g. `assert len(settlement.files_modified) > 0`) to fail loudly during unit testing, despite the code logic being sound.
2. **The Parity Invariant**:
   - In-memory mock record builders must map 100% of the input configuration fields to the internal dictionary representation:
     ```python
     record = {
         "id": msg_id,
         "subject": config.subject,
         "to": config.to,
         "body": config.body,
         "type": config.message_type,
         "taskId": config.task_id,
         "dispatchId": config.dispatch_id,
         "outcome": config.outcome,
         "files_modified": config.files_modified,
         "report_path": config.report_path,
         "timestamp": time.time(),
     }
     ```
   - Both snake_case and camelCase alias resolutions must be supported during dictionary unpacking (`msg.get("files_modified") or msg.get("filesModified")`) to match varying JSON serializers across external ecosystems.

## Verifiable Isnad Lineage
- **Grounding Implementations**:
  - `plugins/agent_orchestration/orca_bridge/service.py:L328-L344`
  - `tests/test_orca_bridge_plugin.py:L200-L220` (`test_orca_coordinate_worker_deep_seam`)
  - Commit `1b72bad`
- **Governing Rules**: `AGENTS.md` Rule 12 (Slotted Models), Rule 28 (Forensic Mock Isolation), Rule 33 (JSON Null-Field Fallback), Rule 55 (Mock Schema Parity Invariant).
