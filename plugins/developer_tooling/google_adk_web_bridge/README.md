# Google ADK Web Bridge Plugin

Connects Harness telemetry with ADK Web UI & A2UI graphs.


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `adk_web_status` | `(project_dir)` | Inspect ADK web dashboard build artifacts, Angular configurations, and dependencies |
| `adk_web_export_graph` | `(nodes, edges, format)` | Convert Harness agent execution DAG into A2UI / ngx-vflow interactive node graph JSON |
| `adk_web_start_dev_server` | `(port, poll_interval)` | Generate configuration command and launch specification for ADK Web UI dev server |
