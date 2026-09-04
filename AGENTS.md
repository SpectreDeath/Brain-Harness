# Harness — Agent Coding Standards

## Architecture Rules

1. **Everything is a plugin.** No functionality is hardcoded into the kernel. Models, tools, storage, and agent loops are all plugins that register services into the IoC container.
2. **Service keys are typed.** Use `ServiceKey[T]` for all service registration (`context.provide(key, instance)`) and resolution (`context.require(key)` or `context.optional(key)`). Never use raw strings or non-existent methods (`register_instance`, `resolve`).
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
15. **Secure Credential Injection & Runner Isolation.** When executing authenticated operations (e.g. git push with tokens), never use shell string variable interpolation. Use isolated Python runner scripts or standard input pipes to prevent shell expansion parse errors and credential exposure. When configuring custom git credential helpers via `-c credential.helper="..."`, always prefix commands with `!` (`!python <path>`), otherwise git prepends `git-credential-`. In headless runners, pass authenticated URLs via isolated argv lists with immediate in-memory log redaction.
16. **In-Flight Lint-After-Edit Self-Repair.** File write and edit tool executions must immediately run fast syntax and diagnostic verification (`ArchLinterService.lint_file()`), appending any detected syntax or bracket balance errors directly into the tool observation for in-flight self-repair before transaction finalization.
17. **Authoritative Thread DAG & Execution Graph Lifecycle.** Multi-agent swarms and hierarchical sub-agent executions must track lifecycle states (`Open`, `Closed`, `Completed`, `Failed`) along directional spawn edges via `AgentExecutionGraphService` (`AGENT_GRAPH_STORE_KEY`), maintaining automated token rollups and deterministic ASCII/JSON tree export seams.
18. **Domain-Partitioned Plugin Synthesis.** Multi-capability codebase bridges or monorepo ingestions must never bundle disparate tools into a single monolithic plugin. Partition tools across single-responsibility plugins co-located in their respective category directories (`agent_orchestration`, `data_engineering`, `security_and_forensics`).
19. **Non-Invasive Kernel Extensibility.** When introducing architectural abstractions or scope metadata, use non-invasive adapters, metadata decorators, or read-only inspectors rather than mutating core `ServiceContext` constructor contracts or IoC lifecycle signatures.
20. **In-Place Deepening over Tool Sprawl.** When foreign codebases or research reveal advanced domain patterns (e.g. recursive AST shell security gates), deepen existing foundational plugins in-place rather than spawning parallel duplicate tool wrappers.
21. **In-Flight Tool-Call Stream Normalization & Promotion.** Tool-calling interfaces and stream parsers must intercept plain-text model codeblocks (JSON fences, XML `<tool_call>` tags) and auto-repair syntax errors (trailing commas, unclosed brackets) in-flight before step execution failure.
22. **Multi-Store Autobiographical Memory Federation.** Agents querying active session stores must connect via read-only SQLite URI modes (`file:...?mode=ro`) to prevent lock contention with worker proactors, federating streaming JSONL parsers for trajectory step history.
23. **Windows UTF-8 Stream Codec Entrypoint Invariant.** All CLI commands, subprocess runners, and background extractors on Windows environments must explicitly configure standard streams to UTF-8 (`sys.stdout.reconfigure(encoding='utf-8')` or `PYTHONIOENCODING=utf-8`) to prevent `cp1252` encoding crashes on Unicode DAG symbols.
24. **Stateless MCP Scientific Tool Isolation.** Heavy domain simulation engines, ODE parameter solvers, and external API pipelines must be encapsulated behind stateless Model Context Protocol (MCP 2026-07-28) servers with JSONSchema validation rather than in-process stateful singleton bindings.
25. **Dynamic 5D Compute Complexity & Reasoning Escalation.** High-scale multi-agent swarms or large repository audits scoring composite 5D complexity (Span, Depth, Concurrency, Rigor, Domain Heterogeneity) $\ge 0.75$ must automatically lock model reasoning budgets to High and scale async subprocess timeouts to 300s+.
26. **Machine-Parsed Stream Piping & Anti-Redirection Invariant.** Never rely on bare PowerShell `>` redirects for machine-parsed logs; always enforce UTF-8 streams (`| Out-File -Encoding utf8`) or native subprocess standard output piping to prevent UTF-16 LE BOM null-byte corruptions.
27. **NLP & Text Stylometry Corpus Token Length Assertion.** Always normalize document filenames and assert non-zero token length across train and test corpora before executing statistical delta distance matrix calculations (`calculate_burrows_delta`).
28. **Forensic Extension Mock Isolation.** Forensic and security extensions must provide self-contained contract verification tests using mocked DAL/Nexus adapters before integration.
29. **Scratch File Execution over Inline `-c` Strings.** Never execute multi-line Python logic via `python -c "..."` in PowerShell commands. Always write to a scratch file (`<artifact_dir>/scratch/<name>.py`) and execute it with `python <path>`. Inline `-c` strings break on f-string braces, nested quotes, and PowerShell escape sequences.
30. **PowerShell Glob Non-Expansion Workaround.** PowerShell does not expand `*` globs in command arguments the way bash does. When running pytest with file pattern matching, use `pytest -k "<pattern>"` keyword filtering instead of `pytest tests/test_*.py` glob paths. For other tools, pipe from `Get-ChildItem -Filter` or use explicit file lists.
31. **Artifact Metadata Restricted to Artifact Directory.** The `write_to_file` tool only accepts `ArtifactMetadata` for files inside the conversation artifact directory. When scaffolding plugin files, test files, or any workspace code, either omit `ArtifactMetadata` or use `run_command` with a Python writer script to create the files.
32. **Defensive Batch Exception Visibility.** In batch-processing loops (directory scanners, metadata loaders, skill/plugin indexers), never use bare `except Exception: continue` without logging. Always log unexpected errors at `logger.debug()` or `logger.warning()`, or explicitly reraise programming errors (`NameError`, `TypeError`, `AttributeError`) so that missing imports and schema bugs fail loudly during testing rather than masking as empty results.
33. **JSON Null-Field Fallback Invariant.** When extracting optional collections (lists, dicts) from JSON or YAML metadata dictionaries, never rely on `dict.get("key", [])` because explicit JSON `null` values return `None`. Always use `dict.get("key") or []` (or `dict.get("key") or {}`) to ensure safe iteration and membership checks.
34. **ValidationReport & Diagnostic Object Interface Invariant.** When consuming validator or diagnostic reports (`SkillValidator.validate()`, `PluginValidator.validate()`), never assume a top-level `.passed` attribute exists. Always evaluate the overall boolean status via `report.valid` and inspect granular rule executions through the `report.checks` collection (where each item contains `check.rule`, `check.passed`, and `check.message`).
35. **Skill Router Dictionary Key & Catalog Resolution Invariant.** When querying the skill knowledge graph via `query_skill_router()`, match entries are strictly keyed by `'skill_name'`, never `'skill'`. Callers must access match names using `match["skill_name"]` (or safe fallback `match.get("skill_name") or match.get("name")`). Furthermore, `index_skill_catalog()` returns an indexing summary dictionary; to access registered graph nodes directly, query `graph.nodes` or `_GRAPH_INSTANCE.nodes`.
36. **Swarm Thread DAG Keying & Session Manager Contract Invariant.** When registering or looking up swarm wave nodes in `AgentExecutionGraphService` or `AgentSessionManager`, node thread identifiers must use the composite key `f"{run_id}_{node_id}"` to prevent cross-run collisions. In `AgentSessionManager`, session creation requires `task: str` as the primary argument (not `agent_name` or `goal`), session completion requires `final_answer: str` (not `summary`), and session failure requires `error_message: str` (not `error`).
37. **Skill Knowledge Graph Parser & ASCII Card Formatting Invariant.** When authoring `CARD.md` and `SKILL.md` files, `CARD.md` metadata boxes must use standard single-pipe borders (`│`, not `║`) so `SkillCardParser._extract_ascii_card()` cleanly strips delimiters when extracting `Name:`, `Category:`, and `Triggers:`. Furthermore, `SKILL.md` must declare anti-patterns under an exact `## Anti-Patterns` heading containing list items formatted as `- **Name** — Description`.
38. **PluginValidator Coroutine & Dual-Mode Invocation Invariant.** `PluginValidator.validate()` is an asynchronous coroutine (`async def validate()`). In synchronous test methods or scripts, callers must invoke `PluginValidator.validate_sync()` or mark the test with `@pytest.mark.asyncio` and `await PluginValidator.validate()` to prevent unawaited coroutine errors on `report.valid`.
39. **Third-Party Engine Dual-API & Mock Spec Invariant.** When wrapping external libraries subject to interface evolution (e.g. `youtube-transcript-api` v0.6+ static functions vs v1.2+ `YouTubeTranscriptApi().fetch()` instance methods), adapters must dynamically support both paradigms. In mock test fixtures, evaluate classic method existence before new instance methods or declare `spec=ClassName` to prevent unconfigured `MagicMock` attributes from hijacking execution paths.



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
