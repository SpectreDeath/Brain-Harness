# Micro-Kernel ServiceContext Typed Key Provider Contract & Singleton Export

## Executive Summary
This Knowledge Item establishes the core IoC micro-kernel contracts that power Brain Harness's 95 plugins across 11 domain categories, anchored in **Rule 1** (*Everything is a plugin*), **Rule 2** (*Service keys are typed*), **Rule 3** (*Plugins declare dependencies*), and **Rule 45** (*Plugin Module Singleton & IoC Provider Invariant*).

## Architectural Mechanics
1. **Module Singleton Export Invariant (Rule 45)**:
   - Dynamic plugin discovery in `PluginLoader` expects an instantiated module-level singleton `plugin = MyPlugin()` at `plugins/<category>/<name>/main.py`.
   - Omission of the `plugin` singleton or leaving entrypoints as detached functions prevents dynamic loader discovery and IoC container registration.
2. **Type-Safe ServiceKey[T] Registration & Resolution (Rule 2)**:
   - Services must be registered with `context.provide(KEY, instance)` where `KEY` is a typed `ServiceKey[T]`.
   - Services are resolved with `context.require(KEY)` (mandatory) or `context.optional(KEY)` (optional fallback).
   - Raw string keys and duck-typed introspection methods (`register_instance`, `resolve`) are strictly prohibited.
3. **Topological Dependency Sorting (Rule 3)**:
   - Plugins declare their dependencies in `provides` and `requires` properties.
   - The kernel lifecycle manager performs cycle detection and topologically sorts all plugins, guaranteeing dependencies are initialized before consumers.

## Verifiable Isnad Lineage
- **Source Seams**: `src/harness/kernel/context.py:20-85`, `src/harness/plugins/loader.py:60-140`.
- **Governing Invariants**: `AGENTS.md` Rule 1, Rule 2, Rule 3, Rule 45.
