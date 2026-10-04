# Dual-Store Autobiographical Memory Federation Architecture

## Problem
In IDE-integrated agent development, developmental state accumulates in two distinct locations:
1. `conversations/<cid>.db` — Relational SQLite databases storing step execution records, executor telemetry, and protobuf payloads under active SQLite WAL journaling.
2. `brain/<cid>/` — Filesystem-native workspace folders storing user-facing artifacts (`implementation_plan.md`, `walkthrough.md`), on-the-fly Python tools (`scratch/*.py`), subprocess execution logs (`.system_generated/tasks/`), and dual transcripts (`transcript.jsonl` / `transcript_full.jsonl`).

Attempting to build a single monolithic miner violates single-responsibility:
- Opening `conversations/*.db` in standard mode causes lock contention with active IDE proactors.
- Attempting to query `brain/` via SQLite fails because filesystem artifacts are not in the SQLite schema.
- Trying to force filesystem tool archaeology into relational trajectory analysis leads to architectural incoherence.

## Solution
Federate autobiographical memory into two single-responsibility, bounded domain skills:
1. `conversation-trajectory-miner`:
   - Enforces read-only SQLite URI mode (`file:{path}?mode=ro`, Rule 22).
   - Extracts step-type frequency distributions, retry loops, and defect densities.
   - Falls back to `conversations/<cid>.db` when `brain/<cid>/` hits protection boundaries (Rule 46).
2. `brain-artifact-miner`:
   - Bounded filesystem traversal (depth $\le 3$, Rule 52).
   - AST classification of 1,000+ scratch scripts into 7 functional domains (Rule 42).
   - Ring-buffer stderr triage of background subprocess logs (Rule 53).
   - Automatic dereferencing of `is_truncated: true` compact transcript steps to untruncated reasoning in `transcript_full.jsonl` (Rule 22).

This separation of concerns honors Rule 20 (In-Place Deepening over Tool Sprawl) by recognizing distinct data topologies, preventing lock contention, and maximizing capability salvage.

## Provenance
- `AGENTS.md` (Rules 20, 22, 40, 41, 46, 52, 53)
- `.agents/skills/conversation-trajectory-miner/`
- `.agents/skills/brain-artifact-miner/`
