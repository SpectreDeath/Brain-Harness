# In-Place Foundational Deepening over Redundant Plugin Sprawl

## Architectural Summary
Demonstrates the principle of in-place foundational deepening. When Kimi Code's pure-language Tree-Sitter Bash AST parsing was analyzed, rather than creating a duplicate standalone shell parser plugin, the existing `codex_execpolicy` was upgraded in-place.

## Operational Guidelines
1. **Consolidate Domain Logic:** Keep single authority for shell execution policy within `codex_execpolicy`.
2. **Deepen Interfaces:** Extend existing AST node contracts to represent complex constructs (subshells, process substitutions, variable prefixes).
3. **Prevent Tool Clutter:** Avoid giving ReAct agents redundant tools that perform overlapping operations.
