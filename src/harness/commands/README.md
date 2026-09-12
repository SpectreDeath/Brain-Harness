# Harness CLI Commands Reference (`harness.commands`)

The `harness.commands` package provides pure async and synchronous command handlers powering the Brain Harness Click CLI entrypoint (`harness`). Each module encapsulates a single command group, delegating domain logic to underlying kernel services and IoC container protocols.

---

## Overview & Architecture

Commands are decoupled from Click CLI option parsers:
- **Pure Async Entrypoints**: Command modules define reusable functions (`cmd_*`) that accept typed arguments or options, allowing programmatic invocation from scripts or test fixtures without shell spawning.
- **IoC Service Resolution**: Command handlers instantiate or connect to the `HarnessRuntime`, resolve typed `ServiceKey[T]` instances from the context, and execute transactional workflows.
- **Rule 6 Compliance**: Subcommands are consolidated into single-source command groups (`main.py` and `cli.py`) to prevent subcommand shadowing.

---

## Command Groups & Modules

| Module | Command Group | Purpose & Capabilities |
|---|---|---|
| [`agent.py`](agent.py) | `harness run`, `harness step` | Autonomous ReAct agent task execution and interactive single-step debugging. |
| [`antigravity.py`](antigravity.py) | `harness antigravity` | Headless inspection for proactor policies, execution gates, and runtime telemetry. |
| [`bridges.py`](bridges.py) | `harness bridge` | Ecosystem connector diagnostics (Em-Cubed, Memtext, Skill Flywheel). |
| [`compute.py`](compute.py) | `harness compute` | Model tier assessment, reasoning budget allocation, and provider routing. |
| [`context.py`](context.py) | `harness context` | Pre-LLM context compilation, AST RepoMap injection, and prompt pruning. |
| [`creator.py`](creator.py) | `harness creator` | Dynamic plugin scaffolding, archetype validation, and AST auto-remediation. |
| [`data.py`](data.py) | `harness data` | Data profiling, schema migration, and relational database execution. |
| [`events.py`](events.py) | `harness events` | Immutable event bus inspection, filtering, and streaming replay. |
| [`mcp.py`](mcp.py) | `harness mcp` | Model Context Protocol (MCP) server launching, tool discovery, and JSON-RPC bridging. |
| [`plugins.py`](plugins.py) | `harness plugin` | Plugin lifecycle management (`list`, `enable`, `disable`, `info`, `inspect`). |
| [`reflection.py`](reflection.py) | `harness reflect` | Endogenous autobiographical memory distillation and isnad claim audits. |
| [`runtime.py`](runtime.py) | `harness runtime` | Runtime lifecycle diagnostics, database migrations, and health checks. |
| [`session.py`](session.py) | `harness session` | Agent execution session transcripts, state inspection, and DAG tree export (`harness session tree`). |
| [`skills.py`](skills.py) | `harness skills` | Skill Knowledge Graph queries, topological shortest-path chaining, and skill authoring. |
| [`system.py`](system.py) | `harness system` | Host environment diagnostics, venv health, and hardware telemetry. |
| [`tools.py`](tools.py) | `harness tools` | Granular tool registry inspection, tool testing, and execution sandboxing. |
| [`watch.py`](watch.py) | `harness watch` | Autonomous file watcher daemon monitoring triggers for hot-reloading. |
| [`workspace.py`](workspace.py) | `harness workspace` | Workspace initialization, configuration validation, and cache management. |
| [`_utils.py`](_utils.py) | — | Internal helper functions for formatted console output and error handling. |

---

## Usage Examples

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
harness skills chain structured-data-scout survival-analysis
```

---

## Related References
- [Harness Kernel Runtime](../kernel/README.md)
- [Harness Service Architecture](../services/README.md)
- [Plugin System Architecture](../plugins/README.md)
