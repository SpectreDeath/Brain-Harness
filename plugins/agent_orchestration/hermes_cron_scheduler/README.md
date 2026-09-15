# domain.hermes_cron_scheduler (v1.0.0)

Hermes unattended natural language cron scheduler, incident classification, and blueprint catalog manager

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/agent_orchestration/hermes_cron_scheduler` |
| Category | `agent_orchestration` |
| Isolation Mode | `in_process` |
| Services Provided | `service.hermes_cron_scheduler` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `schedule_natural_cron` | `(schedule_expr, prompt_action, target_channel)` | Register a recurring unattended schedule using natural language or cron expression |
| `list_cron_jobs` | `(status_filter)` | Query active, paused, or completed cron jobs |
| `inspect_cron_incidents` | `(job_id, limit)` | Retrieve execution incident reports and error diagnostics for cron tasks |
| `manage_blueprint_catalog` | `(action, blueprint_id)` | Query or instantiate curated unattended automation blueprints |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Hermes Cron Scheduler — natural language unattended automation and incident lifecycle.

#### Functions

- `def schedule_natural_cron(schedule_expr, prompt_action, target_channel) -> dict[str, Any]` — Register a new scheduled job with normalized cron expression.
- `def list_cron_jobs(status_filter) -> dict[str, Any]` — List registered cron jobs matching filter.
- `def inspect_cron_incidents(job_id, limit) -> dict[str, Any]` — Inspect incident logs for scheduled automations.
- `def manage_blueprint_catalog(action, blueprint_id) -> dict[str, Any]` — Browse or instantiate pre-configured cron blueprints.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.hermes_cron_scheduler.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
