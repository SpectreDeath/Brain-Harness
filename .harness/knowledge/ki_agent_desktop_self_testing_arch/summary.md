# Self-Mutating Architecture Linter & Zero-OS-Dependency Core

## Context
Extracted during automated repository triad ingestion from `D:\GitHub\cloned\agent-desktop`.

## Distilled Learning
agent-desktop enforces a strict 400-LOC cap per file, zero inline // comments, and complete decoupling between crates/core and OS platform crates (windows, macos, linux). Its check_architecture.py script lexes source tokens into placeholders and runs a self-test by injecting synthetic violations into a temporary copy before scanning the repository. If any rule fails to detect its planted violation, CI immediately fails, providing infallible immunity against architectural regression.

## Triggers & Seam Choices
- **Trigger**: Desktop GUI automation, native accessibility tree walks, ref resolution, or agent ReAct tool retry decisions.
- **Seam Choice**: Integration via Brain Harness IoC container (`AGENT_DESKTOP_KEY`), `agent-desktop-operator` skill, and `plugin.agent_desktop`.
