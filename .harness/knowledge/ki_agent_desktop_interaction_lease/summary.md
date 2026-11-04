# Cross-Process Interaction Lease & Web-Wrapper Depth Bypass

## Context
Extracted during automated repository triad ingestion from `D:\GitHub\cloned\agent-desktop`.

## Distilled Learning
Mutating desktop application state across multiple agent processes can lead to input collisions. agent-desktop resolves this with an inheritable InteractionLease that tracks contention counts and provides atomic ownership during semantic clicks and typing. For observation, it identifies Chromium provenance (Chrome_WidgetWin_1 on Windows) and skips non-semantic anonymous container wrappers during tree walks, preventing deep web applications from exhausting observation budgets by an order of magnitude.

## Triggers & Seam Choices
- **Trigger**: Desktop GUI automation, native accessibility tree walks, ref resolution, or agent ReAct tool retry decisions.
- **Seam Choice**: Integration via Brain Harness IoC container (`AGENT_DESKTOP_KEY`), `agent-desktop-operator` skill, and `plugin.agent_desktop`.
