# Reactive Wakeup Triggers & Non-Polling Background Events

**ID:** `ki_antigravity_004`  
**Category:** `agent_orchestration`  
**Origin:** `google-antigravity-sdk`  
**Provenance Lineage:** `google/antigravity/triggers/trigger_runner.py`, `google/antigravity/triggers/helpers.py`

## Executive Summary
Antigravity's trigger system provides reactive scheduling through async event queues rather than CPU-intensive polling loops. Triggers support time intervals (`every(seconds=...)`) and filesystem modification notifications (`on_file_change(path=...)`), allowing background daemons to awaken agent sessions on actionable external changes without thread sleep.

## Architectural Invariants & Rules
1. Triggers must never execute synchronous sleep loops or busy-waiting in the main thread.
2. Filesystem watcher triggers must debounce rapid sequential edits to prevent event storms.
3. Trigger notifications must pass through async queues to awaken agent step loops reactively.
