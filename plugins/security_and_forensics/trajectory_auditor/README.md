# domain.trajectory_auditor (v1.0.0)

Agent trajectory step auditor, repetitive loop / stuck detector, and recovery prompt synthesizer

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/security_and_forensics/trajectory_auditor` |
| Category | `security_and_forensics` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `audit_trajectory_steps` | `(steps)` | Analyze an agent's execution history for repeated tool failures, excessive step counts, and inefficiency |
| `detect_repetitive_loop` | `(actions, window_size)` | Detect cyclic repetition in agent action sequences (e.g. A -> B -> A -> B) |
| `synthesize_recovery_prompt` | `(stuck_reason, last_failed_action)` | Generate an intervention prompt to break an agent out of a stuck loop or error cycle |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Agent trajectory step auditor, stuck loop detector, and recovery prompt synthesizer plugin.

#### Functions

- `def audit_trajectory_steps(steps) -> dict[str, Any]` — Audit agent step history for failures, token usage, and inefficiencies.
- `def detect_repetitive_loop(actions, window_size) -> dict[str, Any]` — Detect repeating cycles in action sequences (e.g. A -> B -> A -> B).
- `def synthesize_recovery_prompt(stuck_reason, last_failed_action) -> dict[str, Any]` — Generate an intervention prompt to break an agent out of a loop or error cycle.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.security_and_forensics.trajectory_auditor.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
