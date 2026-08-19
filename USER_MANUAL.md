# Brain Harness — User Manual & Reference Guide

```
  ██████╗ ██████╗  █████╗ ██╗███╗   ██╗    ██╗  ██╗ █████╗ ██████╗ ███╗   ██╗███████╗███████╗███████╗
  ██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║    ██║  ██║██╔══██╗██╔══██╗████╗  ██║██╔════╝██╔════╝██╔════╝
  ██████╔╝██████╔╝███████║██║██╔██╗ ██║    ███████║███████║██████╔╝██╔██╗ ██║█████╗  ███████╗███████╗
  ██╔══██╗██╔══██╗██╔══██║██║██║╚██╗██║    ██╔══██║██╔══██║██╔══██╗██║╚██╗██║██╔══╝  ╚════██║╚════██║
  ██████╔╝██║  ██║██║  ██║██║██║ ╚████║    ██║  ██║██║  ██║██║  ██║██║ ╚████║███████╗███████║███████║
  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝╚══════╝
```

> **A modular, autonomous agent harness where *everything* is a plugin.**

---

## Table of Contents

1. [Introduction & Core Philosophy](#1-introduction--core-philosophy)
2. [Architecture Overview](#2-architecture-overview)
3. [Installation & Workspace Setup](#3-installation--workspace-setup)
4. [CLI Operations Manual](#4-cli-operations-manual)
   - [Workspace Initialization](#workspace-initialization)
   - [Plugin Ingestion & Management](#plugin-ingestion--management)
   - [Running Autonomous Agents](#running-autonomous-agents)
   - [Interactive Web Control Room](#interactive-web-control-room)
   - [Creator Mode (Dynamic Plugin Scaffolding)](#creator-mode-dynamic-plugin-scaffolding)
   - [Runtime Introspection & Diagnostics](#runtime-introspection--diagnostics)
   - [Model Context Protocol (MCP) Server](#model-context-protocol-mcp-server)
   - [Ecosystem Bridge Status](#ecosystem-bridge-status)
   - [Immutable Event Stream Auditing](#immutable-event-stream-auditing)
5. [Plugin Developer Guide](#5-plugin-developer-guide)
   - [Plugin Structure & Manifest (`plugin.json`)](#plugin-structure--manifest-pluginjson)
   - [Writing Python In-Process Plugins](#writing-python-in-process-plugins)
   - [Typed Services & `ServiceKey[T]`](#typed-services--servicekeyt)
   - [Registering Tools for Autonomous Agents](#registering-tools-for-autonomous-agents)
6. [Ingestion & Sandbox Security](#6-ingestion--sandbox-security)
   - [Automatic Ingestion Pipeline](#automatic-ingestion-pipeline)
   - [Subprocess & Virtualenv Sandboxing](#subprocess--virtualenv-sandboxing)
7. [Ecosystem Bridges](#7-ecosystem-bridges)
   - [Em-Cubed (Neuro-Symbolic Surfaces)](#em-cubed-neuro-symbolic-surfaces)
   - [Memtext (Persistent Memory & Decision Audit)](#memtext-persistent-memory--decision-audit)
   - [Skill Flywheel (Domain Skill Catalog)](#skill-flywheel-domain-skill-catalog)
   - [MCP Client Plugin (External Tool Servers)](#mcp-client-plugin-external-tool-servers)
8. [Python SDK & Programmatic Usage](#8-python-sdk--programmatic-usage)
9. [Configuration & Troubleshooting](#9-configuration--troubleshooting)

---

## 1. Introduction & Core Philosophy

**Brain Harness** is an unopinionated, enterprise-grade agent execution environment engineered with a strict **micro-kernel architecture**.

Rather than shipping a rigid, pre-packaged bundle of hardcoded domain tools, **Harness is a blank cognitive canvas**. By ingesting your own repositories, custom tools, ZIP archives, and agent skills, **your harness becomes a direct reflection of your brain**—tailored precisely to your domain, workflows, and thinking.

### Key Tenets
- **Everything is a Plugin:** Models, tools, memory, storage engines, execution surfaces, and agent loops are all plugins registered into a unified Inversion of Control (IoC) container. No agent capability is hardcoded into the kernel.
- **Your Brain, Your Harness:** Harness starts clean. You feed it GitHub URLs, local projects, or ZIP files (`harness plugin add <source>`), and the ingestion pipeline dynamically inspects, sandboxes, and mounts them into your personal runtime.
- **Typed Service Keys:** All service registration, dependency injection, and resolution use typed `ServiceKey[T]` tokens rather than fragile raw strings.
- **Transactional Lifecycle Management:** Plugins declare their dependencies (`requires`) and capabilities (`provides`). The lifecycle manager topologically sorts dependencies and ensures zero service leakage on plugin disabling or unloading.
- **Subprocess Isolation by Default:** Ingested external code or untrusted tools execute in isolated subprocess sandboxes communicating via JSON-RPC over standard input/output (`stdin`/`stdout`).
- **Agent Skill Knowledge Graph:** Declarative skill cards (`CARD.md` / `SKILL.md`) are automatically indexed into a directed knowledge graph, enabling autonomous multi-step skill chaining, semantic intent routing, and pre-commit failure-mode mitigation.
- **Immutable Event Stream:** All system transitions, tool executions, agent reasoning steps, and errors are appended to an immutable audit log.

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                 CLI & Web Dashboard                              │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                  Harness Runtime                                 │
│  ┌──────────────────────┬──────────────────────┬──────────────────────────────┐  │
│  │   ServiceContext     │   PluginLifecycle    │          EventBus            │  │
│  │  (Typed IoC Kernel)  │  (Topological Graph) │   (Append-Only Telemetry)    │  │
│  └──────────────────────┴──────────────────────┴──────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────────────────┤
│                              Core Service Plugins                                │
│   • LLM Service (LiteLLM / OpenAI / Anthropic / Local)                           │
│   • Tool Registry & Dynamic Dispatch Table                                       │
│   • SQLite Key-Value Storage                                                     │
│   • Autonomous ReAct Agent Loop Service                                          │
├──────────────────────────────────────────────────────────────────────────────────┤
│                              Ecosystem Bridges                                   │
│   • Em-Cubed (Prolog, Z3, Datalog, Hy, SQLite surfaces)                          │
│   • Memtext (Persistent memory & decision auditing)                              │
│   • Skill Flywheel (Catalog of 800+ domain skills)                               │
│   • MCP Client & Server (Model Context Protocol)                                 │
├──────────────────────────────────────────────────────────────────────────────────┤
│                          Ingestion & Sandbox Engine                              │
│   • GitHub / ZIP / Local Ingestion Engine                                        │
│   • StdioJsonRpcTransport & Isolated Subprocess Sandboxes                        │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Installation & Workspace Setup

### Prerequisites
- Python **≥ 3.10** (Python 3.11, 3.12, 3.13 fully supported)
- Git (optional, for fetching GitHub plugins)

### Installation
Clone the repository and install with development dependencies:

```bash
git clone https://github.com/your-org/brain-harness.git
cd "brain-harness"
pip install -e ".[dev]"
```

### Initializing a New Workspace
Create an empty workspace or initialize the current working directory:

```bash
harness init .
```

This scaffolds the standard directory layout:
```
my-workspace/
├── plugins/              # Drop-in folder for custom / ingested plugins
└── .harness/
    ├── config.json       # Workspace configuration
    ├── events.jsonl      # Immutable event stream audit log
    └── storage.db        # Persistent SQLite storage
```

---

## 4. CLI Operations Manual

Brain Harness includes a comprehensive command-line interface: `harness`.

### Workspace Initialization
```bash
harness init [PATH]
```
Initializes a new directory with `plugins/` and `.harness/` configuration.

---

### Plugin Ingestion & Management

#### Ingest a Plugin from GitHub or ZIP
```bash
# Ingest from a remote GitHub repository
harness plugin add https://github.com/owner/repo-name

# Ingest from a local directory or ZIP file
harness plugin add ./my-plugin.zip
```
The ingestion engine automatically inspects the repository, synthesizes missing manifests, isolates external dependencies, and registers the plugin in `plugins/`.

#### List Installed Plugins
```bash
harness plugin list
```
Displays all detected plugins, their versions, current lifecycle state (`ENABLED`, `LOADED`, `DISABLED`), and provided services.

#### Inspect Plugin Details
```bash
harness plugin inspect plugins/my-tool
```
Outputs manifest metadata, security trust level, isolation mode, declared entrypoints, and parameter schemas.

#### Enable / Disable / Remove Plugins
```bash
harness plugin enable <plugin-name>
harness plugin disable <plugin-name>
harness plugin remove <plugin-name>
```

---

### Running Autonomous Agents

Harness includes an autonomous **ReAct (Reasoning + Acting)** agent loop service.

```bash
harness agent run "Analyze the project structure and summarize the core modules."
```

#### Options:
- `--max-steps <N>`: Maximum reasoning steps (default: `10`).
- `--model <MODEL_NAME>`: LLM model identifier (default: `gpt-4o-mini` or configured environment model).

#### Execution Flow:
1. Agent initializes the micro-kernel and activates all available tools (built-in, sandboxed, and ecosystem bridges).
2. Decomposes task into thought $\rightarrow$ action $\rightarrow$ observation iterations.
3. Invokes tools with strict JSON schema validation.
4. Returns structured `AgentTaskResult` with complete step-by-step reasoning and final answer.

---

### Interactive Web Control Room

Launch the real-time web dashboard to monitor plugins, inspect the IoC container, view live event telemetry over WebSockets, and trigger agent tasks:

```bash
harness ui --host 127.0.0.1 --port 8080
```
Open [http://127.0.0.1:8080](http://127.0.0.1:8080) in any modern web browser.

---

### Creator Mode (Dynamic Plugin Scaffolding)

Creator Mode allows instant scaffolding and dynamic authoring of new plugin packages:

```bash
harness creator build data_cleaner --description "CSV and JSON cleaning utilities" --target-dir plugins/data_cleaner
```
Generates a complete, ready-to-run plugin template with `plugin.json` and `main.py`.

---

### Runtime Introspection & Diagnostics

Inspect the live runtime dependency graph, registered services, active providers, and tool endpoints:

```bash
harness introspect
```

#### Output Example:
```
🔍 System Introspection Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Active Plugins (6):
  • core.storage              [enabled]
  • core.tools                [enabled]
  • core.llm                  [enabled]
  • bridge.em_cubed           [enabled]
  • bridge.memtext            [enabled]
  • bridge.flywheel           [enabled]

Registered Services (4):
  • storage.service           (provided by: core.storage)
  • tools.registry            (provided by: core.tools)
  • llm.service               (provided by: core.llm)
  • memory.provider           (provided by: memory.memtext)

Available Tools (14):
  • surface.python
  • surface.prolog
  • surface.sqlite
  • memory.store
  • memory.recall
  ...

📊 Mermaid Dependency Graph:
graph TD
  core_tools["core.tools"] --> core_storage["core.storage"]
  ...
```

---

### Skill Knowledge Graph & Autonomous Chaining

Harness indexes structured agent skills (`.agents/skills/` and plugin directories) into an in-memory directed knowledge graph with semantic intent routing, shortest-path chain synthesis, and anti-pattern defense:

```bash
# Display the graph and emit an interactive HTML Visual Brief in %TEMP%
harness skills graph --visual

# Route natural language intent to matching skills and recommended execution chains
harness skills route "fetch wine dataset from UCI and profile distribution"

# Compute the directed execution path between two skills
harness skills chain structured-data-scout questio-reflection

# Inspect topological dependencies, handoffs, and mitigated anti-patterns for a skill
harness skills info questio-reflection
```

---

### Model Context Protocol (MCP) Server

Harness can act as an **MCP Server**, exposing all internal plugins, sandboxes, and ecosystem surfaces to external AI coding agents (Claude Code, Cursor, Windsurf, Gemini, etc.) over standard I/O:

```bash
harness mcp serve
```

---

### Ecosystem Bridge Status

Verify connectivity to neighbor ecosystem repositories:

```bash
harness bridge status
```
Checks `Em-Cubed`, `Memtext`, and `Skill Flywheel` directory locations, environment variables, and module availability.

---

### Immutable Event Stream Auditing

Inspect the chronological append-only event stream:

```bash
# View all recent events
harness events

# Filter by event type
harness events --type tool.invoked
```

---

## 5. Plugin Developer Guide

### Plugin Structure & Manifest (`plugin.json`)

A standard plugin directory contains at least a manifest (`plugin.json`) and an entry script (`main.py` or `plugin.py`):

```
plugins/weather_tool/
├── plugin.json
└── main.py
```

#### Example `plugin.json`:
```json
{
  "name": "weather_tool",
  "version": "1.0.0",
  "description": "Fetch real-time weather reports for autonomous agents",
  "entrypoint": "main.py",
  "isolation": "subprocess",
  "trusted": false,
  "entrypoints": [
    {
      "name": "get_weather",
      "description": "Get current weather for a city",
      "parameters": [
        {
          "name": "city",
          "type": "string",
          "description": "City name (e.g. San Francisco)",
          "required": true
        },
        {
          "name": "units",
          "type": "string",
          "description": "Temperature units (celsius or fahrenheit)",
          "required": false
        }
      ]
    }
  ]
}
```

#### Example `main.py`:
```python
def get_weather(city: str, units: str = "celsius") -> str:
    """Entry function invoked by the sandbox via JSON-RPC."""
    return f"Weather in {city}: 21° {units.capitalize()}, Clear skies."
```

---

### Writing Python In-Process Plugins

Trusted in-process plugins inherit directly from [`HarnessPlugin`](file:///d:/GitHub/projects/Brain%20Harness/src/harness/plugins/base.py):

```python
from __future__ import annotations
from typing import Any
from harness.plugins.base import HarnessPlugin
from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry

CALC_SERVICE_KEY: ServiceKey[CalculatorService] = ServiceKey("math.calculator")

class CalculatorService:
    def add(self, a: int, b: int) -> int:
        return a + b

class CalculatorPlugin(HarnessPlugin):
    @property
    def name(self) -> str:
        return "custom.calculator"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [CALC_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return [TOOL_REGISTRY_KEY]

    async def on_load(self, ctx: ServiceContext) -> None:
        # Register the service in the scoped context
        ctx.provide(CALC_SERVICE_KEY, CalculatorService())

    async def on_enable(self) -> None:
        # Mount tools into ToolRegistry
        tool_reg: ToolRegistry = self.context.require(TOOL_REGISTRY_KEY)
        calc: CalculatorService = self.context.require(CALC_SERVICE_KEY)

        tool_reg.register(
            name="math.add",
            description="Add two integers",
            executor=calc.add,
            provider=self.name,
        )

    async def on_disable(self) -> None:
        # Cleanup happens automatically via ScopedServiceContext
        pass

    async def on_unload(self) -> None:
        pass
```

---

## 6. Ingestion & Sandbox Security

Brain Harness guarantees process isolation for third-party, GitHub-sourced, and untrusted plugins.

### Isolation Modes
1. **`subprocess` (Default for untrusted plugins):** Runs in a separate child process. Input and output are exchanged via strict JSON-RPC 2.0 messages over standard I/O pipes managed by [`StdioJsonRpcTransport`](file:///d:/GitHub/projects/Brain%20Harness/src/harness/plugins/transport.py).
2. **`venv` (Virtual Environment):** Creates an isolated Python virtualenv, installs the repository's dependencies (`requirements.txt` or `pyproject.toml`), and runs the subprocess inside the isolated environment.
3. **`in_process` (Explicitly trusted plugins only):** Runs within the host Python process for maximum execution speed.

---

## 7. Ecosystem Bridges

Brain Harness includes first-class connectors to the wider forensic simulation and neuro-symbolic ecosystem:

| Bridge | Description | Key Services & Tools |
|---|---|---|
| **Em-Cubed** | Polyglot neuro-symbolic OS | `bridge.em_cubed`, `surface.python`, `surface.prolog`, `surface.z3`, `surface.sqlite` |
| **Memtext** | Persistent agent memory & audit | `memory.provider`, `memory.store`, `memory.recall` |
| **Skill Flywheel** | Catalog of 800+ domain skills | `bridge.flywheel`, `skill.<skill_id>` |
| **MCP Client** | External Model Context Protocol tools | `mcp.<server_name>`, `mcp.<server>.<tool_name>` |

---

## 8. Python SDK & Programmatic Usage

Embed Brain Harness into your own Python applications, services, or test pipelines:

```python
import asyncio
from harness.kernel.runtime import HarnessRuntime
from harness.services.llm import LLM_SERVICE_KEY, LiteLLMService

async def main():
    # Create runtime instance with in-memory storage and standard plugins
    async with HarnessRuntime.create(db_path=":memory:") as runtime:
        # Run an autonomous task
        result = await runtime.run_task(
            "Find all python files in the current workspace and count their lines."
        )

        print(f"Task Status: {result.status}")
        print(f"Total Steps: {len(result.steps)}")
        print(f"Final Answer:\n{result.final_answer}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 9. Configuration & Troubleshooting

### Workspace Configuration (`.harness/config.json`)

```json
{
  "version": "0.1.0",
  "plugin_dirs": [
    "plugins",
    "custom_plugins"
  ],
  "event_log": ".harness/events.jsonl",
  "storage_db": ".harness/storage.db",
  "llm": {
    "model": "gpt-4o-mini",
    "temperature": 0.2
  }
}
```

### Common Diagnostics

| Issue | Cause | Resolution |
|---|---|---|
| `DependencyError: Missing dependencies` | A plugin requires a `ServiceKey` that is not registered. | Ensure the provider plugin is listed in `plugin_dirs` or loaded before the requiring plugin. |
| `TransportError: Process not running` | A sandboxed subprocess crashed or timed out. | Check the plugin script's syntax or increase timeout with `call(timeout=60.0)`. |
| `ServiceNotFoundError` | Code attempted to `require()` a service that was revoked. | Check if the providing plugin was disabled or unloaded. |

---

*Brain Harness — Autonomous Agent System. Verified for Python ≥ 3.10.*
