# Zero-Dependency Prometheus Text Exposition Architecture & Observability Seams

## Epistemic Seam (Mental Models & Heuristics)
1. **Zero-Dependency Exposition**: Rather than coupling to external client libraries that introduce heavy dependencies and transitive constraints, standard Prometheus version 0.0.4 text format can be generated directly using Python standard library data structures.
2. **Cumulative Bucket Pre-Computation**: In Prometheus histograms, each bucket `le` represents the cumulative count of observations less than or equal to that bucket boundary. Recording observations directly into all applicable buckets during `observe()` enables $O(1)$ read formatting during scrape requests.
3. **Thread Safety Invariant**: In multi-agent swarms where concurrent threads execute steps and record token counters simultaneously, metric dictionaries must be guarded by `threading.Lock()` to prevent race conditions and dictionary mutation crashes.

## Procedural Seam (Integration Architecture)
1. **Slotted Dataclasses (Rule 12)**: `MetricDefinition` and `MetricSample` are declared with `slots=True, frozen=True` to guarantee immutability and minimal memory footprint.
2. **Non-Invasive Route Injection (Rule 19)**: The `/metrics` endpoint is injected directly into `create_app()` within `src/harness/ui/server/app.py` resolving `PROMETHEUS_EXPORTER_SERVICE_KEY`, leaving core application contracts intact.
3. **Plugin Staging**: `PrometheusExporterPlugin` provides `PROMETHEUS_EXPORTER_SERVICE_KEY` and co-locates `config.default.yaml` for scrape interval and bucket configurations.
