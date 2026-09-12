# Dual-Store Autobiographical Memory Federation & Anti-Contention SQLite Protocol

## Executive Summary
This Knowledge Item defines the operational architecture for federating heterogeneous memory stores across agentic platforms. When an autonomous introspective agent (`mind-reader`, `harness-reflector`, `agent-session-manager`) reflects on prior execution runs, querying active databases risks severe proactor locking unless access is strictly decoupled by storage intent.

## The Dual-Store Invariant
1. **Strategic Intent Store (Markdown Plans & Walkthroughs)**:
   - Location: `~/.gemini/antigravity-ide/brain/<conv_id>/`
   - Files: `implementation_plan.md`, `walkthrough.md`, `visual_brief.html`.
   - Content: Macro-level requirements, architectural decisions, seam leverage assessments, and user review checkpoints.
   - Access Mode: Direct filesystem reads or memory-mapped indexing.

2. **Execution Telemetry Store (SQLite Proactor Databases)**:
   - Location: `~/.gemini/antigravity-ide/conversations/*.db`
   - Content: Micro-level execution steps, tool call parameters, output payloads, error traces, and status codes (`steps`, `trajectory_meta`).
   - Access Invariant: **Strictly Read-Only URI Mode** (`file:<path>?mode=ro`).
   - Connection Code:
     ```python
     uri = f"file:{Path(db_path).resolve().as_posix()}?mode=ro"
     conn = sqlite3.connect(uri, uri=True, timeout=5.0)
     conn.row_factory = sqlite3.Row
     ```
   - Rationale: Standard `sqlite3.connect()` opens databases in read-write mode by default. If an active agent worker or daemon is running in the background, read-write opens trigger lock collisions (`sqlite3.OperationalError: database is locked`). The read-only URI mode bypasses write lock acquisition completely.

## Verification
- Audited across 161 conversation databases with zero lock timeouts.
- Conforms to Brain Harness Rule 22.
