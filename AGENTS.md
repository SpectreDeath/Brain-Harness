# Harness — Agent Coding Standards

## Architecture Rules

1. **Everything is a plugin.** No functionality is hardcoded into the kernel. Models, tools, storage, and agent loops are all plugins that register services into the IoC container.
2. **Service keys are typed.** Use `ServiceKey[T]` for all service registration and resolution. Never use raw strings to look up services.
3. **Plugins declare dependencies.** Every plugin must declare `provides` and `requires` lists. The lifecycle manager topologically sorts these before enabling.
4. **Events are append-only.** The event bus log is immutable. Never mutate or delete events.
5. **Subprocess isolation by default.** Untrusted (external/GitHub-sourced) plugins run in subprocess sandboxes. Only explicitly trusted plugins may use `InProcessExecutor`.
6. **Click CLI Group Single-Source Consolidation.** CLI command groups (e.g. `@main.group("bridge")`) must be declared exactly once in a single co-located block to prevent later definitions from shadowing subcommands and breaking CLI test assertions.
7. **Lazy Subprocess Staging for Sandboxed External Plugins.** External plugins with subprocess/venv isolation must remain in DISCOVERED/VALIDATED state during kernel startup and test execution, provisioning virtual environments lazily on first invocation to eliminate cold-start timeouts.
8. **ReAct Agent Step Transactional Isolation.** Agent tool invocations should execute inside context transactions (`async with context.transaction()`) with automatic rollback (`await tx.dispose()`) whenever the tool returns an error payload or raises an exception.
9. **Deterministic Pre-LLM Context Optimization.** Agent step execution loops (`StepExecutionEngine`) must apply deterministic multi-pass context pruning (whitespace deduplication, tabular/JSON payload truncation, AST code skeletonization) prior to model invocation to prevent context blowout and bound token budgets.
10. **Headless CLI Introspection Seams.** All runtime execution trees, session transcripts, and context compilation graphs must expose headless Click CLI inspection and export commands (`harness session tree`, `harness session export`) alongside API/MCP access.


## Code Style

- Python ≥ 3.10, use `|` union syntax, not `Union`.
- Type all public function signatures (`disallow_untyped_defs = true`).
- Use `structlog` for all logging.
- Use `pydantic` models for all data schemas (manifests, events, configs).
- Use `async`/`await` for all I/O-bound operations.
- Follow existing ecosystem conventions from Em-Cubed and Memtext.

## Testing

- Tests live in `tests/` mirroring `src/harness/` structure.
- Use `pytest` with `pytest-asyncio` for async tests.
- Mark tests: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`.
- Aim for ≥80% coverage on kernel and plugin system.

## File Organization

- `src/harness/kernel/` — IoC container, service registry, lifecycle (the micro-kernel)
- `src/harness/events/` — Event bus and event type definitions
- `src/harness/plugins/` — Plugin base class, manifest schema, loader, sandbox
- `src/harness/ingestion/` — GitHub → Plugin pipeline (fetcher, inspector, converter)
- `src/harness/services/` — Built-in service plugins (LLM, storage, tools)
- `plugins/` — Drop-in plugin directory for user-installed plugins
