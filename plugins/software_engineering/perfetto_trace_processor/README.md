# Google Perfetto Trace Processor Plugin

SQL trace analysis, metric calculation, and flame graphs.


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `perfetto_load_trace` | `(trace_path, verbose)` | Load and parse a system trace file (.perfetto-trace, .pftrace, Chrome/Android trace) |
| `perfetto_query_sql` | `(trace_id, sql_query)` | Execute arbitrary SQL queries against trace tables (e.g. 'SELECT name, dur, ts FROM slice') |
| `perfetto_compute_metrics` | `(trace_id, metrics_list)` | Compute standard trace metric summaries (CPU scheduling latency, thread execution times) |
| `perfetto_export_flamegraph` | `(trace_id, focus_thread)` | Produce structured execution stacks and flame graph summaries from trace slices |
