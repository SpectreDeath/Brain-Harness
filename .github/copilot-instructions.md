<!-- Generated from AGENTS.md by `python scripts/sync_context.py`. Edit AGENTS.md instead. -->

# Harness — Agent Coding Standards

> Full rulebook (`Rules 1–59`): read [Agent Coding Invariants](docs/reference/agent-invariants.md) on demand when authoring plugins, skills, CLI commands, subprocess sandboxes, Knowledge Vault items, or Windows runner scripts.

## Core Architecture Rules

1. **Everything is a plugin.** Register models, tools, storage, and agent loops into the IoC container; never hardcode features into the kernel.
2. **Service keys are typed.** Use `ServiceKey[T]` (`context.provide(key, instance)`, `context.require(key)`, `context.optional(key)`), typed `@runtime_checkable` protocols, and non-invasive adapters (`Rule 19`, `Rule 58`).
3. **Plugins declare dependencies & export singletons.** Subclass `HarnessPlugin`, declare `provides` and `requires`, and export `plugin = MyPlugin()` (`Rule 3`, `Rule 45`). Untrusted external plugins stay subprocess-isolated and lazily staged (`Rules 5, 7`).
4. **Events are append-only & ReAct steps are transactional.** Never mutate the event log; execute tool calls inside `async with context.transaction()` with rollback on error (`Rules 4, 8`).
5. **Single-source Click consolidation & clean data models.** Declare each Click group once (`Rule 6`); use `@dataclass(slots=True, frozen=True)` for immutable value types (`Rule 12`).
6. **Lean context files & verify before editing.** Keep root instruction files under 150 lines (`Rule 11`), inspect DAG seams before editing (`Rule 13`), run in-flight lint/tests (`Rule 16`), and drain subprocess pipes inside `finally` (`Rules 14, 53`).

## Quick Start & Developer Loop

- **Install**: `uv pip install -e ".[dev]"`
- **Test (Targeted)**: `.\.venv\Scripts\python.exe -m pytest tests/test_<module>.py -v` (or `-k "<pattern>"` on PowerShell; `Rule 30`)
- **Test (Full unit)**: `.\.venv\Scripts\python.exe -m pytest -m "unit" -q --timeout=60`
- **Lint & Format**: `.\.venv\Scripts\ruff.exe check .` and `.\.venv\Scripts\ruff.exe format --check ...`
- **Context Lint & Sync**: `.\.venv\Scripts\harness.exe context lint --root .` and `.\.venv\Scripts\harness.exe context sync --root .`
- **Knowledge Vault Sync**: `.\.venv\Scripts\harness.exe knowledge sync --strict`

## Negative Boundaries & Windows Guardrails

- **What NOT to Touch**: Never manually edit `.pytest_cache/`, `src/harness/ui/static/`, or persistent SQLite memory stores without transactions.
- **Dependency & Security Guardrails**: Never add `pyproject.toml` dependencies without approval; never push or run `git reset --hard` / `git clean -fd`; never pass tokens via shell interpolation (`Rule 15`).
- **Windows PowerShell Rules**: Set `PYTHONIOENCODING=utf-8` (`Rule 23`), never use bare `>` redirects for machine-parsed logs (`Rule 26`), write multi-line Python to scratch files instead of inline `-c` (`Rule 29`), and use relative links (no workspace file URIs) in docs (`Rule 47`).

## Code Style & Layout

- Python ≥ 3.10 (`|` unions, typed public functions, `structlog`, `pydantic`, `async`/`await`).
- Tests in `tests/` (`test_kernel_*`, `test_service_*`, `test_plugin_*`, `test_command_*`, `test_agent_*`, `test_ingestion_*`) marked with `@pytest.mark.unit`, `@pytest.mark.integration`, or `@pytest.mark.slow`.
- Layout: `src/harness/` (`kernel`, `events`, `plugins`, `ingestion`, `services`, `agent`, `creator`, `commands`, `bridges`, `mcp`, `ui`), `plugins/`, `docs/`, `.agents/skills/`, `.harness/`.
