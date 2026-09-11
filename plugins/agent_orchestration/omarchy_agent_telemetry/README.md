# Omarchy Agent Telemetry Plugin

The `plugin.omarchy_agent_telemetry` plugin provides introspection, skill catalog browsing, and telemetry script analysis for Omarchy Quattro's agentic workflows.

## Architecture

Omarchy Quattro embeds AI agents directly into the operating system shell and UI panels. Its agent infrastructure is divided into:
1. **Developer Skill Guides** (`agents/skills/*.md`): Guides for automated acceptance testing, command metadata authoring, migration management, icon-font generation, shell development, and visual verification.
2. **Runtime Agent Skills** (`default/agents/skills/*/SKILL.md`): End-user agent capabilities like `omarchy` (desktop environment customization) and `diagnose-crash` (system crash analysis and reporting).
3. **Usage Telemetry Scripts** (`bin/omarchy-agent-usage-*`): Python collectors for Claude Code, Codex, and Fireworks AI token consumption, session records, and OAuth rate limits.

This plugin allows Harness agents to inspect skill documentation and analyze usage collectors without attempting to execute Linux-specific shell processes on non-Linux hosts.

## Exposed Tools

1. `omarchy_list_agent_skills()`: Discover all developer guides and runtime agent skills bundled in Omarchy.
2. `omarchy_get_agent_skill(skill_name: str)`: Retrieve the full markdown text, heading outline, and companion documents for an agent skill.
3. `omarchy_inspect_agent_usage_scripts()`: Statically inspect Omarchy's agent usage collectors, argument requirements, docstrings, and environment variables.

## Configuration

Specified in `config.default.yaml`.
