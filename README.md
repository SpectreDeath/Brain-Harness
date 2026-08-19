# Harness

> **Modular agent harness — everything is a plugin.**

A Python-native framework where models, tools, agent loops, storage, and sandboxes are all swappable plugins running on a lightweight IoC micro-kernel. Inspired by DeepSeek Harness's "everything is a plugin" philosophy, built for the existing AI Agent & Forensic Simulation Ecosystem.

## Key Features

- **IoC Micro-Kernel** — Service context with typed keys, dependency injection, and automatic cleanup
- **Plugin Lifecycle** — `DISCOVERED → LOADED → VALIDATED → ENABLED → DISABLED → UNLOADED` with dependency resolution
- **Event Bus** — Append-only event stream for observability and debugging
- **GitHub → Plugin Pipeline** — `harness plugin add <github-url>` downloads, inspects, and auto-converts any repository into a live plugin
- **Subprocess Sandboxing** — Untrusted plugins run in isolated subprocesses via JSON-RPC
- **CLI-First** — Simple commands, no server to manage

## Documentation

📖 See the complete **[User Manual & Reference Guide](USER_MANUAL.md)** for detailed CLI commands, plugin authoring tutorials, sandbox architecture, ecosystem bridge setup, and Python SDK guides.

## Quick Start

```bash
pip install -e ".[dev]"

# Initialize a workspace
harness init

# Add a plugin from GitHub
harness plugin add https://github.com/owner/repo

# List plugins
harness plugin list

# Start the harness
harness run
```

## Architecture

```
┌─────────────────────────────────────────────┐
│                  CLI / API                   │
├─────────────────────────────────────────────┤
│              Service Context                 │
│         (IoC Container + Registry)           │
├──────────┬──────────┬───────────────────────┤
│  Plugin  │  Event   │  GitHub → Plugin      │
│  System  │  Bus     │  Ingestion Pipeline   │
├──────────┴──────────┴───────────────────────┤
│          Built-in Service Plugins            │
│   (LLM · Storage · Tools · Sandbox)         │
└─────────────────────────────────────────────┘
```

## Ecosystem

Part of the [AI Agent & Forensic Simulation Ecosystem](../README.md), alongside Memtext, Em-Cubed, Skill Flywheel, SME, and Strategify.
