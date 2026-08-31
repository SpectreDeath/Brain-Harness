# Transcript-Trajectory Debugging Pattern

## Problem
CI failures and build errors trigger immediate re-runs, wasting time and compute. The root cause is often already visible in prior agent tool trajectories.

## Solution
Before re-executing a failing command:
1. Query the brain_bridge for the failing job's transcript steps.
2. Inspect `RUN_COMMAND` and `PLANNER_RESPONSE` entries for the exact error output and attempted fixes.
3. Identify whether the failure is deterministic (same error every run) or environmental (flaky).

## Operational Guideline
Treat transcript JSONL as a first-class debug artifact. When `brain_query` returns trajectory steps for a failed command, extract the error text and recovery attempts before taking action.

## Provenance
- Source brain: `antigravity_core`
- Primary source: `4fcad908-fa51-4c99-add7-f65810123566.system_generated/logs/transcript.jsonl#L89`
- Distilled from: CI failure analysis (exit code 4, pytest-asyncio compatibility), CLI validation output inspection