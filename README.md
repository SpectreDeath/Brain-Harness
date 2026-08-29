# Brain Harness

> **A modular, autonomous agent harness where *everything* is a plugin — and the harness becomes a reflection of your brain.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-755%20passed-brightgreen.svg)](tests/)

**Brain Harness** is an unopinionated, high-performance agent runtime engineered on an IoC micro-kernel architecture. Rather than locking you into a static collection of hardcoded tools, Harness is a **blank cognitive canvas** that ingests any GitHub repository, local project, ZIP archive, OpenAPI specification, or custom skill into an isolated, sandboxed plugin.

When you install and configure plugins, **your harness becomes a direct reflection of your brain** — tailored to your exact domain, knowledge, and workflow.

---

## 🧠 The Philosophy: Harness Your Brain

1. **Clean Micro-Kernel Core**: Models, tools, memory, storage engines, and agent loops are all plugins registered into a unified Inversion of Control (IoC) container with typed `ServiceKey[T]` resolution.
2. **Universal Ingestion Pipeline**: Point Harness at any public/private GitHub repository or local ZIP archive (`harness plugin add <url/zip>`). The engine auto-inspects code, generates schema manifests, and wraps the codebase into a sandboxed plugin.
3. **Subprocess Isolation by Default**: Ingested plugins run in isolated subprocess sandboxes via line-buffered JSON-RPC over `stdin`/`stdout`, protecting host memory and enforcing strict resource limits.
4. **Agent Skill Knowledge Graph**: Harness indexes structured agent skills (`SKILL.md` and `CARD.md`) into a directed knowledge graph, enabling autonomous multi-step skill chaining, semantic intent routing, and anti-pattern defense.
5. **Interactive Web Control Room & Headless CLI**: Full visibility through live terminal commands, an interactive Web dashboard (`harness ui`), live file watching (`harness watch`), and an append-only event stream.
6. **Autobiographical Memory & Reflection**: Harness introspects its own execution history, logs, and visual reports (`harness reflect`) to distill verified, Isnad-grounded Knowledge Items into a persistent Knowledge Vault.

---

## ⚡ Quick Start

### 1. Installation

```bash
git clone https://github.com/SpectreDeath/Brain-Harness.git
cd Brain-Harness
pip install -e ".[dev]"
```

### 2. Initialize Your Workspace

```bash
harness init
```

### 3. Ingest Repositories & Shape Your Harness

Ingest any repository or archive to create live agent plugins:

```bash
# Ingest from GitHub
harness plugin add https://github.com/psf/requests

# Ingest from a local repository or ZIP archive
harness plugin add ./path/to/my-custom-tools.zip

# Inspect installed plugins and summary cards
harness plugin list
harness plugin card requests
```

### 4. Query Skills & Run Autonomous Agents

```bash
# View the agent skill knowledge graph & generate an interactive HTML visual brief
harness skills graph --visual

# Route natural language intent to matching skill chains
harness skills route "fetch wine dataset from UCI and profile outliers"

# Assess task complexity and recommend optimal model tiering & thinking budget
harness assess-compute "Refactor IoC container lifecycle to support async teardown" --arch

# Run an autonomous task using your ingested plugins
harness agent run "Analyze open ports and generate a security report"

# Inspect hierarchical session execution trees and token rollups
harness session list
harness session tree <session_id>

# Run endogenous reflection to distill learnings into the Knowledge Vault
harness reflect

# Start the interactive web control room
harness ui --port 8080
```

---

## 🏗️ Architecture Overview

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
│                       Universal Ingestion & Sandbox Engine                       │
│   • GitHub URL Fetcher & Inspector (AST analysis & auto-manifest)                │
│   • ZIP / Local Codebase / OpenAPI / PyPI Converters                             │
│   • Isolated Subprocess & Virtualenv Sandboxes (JSON-RPC Transport)              │
├──────────────────────────────────────────────────────────────────────────────────┤
│                              Core Service Plugins                                │
│   • LLM Service (LiteLLM / OpenAI / Anthropic / Local LLMs)                      │
│   • Dynamic Tool Registry & Dispatch Table                                       │
│   • SQLite Storage Engine & Session State                                        │
│   • Autonomous ReAct / Hierarchical Swarm Agent Loops                            │
│   • Skill Knowledge Graph Service (Chaining & Routing)                           │
│   • Knowledge Vault & Autobiographical Reflection Service                        │
├──────────────────────────────────────────────────────────────────────────────────┤
│                              Your Ingested Plugins                               │
│     [Your Repos]   [Your Domain Tools]   [Your APIs]   [Your Knowledge Skills]   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📖 Documentation & Ecosystem

- **[User Manual & Reference Guide](USER_MANUAL.md)**: Comprehensive guide covering all CLI commands, plugin authoring, sandbox configurations, MCP server/client setup, and Python SDK usage.
- **[Agent Standards (AGENTS.md)](AGENTS.md)**: Architectural invariants, code style conventions, and testing guidelines.
- **[Domain Context Map (CONTEXT-MAP.md)](CONTEXT-MAP.md)**: Partitioned bounded domains, ubiquitous language, and skill taxonomy.
- **Ecosystem Integration**: Native protocol bridges for **Memtext** (persistent memory & decision auditing), **Em-Cubed** (neuro-symbolic Prolog/Z3 surfaces), and **Model Context Protocol (MCP)**.

---

## 🛡️ License

MIT License &copy; 2026. See [LICENSE](LICENSE) for details.
