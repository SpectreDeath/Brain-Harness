# Harness — Agent Coding Standards

## Architecture Rules

1. **Everything is a plugin.** No functionality is hardcoded into the kernel. Models, tools, storage, and agent loops are all plugins that register services into the IoC container.
2. **Service keys are typed.** Use `ServiceKey[T]` for all service registration and resolution. Never use raw strings to look up services.
3. **Plugins declare dependencies.** Every plugin must declare `provides` and `requires` lists. The lifecycle manager topologically sorts these before enabling.
4. **Events are append-only.** The event bus log is immutable. Never mutate or delete events.
5. **Subprocess isolation by default.** Untrusted (external/GitHub-sourced) plugins run in subprocess sandboxes. Only explicitly trusted plugins may use `InProcessExecutor`.

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
