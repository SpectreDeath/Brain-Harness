# plugin.context_course_bridge (v1.0.0)

Hugging Face Context Engineering Bridge: 6-layer stack auditor, FastMCP validator, subagent swarm planner, and sandboxed Nano Harness ReAct loop

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/agent_orchestration/context_course_bridge` |
| Category | `agent_orchestration` |
| Isolation Mode | `in_process` |
| Services Provided | `service.context_course` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `audit_context_surface` | `(project_dir)` | Audit a project workspace against the 6-layer context engineering stack (Skills, MCP, Plugins, Subagents, Hooks, Nano Harness) |
| `run_nano_harness` | `(task, workspace_root, max_steps)` | Execute a sandboxed, path-confined minimal ReAct agentic step loop |
| `verify_context_snippets` | `(markdown_text)` | Parse and syntax-validate all fenced code snippets in markdown instructions |
| `plan_subagent_topology` | `(files_count, task_type)` | Plan optimal subagent coordination topology using the 10+ files heuristic |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Hugging Face Context Engineering Bridge: 6-layer stack auditor, FastMCP validator, subagent swarm planner, and sandboxed Nano Harness ReAct loop

#### Classes

- `class ContextCourseBridgePlugin` — Plugin providing 6-layer context engineering, FastMCP, and Nano Harness capabilities.
  - `def __init__(root_dir)` — Executes the operation.
  - `def name()` — Executes the operation.
  - `def version()` — Executes the operation.
  - `def description()` — Executes the operation.
  - `def provides()` — Executes the operation.
  - `def requires()` — Executes the operation.
  - `def on_load(context)` — Register the service singleton in the IoC container (Rule 45).
  - `def on_unload(context)` — Clean up on plugin unload.
  - `def audit_context_surface(project_dir)` — Audit project directory against the 6-layer context engineering stack.
  - `def run_nano_harness(task, workspace_root, max_steps)` — Execute a sandboxed, path-confined minimal ReAct agentic step loop.
  - `def verify_context_snippets(markdown_text)` — Parse and syntax-validate all fenced code snippets in markdown instructions.
  - `def plan_subagent_topology(files_count, task_type)` — Plan optimal subagent coordination topology using the 10+ files heuristic.

---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.context_course_bridge.main import plugin

context = ServiceContext()
# Load plugin into service context
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
