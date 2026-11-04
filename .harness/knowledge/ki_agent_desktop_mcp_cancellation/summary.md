# Clap-Derived Dynamic MCP Server with Pre-Spawn Cancel & SIGTERM Input Release

## Context
Extracted during automated repository triad ingestion from `D:\GitHub\cloned\agent-desktop`.

## Distilled Learning
The agent-desktop mcp subcommand projects all leaf commands from clap CommandFactory into MCP tools adhering to the 2026-07-28 specification. Concurrency is strictly capped at 8 in-flight calls. A centralized Calls registry admits request IDs under mutex before worker thread execution so early cancellations never orphan running children. When an active headed action (e.g., mouse drag) is cancelled, SIGTERM is sent first with a 3-second grace window, allowing the OS input release handler to un-press buttons and keys before process termination.

## Triggers & Seam Choices
- **Trigger**: Desktop GUI automation, native accessibility tree walks, ref resolution, or agent ReAct tool retry decisions.
- **Seam Choice**: Integration via Brain Harness IoC container (`AGENT_DESKTOP_KEY`), `agent-desktop-operator` skill, and `plugin.agent_desktop`.
