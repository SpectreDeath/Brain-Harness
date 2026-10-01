# Harness CLI Commands Reference (`harness.commands`)

The `harness.commands` package provides pure async and synchronous command handlers powering the Brain Harness Click CLI entrypoint (`harness`). Each module encapsulates a single command group, delegating domain logic to underlying kernel services and IoC container protocols.

---

## Overview & Architecture

Commands are strictly decoupled from Click CLI option parsers:
- **Pure Async Entrypoints**: Command modules define reusable functions (`cmd_*`) that accept typed arguments or options, allowing programmatic invocation from scripts or test fixtures without shell spawning.
- **IoC Service Resolution**: Command handlers instantiate or connect to the `HarnessRuntime`, resolve typed `ServiceKey[T]` instances from the context, and execute transactional workflows.
- **Rule 6 Single-Source Consolidation**: CLI command groups (e.g. `@main.group("bridge")`) are declared exactly once in a single co-located block in [`cli.py`](../cli.py) to prevent later definitions from shadowing subcommands and breaking CLI test assertions.
- **Rule 10 Headless Introspection Seams**: All runtime execution trees, session transcripts, and context compilation graphs expose headless Click CLI inspection and export commands.

---

## Command Groups & Modules

### 1. Agent Execution & Sessions
| Module | Command Group | Purpose & Capabilities |
|---|---|---|
| [`agent.py`](agent.py) | `harness run`, `harness step` | Autonomous ReAct agent task execution and interactive single-step debugging. |
| [`session.py`](session.py) | `harness session` | Agent execution session transcripts, state inspection, and DAG tree export (`harness session tree`). |
| [`context.py`](context.py) | `harness context` | Pre-LLM context compilation, AST RepoMap injection, and prompt pruning. |
| [`compute.py`](compute.py) | `harness compute` | Model tier assessment, reasoning budget allocation, and provider routing. |
| [`model_router.py`](model_router.py) | `harness model-router` | Sub-5ms query complexity classification and dynamic multi-provider failover. |
| [`calibrator.py`](calibrator.py) | `harness calibrator` | Context staging calibration (T0-T4) and action space benchmarking. |
| [`harness_architect.py`](harness_architect.py) | `harness architect` | 5-part harness auditing, 4-mechanism reliability scoring, and stack analysis. |
| [`compass.py`](compass.py) | `harness compass` | Autonomous agent harness benchmarking and constrained evolution. |
| [`self_eval.py`](self_eval.py) | `harness self-eval` | Deterministic prompt evaluation pipelines and gold-standard assertions. |
| [`validation_loop.py`](validation_loop.py) | `harness validation-loop`| Spec-first deterministic validation loop execution and HTML report generation. |
| [`uncertainty.py`](uncertainty.py) | `harness uncertainty` | 3-layer uncertainty gating, retrieval similarity scoring, and logprob validation. |

### 2. Plugins & Capability Creation
| Module | Command Group | Purpose & Capabilities |
|---|---|---|
| [`plugins.py`](plugins.py) | `harness plugin` | Plugin lifecycle management (`list`, `enable`, `disable`, `info`, `inspect`). |
| [`creator.py`](creator.py) | `harness creator` | Dynamic plugin scaffolding, archetype validation, and AST auto-remediation. |
| [`skills.py`](skills.py) | `harness skills` | Skill Knowledge Graph queries, topological shortest-path chaining, and skill authoring. |
| [`tools.py`](tools.py) | `harness tools` | Granular tool registry inspection, tool testing, and execution sandboxing. |
| [`mcp.py`](mcp.py) | `harness mcp` | Model Context Protocol (MCP) server launching, tool discovery, and JSON-RPC bridging. |
| [`gate.py`](gate.py) | `harness gate` | Security and verification gate evaluations for production deployments. |
| [`pre_commit_security.py`](pre_commit_security.py) | `harness security` | Pre-commit security interceptor executing DevSkim SAST and Gitleaks rules. |

### 3. Documentation, Data & Ingestion
| Module | Command Group | Purpose & Capabilities |
|---|---|---|
| [`doc.py`](doc.py) | `harness doc` | AST documentation coverage auditing, stale symbol detection, and link drift checking. |
| [`doc_builder.py`](doc_builder.py) | `harness doc-builder` | HF doc-builder compilation, AST anchor graphs, and zero-dependency mock loading. |
| [`data.py`](data.py) | `harness data` | Data profiling, schema migration, and relational database execution. |
| [`datasets.py`](datasets.py) | `harness datasets` | Arrow zero-copy memory mapping and streaming pipelines for large datasets. |
| [`bigquery.py`](bigquery.py) | `harness bigquery` | BigQuery in-database augmented analytics via TVFs and causal inference. |
| [`garf.py`](garf.py) | `harness garf` | Declarative SQL reporting pipelines and analytical workflow execution. |
| [`gis.py`](gis.py) | `harness gis` | Geospatial processing across 14 GIS engines with CRS safety verification. |
| [`okf.py`](okf.py) | `harness okf` | Open Knowledge Framework (OKF v0.2) Git-native episodic memory governance. |

### 4. System, Bridges & Runtime
| Module | Command Group | Purpose & Capabilities |
|---|---|---|
| [`runtime.py`](runtime.py) | `harness runtime` | Runtime lifecycle diagnostics, database migrations, and health checks. |
| [`system.py`](system.py) | `harness system` | Host environment diagnostics, venv health, and hardware telemetry. |
| [`events.py`](events.py) | `harness events` | Immutable event bus inspection, filtering, and streaming replay. |
| [`workspace.py`](workspace.py) | `harness workspace` | Workspace initialization, configuration validation, and cache management. |
| [`watch.py`](watch.py) | `harness watch` | Autonomous file watcher daemon monitoring triggers for hot-reloading. |
| [`reflection.py`](reflection.py) | `harness reflect` | Endogenous autobiographical memory distillation and isnad claim audits. |
| [`antigravity.py`](antigravity.py) | `harness antigravity` | Headless inspection for proactor policies, execution gates, and runtime telemetry. |
| [`bridges.py`](bridges.py) | `harness bridge` | Ecosystem connector diagnostics (Em-Cubed, Memtext, Skill Flywheel). |
| [`tau.py`](tau.py) | `harness tau` | Tau coding harness bridge diagnostics and session imports. |
| [`gemini_vercel.py`](gemini_vercel.py) | `harness vercel` | Streaming chatbot deployment configurations and CORS verification. |
| [`gradio_app.py`](gradio_app.py) | `harness gradio` | Gradio web application deployment and block event graph auditing. |
| [`network_forensics.py`](network_forensics.py) | `harness forensics` | Packet capture dissection, TCP flag analysis, and network isolation verification. |
| [`_utils.py`](_utils.py) | — | Internal helper functions for formatted console output and error handling. |

---

## CLI Usage Examples

### Running an Autonomous Task
```bash
harness run "Audit codebase documentation coverage and detect stale links"
```

### Exporting Execution Session Trees
```bash
# Export hierarchical ASCII DAG tree of agent execution steps
harness session tree <session_id>

# Export full session transcript JSON
harness session export <session_id> --output transcript.json
```

### Querying Skill Knowledge Graph
```bash
# Find optimal skill execution chain between two domain capabilities
harness skills chain --from code-review --to tdd
```

### Auditing Documentation Coverage
```bash
# Audit AST documentation coverage across the workspace
harness doc audit --root . --min-coverage 95.0
```

---

## Related Documentation

- [CLI Reference Guide](../../../docs/reference/cli.md)
- [Kernel Architecture](../kernel/README.md)
- [User Manual](../../../USER_MANUAL.md)
