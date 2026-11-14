# Python 3.10 Matrix Compatibility: `datetime.timezone.utc` Gate

## Root Cause Observed
- On CI run `43628036027` (`sha=627a09a`), 6 of 7 jobs passed (`Ruff`, `Frontend Build & Lint`, Python 3.11 on Ubuntu/macOS/Windows, and Python 3.12 on Ubuntu).
- Only `Test Suite (ubuntu-latest, Python 3.10)` failed during pytest collection with `266` errors (`ImportError: cannot import name 'UTC' from 'datetime'`), because `src/harness/services/__init__.py` eagerly imports `src/harness/services/graphiti_zep_memory.py`, which imported `UTC` (added in Python 3.11).

## Mandatory Invariant
- Always import `from datetime import datetime, timezone` and pass `timezone.utc` instead of `UTC` in `src/harness/`, `plugins/`, and `.agents/skills/*/scripts/`.
- Verified via commit `c8bebbe` (`run_id=43629131238`, 7/7 CI matrix jobs `success`).
