# Click CLI Group Single-Source Co-Registration Invariant

**ID:** `ki_self_20260907_03`  
**Category:** `cli_architecture`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `ba193963/walkthrough.md`, `src/harness/cli.py`, `src/harness/commands/__init__.py`, `AGENTS.md#Rule6`

## Executive Summary
Brain Harness exposes its internal engine capabilities through a rich, headless Click CLI surface. When adding or refactoring CLI command groups (e.g. `harness data`, `harness session`, `harness bridge`), partial or split registrations lead to silent command shadowing, missing CLI help entries, and broken test assertions.

## Dual Co-Registration Requirements

Every CLI command group requires two synchronized registrations:

1. **Mounting the Click Group in `cli.py`**
   - Click command groups must be mounted in a single co-located block in `src/harness/cli.py` using `main.add_command(group, name="...")`.
   - Groups must **never** be defined or decorated multiple times across separate files with the same name, as later definitions shadow earlier ones and erase subcommands (Rule 6).

2. **Registering Async Command Functions in `commands/__init__.py`**
   - Individual async and synchronous command entrypoints must be listed in `_BUILTIN_COMMANDS` in `src/harness/commands/__init__.py`.
   - Each tuple defines `(name, command_func, category, description)`.
   - This enables dynamic introspection (`harness commands list`), headless command discovery, and programmatic CLI invocation by autonomous agents.

## Validation Case Study
In session `ba193963`, the `harness data` command group (`inspect`, `validate`, `lineage`, `quality`, `lakehouse`) was implemented using this exact dual co-registration pattern. All 17 automated CLI runner tests passed on first execution with zero command shadowing.
