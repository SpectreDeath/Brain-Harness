# Knowledge Item: Agent Instruction File Hygiene & Boundary Control

- **ID**: `ki_self_20260828_01`
- **Category**: `configuration` / `agent_hygiene`
- **Status**: `VERIFIED`

## Summary & Heuristic

Repository agent instruction files (`AGENTS.md`, `CLAUDE.md`) must be treated as executable interface definitions rather than narrative documentation.

### Core Guidelines:
1. **Context Economy**: Keep total line count strictly under 150 lines. Every token consumes prompt budget across every model turn.
2. **Eliminate Lint Leakage**: Avoid generic programming tutorials, markdown style lectures, or language syntax explainers.
3. **Execution Seams**: Provide single-source commands for build, test, and lint cycles so agents never guess flags or environments.
4. **Negative Boundaries**: Explicitly state "what NOT to touch" (e.g. lockfiles, generated assets, sensitive database migrations).
5. **Post-Mortem Hardening**: When an agent fails or diverges, identify the root cause and add an actionable negative constraint to the instruction file.
