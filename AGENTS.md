# Harness — Agent Coding Standards

## Architecture Rules

1. **Everything is a plugin.** No functionality is hardcoded into the kernel. Models, tools, storage, and agent loops are all plugins that register services into the IoC container.
2. **Service keys are typed.** Use `ServiceKey[T]` for all service registration and resolution. Never use raw strings to look up services.
3. **Plugins declare dependencies.** Every plugin must declare `provides` and `requires` lists. The lifecycle manager topologically sorts these before enabling.
4. **Events are append-only.** The event bus log is immutable. Never mutate or delete events.
5. **Subprocess isolation by default.** Untrusted (external/GitHub-sourced) plugins run in subprocess sandboxes. Only explicitly trusted plugins may use `InProcessExecutor`.
6. **Click CLI Group Single-Source Consolidation.** CLI command groups (e.g. `@main.group("bridge")`) must be declared exactly once in a single co-located block to prevent later definitions from shadowing subcommands and breaking CLI test assertions.
7. **Lazy Subprocess Staging for Sandboxed External Plugins.** External plugins with subprocess/venv isolation must remain in DISCOVERED/VALIDATED state during kernel startup and test execution, provisioning virtual environments lazily on first invocation to eliminate cold-start timeouts.
8. **ReAct Agent Step Transactional Isolation & Workspace Checkpoints.** Agent tool invocations execute inside context transactions (`async with context.transaction()`). On success, the transaction creates an atomic Git checkpoint via `FilesystemGitService.commit_transaction()`. If the tool returns an error payload or raises an exception, the transaction triggers automatic rollback (`await tx.dispose()`) and workspace restoration (`rollback_transaction()`).
9. **Deterministic Pre-LLM Context Optimization & AST RepoMap.** Agent step execution loops (`StepExecutionEngine`) must apply deterministic multi-pass context pruning (whitespace deduplication, progressive middle-out tool reduction, tabular/JSON truncation) and dynamic PageRanked AST Repo Map injection (`RepoMapService`) prior to model invocation to prevent context blowout and bound token budgets.
10. **Headless CLI Introspection Seams.** All runtime execution trees, session transcripts, and context compilation graphs must expose headless Click CLI inspection and export commands (`harness session tree`, `harness session export`) alongside API/MCP access.
11. **Agent Instruction File Hygiene & Negative Boundaries.** Repository agent configuration files (`AGENTS.md`, `CLAUDE.md`) must remain lean (<150 lines), free of generic tutorials or lint leakage, and define explicit execution seams (build/test/lint) along with strict negative boundaries ("what NOT to touch").
12. **Slotted & Frozen Dataclass Architecture.** High-volume internal entity and AST data structures must use `slots=True` to minimize memory footprint, `frozen=True` for immutable value objects, `__post_init__` construction assertions, and `default_factory` for mutable collections.
13. **Inspect-Before-Edit & Seam Verification Protocol.** Agents must never prematurely modify code without first mapping DAG component seams, authoring failing test contracts, and validating changes against strict git diffs.
14. **Subprocess Pipe Transport Disposal Invariant.** All asynchronous subprocess sandbox transports must explicitly drain and close stdin/stdout/stderr pipes inside `finally` blocks to guarantee clean proactor resource disposal across operating systems.
15. **Secure Credential Injection & Runner Isolation.** When executing authenticated operations (e.g. git push with tokens), never use shell string variable interpolation. Use isolated Python runner scripts or standard input pipes to prevent shell expansion parse errors and credential exposure.
16. **In-Flight Lint-After-Edit Self-Repair.** File write and edit tool executions must immediately run fast syntax and diagnostic verification (`ArchLinterService.lint_file()`), appending any detected syntax or bracket balance errors directly into the tool observation for in-flight self-repair before transaction finalization.
17. **Authoritative Thread DAG & Execution Graph Lifecycle.** Multi-agent swarms and hierarchical sub-agent executions must track lifecycle states (`Open`, `Closed`, `Completed`, `Failed`) along directional spawn edges via `AgentExecutionGraphService` (`AGENT_GRAPH_STORE_KEY`), maintaining automated token rollups and deterministic ASCII/JSON tree export seams.
18. **Domain-Partitioned Plugin Synthesis.** Multi-capability codebase bridges or monorepo ingestions must never bundle disparate tools into a single monolithic plugin. Partition tools across single-responsibility plugins co-located in their respective category directories (`agent_orchestration`, `data_engineering`, `security_and_forensics`).
19. **Non-Invasive Kernel Extensibility.** When introducing architectural abstractions or scope metadata, use non-invasive adapters, metadata decorators, or read-only inspectors rather than mutating core `ServiceContext` constructor contracts or IoC lifecycle signatures.
20. **In-Place Deepening over Tool Sprawl.** When foreign codebases or research reveal advanced domain patterns (e.g. recursive AST shell security gates), deepen existing foundational plugins in-place rather than spawning parallel duplicate tool wrappers.


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
- `src/harness/plugins/` — Plugin base class, manifest schema, loader, sandbox transports
- `src/harness/ingestion/` — GitHub → Plugin pipeline (fetcher, inspector, converters)
- `src/harness/services/` — Built-in service plugins (LLM, storage, tools, skill graph)
- `src/harness/agent/` — Autonomous ReAct agent loop, step execution engine, multi-agent coordination
- `src/harness/creator/` — Dynamic plugin scaffolding, archetypes, and validation/remediation engine
- `src/harness/commands/` — Modular CLI command implementations
- `src/harness/bridges/` — Ecosystem bridges (Em-Cubed, Memtext, Skill Flywheel)
- `src/harness/mcp/` — Model Context Protocol (MCP) server & client
- `src/harness/ui/` — Web dashboard server and real-time WebSocket telemetry
- `plugins/` — Drop-in plugin directory for user-installed plugins
