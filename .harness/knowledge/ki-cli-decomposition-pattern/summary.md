# CLI Monolith Decomposition Pattern

**ID:** `ki-cli-decomposition-pattern`

## Summary
Pattern for decomposing monolithic Click CLI entry points into domain-specific command modules. The cli.py file (1,331 LOC) contains 17+ Click command groups defined inline. The pattern promotes each @main.group() block to its corresponding commands/*.py module, leaving cli.py as a thin ~100 LOC import router. Key constraint: AGENTS.md Rule 6 mandates CLI command groups are declared exactly once in a single co-located block.
