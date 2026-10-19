# Subprocess Venv Staging & Adversarial GenAI Red-Teaming Architecture

## Epistemic Seam (Mental Models & Heuristics)
1. **Lazy Subprocess Staging (Rule 7)**: Third-party security and red-teaming frameworks often require heavy or conflict-prone packages (e.g., Azure AI SDKs, legacy ML dependencies). Rather than bloating the core harness virtual environment or causing pip dependency conflicts, security extensions remain in a `DISCOVERED/VALIDATED` state and execute within dedicated external subprocess venvs.
2. **Deterministic Fallback Simulation**: For fast headless CI and developer environments where the external venv has not yet been provisioned, services must provide bounded deterministic simulation modes returning structured `VulnerabilityScorecard` data without throwing import errors.
3. **Loopback Preservation Invariant (Rule 56)**: When sandboxing subprocess network access, the runner must explicitly preserve local loopback connections (`127.0.0.1`, `localhost`, `::1`) to allow internal IPC pipes and proactor event loops on Windows to function properly.

## Procedural Seam (Integration Architecture)
1. **Slotted Immutable Schemas (Rule 12)**: `RedTeamTarget`, `AttackVector`, and `VulnerabilityScorecard` are implemented as frozen slotted dataclasses with construction-time range validation.
2. **Click CLI Introspection (Rule 10)**: Headless CLI commands (`harness redteam scan`, `harness redteam techniques`, `harness redteam status`) provide operators with immediate access to probe results and scorecard metrics.
3. **Pipe Drainage Invariant (Rule 14)**: Asynchronous subprocess pipes are drained into a ring buffer and closed within `finally` blocks to guarantee clean resource disposal across operating systems.
