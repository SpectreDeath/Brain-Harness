# Multi-Store Autobiographical Memory Federation

## Metadata
- **KI ID**: `ki_self_20260901_01`
- **Source Target**: `C:\Users\spectre\.gemini\antigravity-ide\conversations`
- **Format**: `antigravity_ide_autobiographical_store`
- **Timestamp**: `2026-09-01T17:35:00Z`
- **Status**: `VERIFIED`

## Distilled Learning
# KI: Multi-Store Autobiographical Memory Federation

## Operational Summary
Antigravity IDE maintains two distinct storage layers for session execution:
1. **Binary SQLite ACID Stores (`.db`)**: Holds structured tables (`trajectory_meta`, `steps`, `gen_metadata`, `executor_metadata`, `trajectory_metadata_blob`) managed with Write-Ahead Logging (WAL) and shared memory (`.db-shm`, `.db-wal`) by active worker proactors.
2. **Streaming JSONL Transcripts (`transcript.jsonl`)**: Holds append-only, human-readable line-delimited records in the brain trajectory directory.

When extracting endogenous memories or conducting introspective reflection loops across active IDE sessions, attempting direct write or exclusive locking connections against `.db` files can cause SQLite locking contention (`sqlite3.OperationalError: database is locked`). Agents must unconditionally connect using read-only URI mode (`sqlite3.connect('file:' + path + '?mode=ro', uri=True)`) and stream JSONL step lines for large historical trajectory audits.

## Invariant Rule
Always federate memory queries across read-only SQLite URIs and streaming JSONL parsers; never execute synchronous blocking writes or acquire write locks on active conversation databases during agent reflection.

## Primary Lineage
- **Assertion**: Antigravity IDE partitions session state into ACID SQLite WAL databases (.db) and streaming JSONL step logs (transcript.jsonl). Agents querying SQLite databases during active sessions must use explicit read-only URI mode (file:...?mode=ro) to eliminate lock contention with live IDE worker proactors while federating streaming JSONL parsers for multi-turn step transcripts.
  - `primary_code`: `C:/Users/spectre/.gemini/antigravity-ide/conversations/e3aff7ce-7b79-49e4-93c5-030d20470a89.db` (Verified: True)
  - `primary_code`: `C:/Users/spectre/.gemini/antigravity-ide/brain/e3aff7ce-7b79-49e4-93c5-030d20470a89/.system_generated/logs/transcript.jsonl` (Verified: True)
  - `visual_brief`: `C:/Users/spectre/AppData/Local/Temp/harness-reflection-20260901-173500.html` (Verified: True)
