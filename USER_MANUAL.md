# Brain Harness — User Manual & Reference Guide

```
  ██████╗ ██████╗  █████╗ ██╗███╗   ██╗    ██╗  ██╗ █████╗ ██████╗ ███╗   ██╗███████╗███████╗███████╗
  ██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║    ██║  ██║██╔══██╗██╔══██╗████╗  ██║██╔════╝██╔════╝██╔════╝
  ██████╔╝██████╔╝███████║██║██╔██╗ ██║    ███████║███████║██████╔╝██╔██╗ ██║█████╗  ███████╗███████╗
  ██╔══██╗██╔══██╗██╔══██║██║██║╚██╗██║    ██╔══██║██╔══██║██╔══██╗██║╚██╗██║██╔══╝  ╚════██║╚════██║
  ██████╔╝██║  ██║██║  ██║██║██║ ╚████║    ██║  ██║██║  ██║██║  ██║██║ ╚████║███████╗███████║███████║
  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝╚══════╝
```

> **A modular, autonomous agent harness where *everything* is a plugin — and the harness becomes a reflection of your brain.**

---

## Table of Contents

1. [Introduction & Core Philosophy](#1-introduction--core-philosophy)
2. [Architecture Overview](#2-architecture-overview)
3. [Installation & Workspace Setup](#3-installation--workspace-setup)
4. [CLI Operations Manual](#4-cli-operations-manual)
   - [Workspace Management & Hot-Reload (`init`, `watch`, `apply`, `config`)](#workspace-management--hot-reload)
   - [Plugin Ingestion & Lifecycle Management (`plugin`)](#plugin-ingestion--lifecycle-management)
   - [Granular Tool & Skill Enablement (`tool`)](#granular-tool--skill-enablement)
   - [Autonomous Agent Task Execution (`agent`)](#autonomous-agent-task-execution)
   - [Hierarchical Session Introspection & Trajectory Export (`session`)](#hierarchical-session-introspection--trajectory-export)
   - [3-Tier AST Context Compilation & Code Skeletonization (`context`)](#3-tier-ast-context-compilation--code-skeletonization)
   - [Compute Budget & Model Tier Assessment (`assess-compute`)](#compute-budget--model-tier-assessment)
   - [Agent Skill Knowledge Graph & Intent Routing (`skills`)](#agent-skill-knowledge-graph--intent-routing)
   - [Dynamic Plugin Creator & Archetype Scaffolding (`creator`, `scaffold`, `validate`)](#dynamic-plugin-creator--archetype-scaffolding)
   - [Knowledge Vault & Autobiographical Reflection (`knowledge`, `reflect`)](#knowledge-vault--autobiographical-reflection)
   - [Model Context Protocol (MCP) Server (`mcp`)](#model-context-protocol-mcp-server)
   - [Ecosystem Bridge Management (`bridge`)](#ecosystem-bridge-management)
   - [Runtime Introspection, Telemetry & Web Dashboard (`introspect`, `services`, `events`, `run`, `ui`)](#runtime-introspection-telemetry--web-dashboard)
5. [Plugin Developer Guide](#5-plugin-developer-guide)
   - [Plugin Structure & Manifest (`plugin.json`)](#plugin-structure--manifest-pluginjson)
   - [Archetype Presets](#archetype-presets)
   - [Multi-Language Plugin Support (Python, JavaScript, TypeScript)](#multi-language-plugin-support)
   - [Writing Python In-Process Plugins](#writing-python-in-process-plugins)
   - [Typed Services & `ServiceKey[T]`](#typed-services--servicekeyt)
   - [Registering Tools for Autonomous Agents](#registering-tools-for-autonomous-agents)
   - [Validation & Auto-Remediation Engine](#validation--auto-remediation-engine)
6. [Ingestion & Sandbox Security](#6-ingestion--sandbox-security)
   - [Universal Ingestion Pipeline](#universal-ingestion-pipeline)
   - [Subprocess & Virtualenv Sandboxing](#subprocess--virtualenv-sandboxing)
   - [Lazy Subprocess Staging & Context Transactions](#lazy-subprocess-staging--context-transactions)
7. [Ecosystem Bridges](#7-ecosystem-bridges)
   - [Em-Cubed (Neuro-Symbolic Surfaces)](#em-cubed-neuro-symbolic-surfaces)
   - [Memtext (Persistent Memory & Decision Audit)](#memtext-persistent-memory--decision-audit)
   - [Skill Flywheel (Domain Skill Catalog)](#skill-flywheel-domain-skill-catalog)
   - [MCP Client & Server](#mcp-client--server)
8. [Python SDK & Programmatic Usage](#8-python-sdk--programmatic-usage)
9. [Configuration & Troubleshooting](#9-configuration--troubleshooting)

---

## 1. Introduction & Core Philosophy

**Brain Harness** is an unopinionated, enterprise-grade agent execution environment engineered with a strict **micro-kernel architecture**.

Rather than shipping a rigid, pre-packaged bundle of hardcoded domain tools, **Harness is a blank cognitive canvas**. By ingesting your own repositories, custom tools, ZIP archives, and agent skills, **your harness becomes a direct reflection of your brain**—tailored precisely to your domain, workflows, and thinking.

### Key Architectural Tenets
- **Everything is a Plugin:** Models, tools, memory, storage engines, execution surfaces, and agent loops are all plugins registered into a unified Inversion of Control (IoC) container. No agent capability is hardcoded into the kernel.
- **Your Brain, Your Harness:** Harness starts clean. You feed it GitHub URLs, local projects, or ZIP files (`harness plugin add <source>`), and the ingestion pipeline dynamically inspects, sandboxes, and mounts them into your personal runtime.
- **Typed Service Keys:** All service registration, dependency injection, and resolution use typed `ServiceKey[T]` tokens rather than fragile raw strings.
- **Transactional Lifecycle Management:** Plugins declare their dependencies (`requires`) and capabilities (`provides`). The lifecycle manager topologically sorts dependencies and ensures zero service leakage on plugin disabling or unloading.
- **Subprocess Isolation by Default:** Ingested external code or untrusted tools execute in isolated subprocess sandboxes communicating via line-buffered JSON-RPC 2.0 over standard I/O pipes.
- **Deterministic Pre-LLM Context Optimization:** Multi-pass pruning, whitespace deduplication, tabular payload compression, and 3-tier AST skeletonization prevent context blowout and enforce bounded token budgets.
- **Agent Skill Knowledge Graph:** Declarative skill cards (`CARD.md` / `SKILL.md`) are automatically indexed into an in-memory directed graph with shortest-path chaining, intent routing, and anti-pattern defense.
- **Autobiographical Reflection & Knowledge Vault:** Harness harvests its own transcripts, reports, and execution logs to distill verified, Isnad-grounded Knowledge Items.
- **Immutable Event Stream:** All system transitions, tool executions, agent reasoning steps, and errors are appended to an immutable audit log.

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             CLI & Web Dashboard (UI)                             │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                  Harness Runtime                                 │
│  ┌──────────────────────┬──────────────────────┬──────────────────────────────┐  │
│  │   ServiceContext     │   PluginLifecycle    │          EventBus            │  │
│  │  (Typed IoC Kernel)  │  (Topological Graph) │   (Append-Only Telemetry)    │  │
│  └──────────────────────┴──────────────────────┴──────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────────────────┤
│                       Universal Ingestion & Sandbox Engine                       │
│   • GitHub URL Fetcher & Inspector (AST analysis & auto-manifest)                │
│   • ZIP / Local Codebase / OpenAPI / PyPI Converters                             │
│   • Subprocess, Virtualenv & In-Process Transports (JSON-RPC 2.0)                │
├──────────────────────────────────────────────────────────────────────────────────┤
│                              Core Service Plugins                                │
│   • LLM Service (LiteLLM / OpenAI / Anthropic / Local LLMs)                      │
│   • Dynamic Tool Registry & Dispatch Table                                       │
│   • SQLite Storage Engine & Session State                                        │
│   • Autonomous ReAct / Hierarchical Multi-Agent Engine                           │
│   • Skill Knowledge Graph Service (Chaining & Routing)                           │
│   • Knowledge Vault & Autobiographical Reflection Service                        │
├──────────────────────────────────────────────────────────────────────────────────┤
│                              Ecosystem Bridges                                   │
│   • Em-Cubed (Prolog, Z3, Datalog, Hy, SQLite surfaces)                          │
│   • Memtext (Persistent memory & decision auditing)                              │
│   • Skill Flywheel (Catalog of 800+ domain skills)                               │
│   • MCP Client & Server (Model Context Protocol)                                 │
├──────────────────────────────────────────────────────────────────────────────────┤
│                              Your Ingested Plugins                               │
│     [Your Repos]   [Your Domain Tools]   [Your APIs]   [Your Knowledge Skills]   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Installation & Workspace Setup

### Prerequisites
- Python **≥ 3.10** (Python 3.10, 3.11, 3.12, 3.13 fully supported)
- Git (optional, for fetching GitHub repositories)

### Installation
Clone the repository and install with development dependencies:

```bash
git clone https://github.com/SpectreDeath/Brain-Harness.git
cd Brain-Harness
pip install -e ".[dev]"
```

Verify installation:
```bash
harness --version
```

### Initializing a Workspace
Initialize the current directory or create a new workspace:

```bash
# Initialize current directory
harness init

# Initialize specific target path
harness init ./my-agent-workspace
```

This sets up the standard workspace directory layout:
```
my-workspace/
├── plugins/              # Drop-in folder for custom / ingested plugins
└── .harness/
    ├── config.json       # Workspace configuration
    ├── events.jsonl      # Immutable event stream audit log
    ├── knowledge/        # Distilled Knowledge Vault items
    └── storage.db        # Persistent SQLite storage
```

---

## 4. CLI Operations Manual

Brain Harness provides a single unified CLI binary: `harness`.

### Workspace Management & Hot-Reload

#### `harness init [PATH]`
Scaffolds a new workspace with configuration and drop-in plugin directories.
```bash
harness init .
```

#### `harness watch`
Starts the Harness runtime with live filesystem hot-reloading. Watches `plugins/` and immediately recompiles/re-enables modified plugins without downtime.
```bash
harness watch
```

#### `harness apply -f <config-file>`
Applies and reconciles a declarative configuration tree (`.yaml` or `.json`) against the active Harness instance.
```bash
harness apply -f ./harness-config.yaml
```

#### `harness config validate <config-file>`
Validates syntax and schema compliance for declarative configuration files.
```bash
harness config validate ./harness-config.yaml
```

---

### Plugin Ingestion & Lifecycle Management

#### `harness plugin add <source> [OPTIONS]`
Ingests a GitHub repository, owner/repo shorthand, local directory, or ZIP archive into an isolated plugin.
```bash
# Ingest public GitHub repository
harness plugin add https://github.com/psf/requests

# Ingest specific git branch or tag
harness plugin add https://github.com/psf/requests --ref v2.31.0

# Ingest local ZIP archive
harness plugin add ./my-tools.zip

# Re-download and force manifest re-synthesis
harness plugin add https://github.com/psf/requests --force
```

#### `harness plugin list`
Lists all discovered plugins, manifest presence, and local filesystem paths.
```bash
harness plugin list
```

#### `harness plugin inspect <path>`
Inspects any plugin directory and renders its standardized metadata card.
```bash
harness plugin inspect plugins/requests
```

#### `harness plugin info <name>` & `harness plugin card <name>`
Displays the standardized summary card, parameters, and entrypoint signatures for an installed plugin.
```bash
harness plugin info requests
harness plugin card requests
```

#### `harness plugin guide <name>`
Prints the auto-generated Quick Start and Agent Usage Guide for the specified plugin.
```bash
harness plugin guide requests
```

#### `harness plugin enable <name>` / `disable <name>`
Enables or disables an installed plugin by name or pattern.
```bash
harness plugin enable requests
harness plugin disable requests
```

#### `harness plugin enable-all` / `disable-all [OPTIONS]`
Batch enables all discovered plugins or disables all non-core plugins.
```bash
harness plugin enable-all
harness plugin disable-all --keep-core
```

#### `harness plugin remove <name>`
Safely tears down and deletes a cached plugin package from `plugins/`.
```bash
harness plugin remove requests
```

---

### Granular Tool & Skill Enablement

Harness allows fine-grained runtime control over individual tool endpoints:

#### `harness tool list [OPTIONS]`
Lists all registered tools, their provider plugin, and active enablement state.
```bash
# List all registered tools
harness tool list

# Filter tools by provider plugin
harness tool list --provider requests

# Show only enabled tools
harness tool list --enabled-only
```

#### `harness tool enable <name>` / `disable <name>`
Enables or disables a specific tool endpoint dynamically.
```bash
harness tool disable requests.post
harness tool enable requests.post
```

---

### Autonomous Agent Task Execution

#### `harness agent run "<task>" [OPTIONS]`
Executes an autonomous task using the ReAct (Reasoning + Acting) execution engine with transactional tool isolation and multi-pass context optimization.
```bash
harness agent run "Analyze repository dependencies and list all outdated packages" --max-steps 15
```

#### Options:
- `--max-steps <N>`: Maximum thought/action reasoning steps (default: `10`).

---

### Hierarchical Session Introspection & Trajectory Export

Harness exposes first-class headless CLI seams for inspecting agent execution trees, token metrics, and transcripts.

#### `harness session list [OPTIONS]`
Lists all stored agent sessions with step counts and execution status.
```bash
# List recent sessions
harness session list --limit 10

# Filter by execution status
harness session list --status COMPLETED

# List only root-level sessions
harness session list --root-only
```

#### `harness session get <session_id>`
Retrieves full structured JSON state for a specific session.
```bash
harness session get sess_20260828_01
```

#### `harness session tree <session_id>`
Renders the hierarchical multi-agent execution tree with aggregated subtree token counts, durations, and child statuses.
```bash
harness session tree sess_20260828_01
```
*Example Output:*
```
Execution Tree for Session: sess_20260828_01
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Subtree Sessions: 3
Total Tokens:           4,280
Total Steps:            7
Completed / Failed:     3 / 0
Duration:               4.12s

Tree Hierarchy:
────────────────────────────────────────────────────────────
• [supervisor] sess_20260828_01 (COMPLETED) — Coordinate repository audit
  └─ [worker] sess_20260828_02 (COMPLETED) — Scan dependency security
  └─ [worker] sess_20260828_03 (COMPLETED) — Generate summary report
```

#### `harness session export <session_id> [OPTIONS]`
Exports an agent session trajectory into clean GitHub-flavored Markdown or structured JSON.
```bash
# Export trajectory to terminal
harness session export sess_20260828_01 --format markdown

# Save trajectory to file
harness session export sess_20260828_01 --format markdown -o ./trajectory.md
```

---

### 3-Tier AST Context Compilation & Code Skeletonization

Prevent context window blowout by compiling deterministic, AST-reachability-bounded context graphs prior to model invocation:

#### `harness context compile <target_file> [OPTIONS]`
Compiles a 3-tier reachability context graph starting from a target file:
- **Tier 1**: Target file in full source.
- **Tier 2**: Direct dependencies compiled to interface skeletons (docstrings, class/function signatures, `...` bodies).
- **Tier 3**: Excluded transitive dependencies.

```bash
harness context compile src/harness/kernel/runtime.py --repo-root . --max-hops 2
```

#### `harness context skeletonize <target_file>`
Extracts a structural interface skeleton from any Python source file, stripping internal function bodies while preserving type signatures and docstrings.
```bash
harness context skeletonize src/harness/agent/engine.py
```

---

### Compute Budget & Model Tier Assessment

#### `harness assess-compute "<prompt>" [OPTIONS]`
Assesses task surface complexity and recommends calibrated model tiers and thinking budgets (Gemini 3.7 Flash, Claude 3.7 Sonnet, OpenAI o-series).
```bash
# Assess architectural refactoring task
harness assess-compute "Refactor IoC container lifecycle to support async teardown" --arch --files 4

# Output assessment as JSON
harness assess-compute "Fix off-by-one bug in token counter" --debug-task --json

# Generate interactive HTML visual brief in %TEMP%
harness assess-compute "Design multi-agent consensus protocol" --arch --html
```

#### Options:
- `--files`, `-f`: Number of files in scope (default: `1`).
- `--arch`, `-a`: Flag indicating architectural refactoring.
- `--debug-task`, `-d`: Flag indicating debugging / diagnostic investigation.
- `--profile`, `-p`: Scoring preset (`balanced`, `reasoning_heavy`, `cost_optimized`, `latency_optimized`).
- `--override`, `-o`: Force specific tier (`high_reasoning`, `standard_agentic`, `fast_mechanical`).
- `--json`: Output raw assessment in JSON format.
- `--html`: Generate an interactive visual HTML brief.

---

### Agent Skill Knowledge Graph & Intent Routing

Harness indexes structured agent skills (`SKILL.md` and companion `CARD.md`) into a directed graph for autonomous multi-step execution:

#### `harness skills graph [OPTIONS]`
Indexes all skills in the workspace and displays node/edge statistics.
```bash
# Display skill statistics
harness skills graph

# Generate an interactive HTML Visual Brief in %TEMP%
harness skills graph --visual
```

#### `harness skills route "<intent>" [OPTIONS]`
Routes natural language intent to matching skills with confidence scores and recommended execution chains.
```bash
harness skills route "fetch wine dataset from UCI and profile outliers" --top-k 3
```

#### `harness skills chain <start_skill> <target_skill>`
Computes the shortest directed topological execution path between two skills.
```bash
harness skills chain structured-data-scout questio-reflection
```

#### `harness skills info <skill_name>`
Inspects topological dependencies, prerequisites, downstream handoffs, and mitigated anti-patterns for a skill.
```bash
harness skills info questio-reflection
```

#### `harness skills create <name> [OPTIONS]`
Scaffolds a high-precision agent skill with `SKILL.md` and `CARD.md` blueprints conforming to deep-module craft standards.
```bash
harness skills create database-auditor \
  --description "Audit PostgreSQL connection pools and query performance" \
  --category "data_engineering" \
  --trigger "audit database" \
  --trigger "check connection pool" \
  --validate
```

#### `harness skills validate <skill_dir>`
Validates an agent skill against deep-module craft standards, checking YAML frontmatter, 5-stage progressions, companion card checklists, and anti-pattern boundaries.
```bash
harness skills validate .agents/skills/questio-reflection
```

---

### Dynamic Plugin Creator & Archetype Scaffolding

Creator Mode enables rapid authoring, templating, and pre-flight validation of plugins.

#### `harness creator init`
Interactive CLI wizard that guides you through plugin name, description, implementation language, preset, tool names, dependencies, and isolation modes.
```bash
harness creator init
```

#### `harness creator build <name>` (or `harness create` / `harness scaffold`)
Scaffolds a complete plugin package non-interactively from CLI flags.
```bash
harness creator build data_cleaner \
  --description "CSV and JSON cleaning utilities" \
  --language python \
  --preset tool \
  --tools "clean_csv,normalize_json" \
  --deps "pandas,pydantic" \
  --isolation subprocess
```

#### `harness creator archetypes` (or `harness archetypes`)
Lists all available plugin archetype presets:
- `general`: Standard multipurpose plugin.
- `tool`: High-performance utility tool provider.
- `service`: Background daemon or stateful service provider.
- `api_wrapper`: External REST / GraphQL API client.
- `agentic_workflow`: Multi-step reasoning pipeline.
- `container`: OCI container / Docker wrapper.
- `mcp_bridge`: Bridge connecting external MCP tool servers.

```bash
harness creator archetypes
```

#### `harness creator validate <path>` (or `harness validate`)
Validates manifest structure, entrypoint syntax, dependency definitions, and optionally executes a dry-run inside a sandboxed subprocess.
```bash
# Static validation
harness creator validate plugins/data_cleaner

# Dynamic sandbox execution test
harness creator validate plugins/data_cleaner --dry-run --timeout 10.0

# Auto-repair detected issues
harness creator validate plugins/data_cleaner --fix
```

#### `harness creator remediate <path>`
Automatically repairs missing manifests, generates entrypoint stubs, and normalizes configuration files.
```bash
harness creator remediate plugins/data_cleaner
```

---

### Knowledge Vault & Autobiographical Reflection

Harness includes an endogenous memory loop that harvests internal execution history, extracts battle-tested heuristics, and commits verified Knowledge Items (KIs) with complete Isnad provenance.

#### `harness reflect` (or `harness knowledge reflect`)
Runs an endogenous reflection cycle across temporary HTML reports and conversation transcripts.
```bash
# Run reflection across all recent reports and transcripts
harness reflect

# Filter reflection to a specific category
harness reflect --category architecture --min-confidence 0.85

# Dry run without committing to knowledge vault
harness reflect --no-commit
```

#### `harness knowledge sync`
Synchronizes on-disk Knowledge Items (`.harness/knowledge/`) into persistent SQLite storage.
```bash
harness knowledge sync
```

#### `harness knowledge list [OPTIONS]`
Lists all Knowledge Items in storage with titles and category tags.
```bash
harness knowledge list
harness knowledge list --tag architecture
```

#### `harness knowledge query "<query>" [OPTIONS]`
Searches the Knowledge Vault by semantic keyword, tag, or Isnad status.
```bash
harness knowledge query "subprocess isolation" --status VERIFIED
```

#### `harness knowledge verify <ki_id>`
Audits the unbroken Isnad chain of custody for a Knowledge Item, asserting that all primary source URIs, commits, and report files exist.
```bash
harness knowledge verify ki_self_20260826_01
```

---

### Model Context Protocol (MCP) Server

#### `harness mcp serve`
Starts the Harness MCP server over standard I/O (`stdin`/`stdout`). Exposes all internal plugins, sandboxed tools, and ecosystem surfaces to external IDEs (Claude Code, Cursor, Windsurf, Gemini, etc.).

```bash
harness mcp serve
```

*Example Cursor / Claude Code `mcp_config.json` entry:*
```json
{
  "mcpServers": {
    "brain-harness": {
      "command": "harness",
      "args": ["mcp", "serve"]
    }
  }
}
```

---

### Ecosystem Bridge Management

#### `harness bridge list`
Lists all registered ecosystem bridges (`Em-Cubed`, `Memtext`, `Skill Flywheel`) and their current availability.
```bash
harness bridge list
```

#### `harness bridge status [name]`
Runs detailed diagnostics on peer ecosystem bridges.
```bash
# Check all ecosystem bridges
harness bridge status

# Check specific bridge
harness bridge status em_cubed
```

---

### Runtime Introspection, Telemetry & Web Dashboard

#### `harness introspect`
Displays live runtime diagnostics, active plugins, registered services, available tools, and a Mermaid dependency graph.
```bash
harness introspect
```

#### `harness services`
Lists all registered IoC services and their providing plugins.
```bash
harness services
```

#### `harness events [OPTIONS]`
Views the chronological, append-only event stream log.
```bash
# View last 50 events
harness events

# Filter by event type
harness events --type tool.invoked --limit 20
```

#### `harness run`
Starts the Harness runtime in interactive CLI console mode.
```bash
harness run
```

#### `harness ui [OPTIONS]`
Launches the real-time Web Control Room dashboard with WebSocket telemetry.
```bash
harness ui --host 127.0.0.1 --port 8080
```
Open [http://127.0.0.1:8080](http://127.0.0.1:8080) in your browser to inspect live agent execution, telemetry, and IoC container status.

---

## 5. Plugin Developer Guide

### Plugin Structure & Manifest (`plugin.json`)

A standard plugin directory contains at least a manifest (`plugin.json`) and an entry script:

```
plugins/weather_tool/
├── plugin.json
└── main.py
```

#### Complete `plugin.json` Schema:
```json
{
  "name": "weather_tool",
  "version": "1.0.0",
  "description": "Fetch real-time weather reports for autonomous agents",
  "language": "python",
  "entrypoint": "main.py",
  "isolation": "subprocess",
  "trusted": false,
  "category": "general",
  "dependencies": ["requests>=2.31.0"],
  "entrypoints": [
    {
      "name": "get_weather",
      "description": "Get current weather conditions for a city",
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
          "description": "Temperature units: 'celsius' or 'fahrenheit'",
          "required": false
        }
      ]
    }
  ]
}
```

---

### Archetype Presets

When creating plugins with `harness creator build`, choose from seven specialized presets:

| Preset | Description | Default Isolation | Recommended Use Case |
|---|---|---|---|
| `general` | Standard multipurpose plugin | `subprocess` | General utilities and scripts |
| `tool` | High-performance tool provider | `subprocess` | Computational tools, formatting, parsing |
| `service` | Long-running stateful service | `in_process` | In-memory caches, message routers |
| `api_wrapper` | HTTP REST / GraphQL client | `subprocess` | SaaS integrations, web APIs |
| `agentic_workflow` | Multi-step reasoning pipeline | `subprocess` | Complex agent orchestration loops |
| `container` | OCI / Docker container wrapper | `subprocess` | Heavy binary tools, multi-language runtimes |
| `mcp_bridge` | Model Context Protocol adapter | `subprocess` | Connecting third-party MCP servers |

---

### Multi-Language Plugin Support

Harness supports sandboxed plugins written in **Python**, **JavaScript**, and **TypeScript**:

#### Python Entrypoint (`main.py`):
```python
def get_weather(city: str, units: str = "celsius") -> str:
    """Fetch current weather for a city."""
    return f"Weather in {city}: 21° {units.capitalize()}, Clear skies."
```

#### TypeScript Entrypoint (`index.ts`):
```typescript
export function get_weather(params: { city: string; units?: string }): string {
    const unitStr = params.units || "celsius";
    return `Weather in ${params.city}: 21° ${unitStr}, Clear skies.`;
}
```

---

### Writing Python In-Process Plugins

Trusted in-process plugins inherit directly from [`HarnessPlugin`](file:///d:/GitHub/projects/Brain%20Harness/src/harness/plugins/base.py) and interact with the IoC container via typed `ServiceKey[T]`:

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
        # Scoped cleanup occurs automatically
        pass

    async def on_unload(self) -> None:
        pass
```

---

### Validation & Auto-Remediation Engine

Verify plugin packages prior to runtime execution:

```bash
# Run structural validation
harness creator validate plugins/my-plugin

# Perform sandboxed dry-run
harness creator validate plugins/my-plugin --dry-run

# Automatically repair manifest and boilerplate errors
harness creator remediate plugins/my-plugin
```

---

## 6. Ingestion & Sandbox Security

Brain Harness guarantees strict isolation for external, GitHub-sourced, and untrusted plugins.

### Isolation Modes
1. **`subprocess` (Default):** Executes in a separate child process. Input and output are exchanged via strict JSON-RPC 2.0 messages over standard I/O pipes managed by [`StdioJsonRpcTransport`](file:///d:/GitHub/projects/Brain%20Harness/src/harness/plugins/transport.py).
2. **`venv` (Virtual Environment):** Creates an isolated virtualenv, installs the repository's dependencies (`requirements.txt` or `pyproject.toml`), and runs the subprocess inside the virtualenv.
3. **`in_process` (Explicitly trusted plugins only):** Executes within the host Python process for microsecond execution speed.
4. **`docker` (Container Isolation):** Executes within an isolated OCI container sandbox.

### Lazy Subprocess Staging & Context Transactions
- **Lazy Staging**: External plugins with `subprocess` or `venv` isolation remain in `DISCOVERED`/`VALIDATED` state during startup, provisioning virtualenvs lazily on first invocation to eliminate cold-start delays.
- **Context Transactions**: ReAct agent tool invocations execute inside scoped context transactions (`async with context.transaction()`) with automatic rollback on error or exception.

---

## 7. Ecosystem Bridges

Brain Harness includes native connectors to the wider forensic simulation and neuro-symbolic ecosystem:

| Bridge | Description | Key Services & Tools |
|---|---|---|
| **Em-Cubed** | Polyglot neuro-symbolic OS | `bridge.em_cubed`, `surface.python`, `surface.prolog`, `surface.z3`, `surface.sqlite` |
| **Memtext** | Persistent agent memory & audit | `memory.provider`, `memory.store`, `memory.recall` |
| **Skill Flywheel** | Catalog of 800+ domain skills | `bridge.flywheel`, `skill.<skill_id>` |
| **MCP Client & Server** | Model Context Protocol integration | `mcp.<server_name>`, `mcp.<server>.<tool_name>` |

---

## 8. Python SDK & Programmatic Usage

Embed Brain Harness into your own Python applications, backend services, or automated evaluation pipelines:

```python
import asyncio
from harness.kernel.runtime import HarnessRuntime

async def main():
    # Initialize runtime with in-memory storage and standard core services
    async with HarnessRuntime.create(db_path=":memory:") as runtime:
        # 1. Run an autonomous agent task
        result = await runtime.run_task(
            "Find all python files in the current workspace and count their lines."
        )

        print(f"Task Status: {result.status}")
        print(f"Total Steps:  {len(result.steps)}")
        print(f"Final Answer:\n{result.final_answer}")

        # 2. Query the Skill Knowledge Graph
        skill_matches = await runtime.route_skills("clean dataset and remove outliers")
        for match in skill_matches:
            print(f"Matched Skill: {match.skill_name} ({match.confidence:.2f})")

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

### Common Diagnostics & Troubleshooting

| Issue | Cause | Resolution |
|---|---|---|
| `DependencyError: Missing dependencies` | A plugin requires a `ServiceKey` that is not registered. | Ensure the provider plugin is listed in `plugin_dirs` or loaded before the requiring plugin. |
| `TransportError: Process not running` | A sandboxed subprocess crashed or timed out. | Check the plugin script's syntax or run `harness creator validate <path> --dry-run`. |
| `ServiceNotFoundError` | Code attempted to `require()` a service that was revoked. | Check if the providing plugin was disabled (`harness plugin list`). |
| `Validation failed: missing entrypoint` | Plugin manifest references a function that does not exist in `main.py`. | Run `harness creator remediate <path>` to auto-generate missing entrypoint stubs. |
| `Isnad Integrity Warning` | Knowledge Item references a primary source file that was moved or deleted. | Run `harness knowledge verify <ki_id>` and update the lineage URI. |

---

*Brain Harness — Autonomous Agent System. Verified for Python ≥ 3.10.*
