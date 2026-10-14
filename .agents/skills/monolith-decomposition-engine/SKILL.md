---
name: monolith-decomposition-engine
description: Factor monolithic codebases into slotted domain models, single-seam resolvers, and Click command groups strictly bounded to <= 200 lines. Do not use for generic prompt writing or untyped procedural scripts.
---

# Monolith Decomposition Engine

Authoritative deep architectural skill providing AST factorization patterns, slotted domain model extraction, single-seam resolvers (Rule 58), and Click command consolidation (Rule 6).

## Overview

The `monolith-decomposition-engine` provides the technical levers to factor complex monolithic Python modules into high-cohesion, low-coupling subpackages adhering to strict architectural invariants:
- **Rule 6 (Click CLI Single-Source Consolidation)**: Declaring command groups and subcommands in a single co-located block.
- **Rule 11 (Strict Submodule Bounds)**: Strictly capping submodule length at $\le 200$ lines.
- **Rule 12 & 43 (Slotted & Frozen Dataclasses)**: Applying `slots=True, frozen=True` to internal state, AST nodes, and check records.
- **Rule 23 (Windows UTF-8 Stream Codec)**: Reconfiguring `sys.stdout` and `sys.stderr` to UTF-8 at module entry.
- **Rule 45 (Plugin Singleton Export)**: Ensuring plugin entrypoints export instantiated singletons (`plugin = MyPlugin()`).
- **Rule 58 (Single-Seam Resolver)**: Standardizing `resolve_<domain>(context)` factories that handle IoC resolution and local fallbacks.

## Technical Levers

### 1. Slotted & Frozen Model Extraction
Extract data structures out of monolithic files into dedicated `models.py` (or `checks.py` / `reports.py` if complex):
```python
@dataclass(slots=True, frozen=True)
class CheckResult:
    target: str
    passed: bool
    message: str

    def __post_init__(self) -> None:
        assert self.target, "target cannot be empty"
```

### 2. Single-Seam Resolver Factory (Rule 58)
Implement unified resolvers in `resolvers.py` that query the IoC container with graceful fallback:
```python
def resolve_service(ctx: ServiceContext | None = None) -> ServiceProtocol:
    if ctx is not None:
        svc = ctx.optional(SERVICE_KEY)
        if svc is not None:
            return svc
    return DefaultService()
```

### 3. Click CLI Command Group Consolidation (Rule 6)
Consolidate Click command groups into `group.py` with explicit co-located `.add_command()` calls to avoid shadowing:
```python
@click.group("domain")
def domain_group() -> None:
    """Domain CLI command group."""
    pass

domain_group.add_command(cmd_action)
domain_group.add_command(cmd_inspect)
```

## Anti-Patterns

- **Shallow Delegation Wrappers** — Creating submodules that only wrap another function without meaningful interface depth.
- **Untyped String Service Keys** — Querying the IoC container using raw strings instead of typed `ServiceKey[T]` (Rule 2).
- **Mutating Frozen Dataclasses** — Attempting attribute reassignment on frozen entities instead of constructing new immutable copies (Rule 12 & 43).
- **Click Subcommand Shadowing** — Declaring multiple `@main.group()` blocks with the same name across files, breaking subcommand registration (Rule 6).
- **Missing Module-Level Singletons** — Forgetting `plugin = MyPlugin()` in plugin entrypoint manifests (Rule 45).
