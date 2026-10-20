```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:        cloud-infrastructure-architect           │
│ Category:     infra_and_cloud                          │
│ Invocation:   /cloud-infrastructure-architect          │
│ Triggers:     "prometheus", "metrics", "cloud infra",  │
│               "terraform drift", "container telemetry" │
│ Version:      1.0.0                                    │
│ Isolation:    subprocess                               │
│ Provides:     "service.prometheus_exporter"            │
├────────────────────────────────────────────────────────┤
│ Target:       Architect cloud observability, Prometheus│
│               metric exposition, and containerized     │
│               sandboxing telemetry.                    │
└────────────────────────────────────────────────────────┘
```

# Cloud Infrastructure Architect — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
| --- | --- | --- | --- |
| **1. Metric Schema** | Define counter, gauge, and histogram metric schemas | `metrics_schema.json` | Valid metric name and allowed type |
| **2. Seam Instrumentation**| Emit observations from execution loop hotspots | `sample_traces.json` | Zero latency regression at call sites |
| **3. Text Exposition** | Format metrics into Prometheus 0.0.4 text syntax | `metrics.prom` | Valid `# HELP`, `# TYPE`, and sample lines |
| **4. Scrape Route** | Expose `/metrics` route on control server | `http_response.txt` | HTTP 200 with text/plain exposition format |

---

## Mandatory Invariants Checklist

- [ ] **Thread Safety Invariant**: The metric registry must use `threading.Lock()` to prevent race conditions across parallel threads.
- [ ] **Counter Monotonicity Invariant**: Counter increments must be strictly non-negative ($v \ge 0$).
- [ ] **Prometheus Syntax Invariant**: Output must strictly conform to Prometheus version 0.0.4 text format specification.
- [ ] **Slotted Immutability Invariant**: Metric definitions and samples must adhere to `@dataclass(slots=True, frozen=True)` schemas.
