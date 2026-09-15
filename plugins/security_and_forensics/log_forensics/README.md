# domain.log_forensics (v1.0.0)

High-throughput SIEM log stream parser, anomaly detection, and incident timeline reconstructor

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/security_and_forensics/log_forensics` |
| Category | `security_and_forensics` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `parse_log_stream` | `(log_content, format_hint)` | Parse raw text log stream (Syslog, JSONL, Apache/Nginx, or standard key-value) into structured records |
| `detect_log_anomalies` | `(log_events)` | Detect attack patterns (brute force, 4xx/5xx spikes, privilege escalation, suspicious IPs) in parsed logs |
| `build_incident_timeline` | `(log_events)` | Sort and synthesize a chronological incident timeline with severity tagging |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Log Forensics and SIEM stream analyzer plugin for Brain Harness.

#### Functions

- `def parse_log_stream(log_content, format_hint) -> dict[str, Any]` — Parse raw log lines into structured event dictionaries.
- `def detect_log_anomalies(log_events) -> dict[str, Any]` — Inspect structured logs for attack patterns and anomalies.
- `def build_incident_timeline(log_events) -> dict[str, Any]` — Reconstruct an incident timeline from event logs.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.security_and_forensics.log_forensics.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
