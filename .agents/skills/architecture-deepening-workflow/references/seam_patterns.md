# Architectural Hotspot Decomposition Patterns

Standard structural patterns for partitioning common monolithic archetypes into subpackages <= 200 lines:

## Pattern 1: Click CLI Command Groups (e.g. `src/harness/commands/uncertainty/`)
- `group.py`: Single Click group declaration with co-located `group.add_command()` registrations (Rule 6).
- `<subcommand>.py`: Granular subcommands isolated into dedicated modules.
- `converters.py`: Input/output and formatting converters.
- `brief.py`: HTML visual brief generator.
- `__init__.py`: Facade re-exporting CLI group and subcommands.

## Pattern 2: Micro-Kernel Services (e.g. `src/harness/services/codebase_context/`)
- `models.py` / `checks.py` / `reports.py`: Slotted & frozen dataclasses (Rule 12 & 43).
- `protocol.py`: Typed protocol and `ServiceKey[T]` (Rule 2).
- `resolvers.py`: Single-seam `resolve_*()` factory (Rule 58).
- `service.py`: `Default*Service` implementing protocol and delegating to engines.
- `__init__.py`: Package facade with Windows UTF-8 stream codec entrypoint (Rule 23).

## Pattern 3: Harness Plugins (e.g. `plugins/memory_and_epistemics/context_type_system/`)
- `models.py`: Slotted entity representations (Rule 12).
- `engine/`: Domain calculation, ledger, storage, and assembly submodules.
- `main.py`: `HarnessPlugin` subclass with explicit `plugin = MyPlugin()` export (Rule 45).
- `resolvers.py`: Single-seam resolver with IoC context resolution (Rule 58).
