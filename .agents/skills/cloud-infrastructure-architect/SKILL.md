---
name: cloud-infrastructure-architect
description: Architect cloud infrastructure, container sandboxing governance, and Prometheus metrics exposition across hybrid runtime environments. Do not use for generic web development or raw ad-hoc database administration.
---

# Cloud Infrastructure Architect

The Cloud Infrastructure Architect governs infrastructure design, container sandboxing, and runtime observability across multi-cloud and edge deployments. It standardizes telemetry pipelines using Prometheus exposition patterns and enforces deterministic infrastructure-as-code state synchronization.

## Operational Workflow

1. **Telemetry Topology Design**: Establish metric naming conventions, label dimensionality, and histogram bucket boundaries.
2. **Exposition Pipeline Wiring**: Expose standard `/metrics` endpoints and integrate thread-safe counters, gauges, and timers into execution hotspots.
3. **Container Sandboxing Auditing**: Audit container runtime boundaries, rootless daemon configs, and read-only filesystem mounts.
4. **Drift Telemetry Synthesis**: Aggregate infrastructure metrics and synthesize alert thresholds for anomaly detection.

## Anti-Patterns

- **High-Cardinality Label Explosion** — Injecting unbounded user IDs or dynamic timestamps directly into metric label dimensions.
- **Unbounded Histogram Bucketing** — Creating dozens of dense histogram buckets that cause excessive memory footprint on scrapers.
- **Unbuffered Metric Emitting** — Emitting metrics synchronously over blocking network sockets during hot path agent step execution.

## Diagnostic Verification

Verify telemetry generation using `harness.services.prometheus.DefaultPrometheusExporterService` or the plugin tools `prometheus_record_metric` and `prometheus_get_text_metrics`.
