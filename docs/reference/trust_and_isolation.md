# Trust, Isolation, and Sandboxing Architecture

This reference defines the security model, trust justifications, isolation tiers, and CLI execution postures for the Brain Harness runtime.

---

## 1. Trust Architecture & The `trusted` Flag

All plugins in the harness declare their isolation and trust posture in their manifest (`plugin.json`) and `HarnessPlugin` subclass:

* **`trusted: bool`**: Indicates whether the plugin is permitted to execute in-process within the harness micro-kernel container or whether it must be sandboxed.
* **`trust_justification: str`**: Documents the architectural and security rationale explaining why the plugin is trusted. Unjustified or untrusted plugins loaded from external/unvetted sources must never execute in-process.

### Baseline Trust Justification for First-Party Plugins

| Plugin Category | Trust Posture | Architectural Justification |
| :--- | :--- | :--- |
| **Kernel Core (`llm.*`, `storage.*`, `tools.registry`)** | `trusted: True` | Foundational harness micro-kernel services required for system operation. |
| **`token_economizer`** | `trusted: True` | Pure in-memory computation, advisory-only context pruning, no filesystem write, no network access, no host environment leaks. |
| **External Ingested Plugins** | `trusted: False` | Default untrusted. Run strictly via `SubprocessExecutor`, `VenvExecutor`, or `ContainerExecutor`. |

---

## 2. CLI-Path In-Process Execution Policy

### The 12 Subprocess-Manifest Plugins on the CLI Path
The following 12 plugins declare `isolation: "subprocess"` in their manifest for agent step execution, but are imported in-process by CLI command modules:
1. `deepselect_topk`
2. `garf_reporting_pipeline`
3. `rea_javascript`
4. `wiki_compiler`
5. `hf_doc_builder`
6. `gods_eye_view`
7. `context_compiler`
8. `memgraphrag`
9. `memory_decay_engine`
10. `rea_managed_runtime`
11. `rea_mobile_firmware`
12. `rea_native`

**Architectural Decision**:
All 12 plugins are first-party components carrying `trusted: True`. Direct in-process execution on the **CLI operator path** is intentional:
* Operator commands run interactively under the local user's terminal with immediate stdio requirements, where subprocess IPC fork overhead is undesirable.
* Conversely, when dispatched by an autonomous agent during ReAct loop execution, these tools run inside the sandboxed isolation transport configured in their manifest.

### Skill-Script Adapters
The 5 skill-script adapters (`calibrator/engine_adapter.py`, `self_eval`, `uncertainty`, `bigquery`, `compass`) adapt domain algorithms from `.agents/skills/<name>/scripts/` into Click CLI subcommands. These scripts are vetted first-party domain models and execute directly in-process when invoked via the CLI.

---

## 3. External Skill Bundles (Pocock Bundle Policy)

The bundled `mattpocock-skills` suite comprises 35 specialized engineering and documentation tools.

**Architectural Decision**:
Enabling the Pocock skill bundle is an **all-or-nothing** package operation. When enabled, all 35 entrypoints mount as a unified tool suite into `ToolRegistry`. Granular tool-level disabling is achieved after mount via `harness tool disable <name>` or programmatic `ToolRegistry.disable_tool()`.

---

## 4. Model Context Protocol (MCP) Server Posture

The Harness MCP server (`src/harness/mcp/server/`) exposes registered tools to connected MCP clients (e.g. IDE sidecars, Claude Desktop):

1. **Tool Discovery (`tools/list`)**:
   * Uses `enabled_only=True` to guarantee that only actively enabled tools are advertised.
   * Surfaces all 28 REA aliases (`rea_disassemble`, `rea_decompile`, etc.) alongside canonical names so clients discover full invocation capabilities.
2. **Tool Invocation (`tools/call`)**:
   * Any connected client may invoke any currently enabled tool. Disabled tools are rejected with code `-32603` or execution errors.
   * Alias resolution is performed transparently before dispatch.
   * As a single-user local harness, explicit per-call human confirmation is not required over MCP; instead, boundary protection is enforced by sandbox isolation and tool enablement state.

---

## 5. Configuration & Persistence Files

* **`.harness/config.json`**:
  Stores user-toggled plugin enablement states (`enabled_plugins`, `disabled_plugins`) modified via `harness plugin enable/disable`. Stale entries pointing to non-existent or deleted plugins are pruned automatically.
* **`.harness/tool_state.json`**:
  Stores user-toggled granular tool enablement states (`enabled_tools`, `disabled_tools`) modified via `harness tool enable/disable`. Loaded on kernel startup by `ToolRegistryPlugin`.

---

## 6. Nested Subprocess Execution & Binary Discovery

* **R Editor Bridge (`plugin.r_editor_bridge`)**:
  Spawns child R/Rscript processes via `asyncio.create_subprocess_exec` (`r_editor_service.py`). When running inside a parent sandbox (`SubprocessExecutor` or `ContainerExecutor`), this is nested execution bounded by the parent sandbox's limits with Rule 14 pipe cleanup and Rule 53 stderr drainage.
* **Agent Reach Bridge (`plugin.agent_reach_bridge`)**:
  Operates primarily as an in-memory Schema v1 result envelope formatter and platform channel router. Any execution of the external `agent-reach` binary verifies binary presence on PATH via `shutil.which` before execution and raises clear diagnostic errors if missing, preventing silent execution failures or unverified PATH assumptions.

---

## 7. CI, Dependencies & Extras Policy

* **Wasmtime WebAssembly Isolation**:
  `src/harness/plugins/sandbox/wasm.py` provides optional WebAssembly isolation using `wasmtime`. To maintain lean installation footprints and prevent platform-specific C-extension compile errors, `wasmtime` is an optional runtime dependency rather than a required core package. When `wasmtime` is absent, the sandbox factory automatically falls back to `SubprocessExecutor` with cooperative in-process socket controls and memory limits.
* **Docker Container Extra**:
  The `docker` extra in `pyproject.toml` (`docker>=7.0.0`) is retained for optional programmatic container management. By default, `ContainerExecutor` (`src/harness/plugins/sandbox/container.py`) shells out directly to native `docker` / `podman` CLI binaries on `PATH` with process timeouts and pipe drainage (Rule 14), eliminating in-process daemon handle leaks.
* **`uv.lock` vs CI Multi-OS Pip Installation**:
  `uv.lock` provides deterministic package pinning for local development with `uv`. CI (`.github/workflows/ci.yml`) uses standard `pip install -e ".[dev]"` to guarantee broad wheel compatibility across Ubuntu, Windows, and macOS runners.
* **Plugin Virtual Environment Requirements**:
  Individual plugins specifying local `requirements.txt` (such as `rea_native`) are provisioned lazily inside isolated subprocess virtual environments upon first invocation (Rule 7). This decouples plugin-specific libraries from kernel dependencies.
* **Code Quality & Coverage Policy**:
  CI measures test coverage across the kernel and plugins emitting JUnit and XML reports. Because optional domain suites and plugins are isolated, `--cov-fail-under` is not enforced as a hard build gate, maintaining AGENTS.md's 80% coverage target as an engineering goal. In-flight formatting is enforced on modified files (Rule 16), while CI validates syntax and structural correctness via `ruff check .`.

---

## 8. Network Isolation & Sandbox Boundaries

* **Cooperative Process-Level Network Restriction**:
  The `HARNESS_NO_NETWORK=1` flag enforces cooperative network restriction on the plugin process's own Python socket primitives (`connect`, `connect_ex`, `sendto`, `getaddrinfo`, with Windows loopback preserve per Rule 56). The network flag is cooperative for the plugin's own Python process and does not constrain child processes (e.g. `curl`, fresh `python` binaries) that it may spawn. Complete network boundary isolation for arbitrary child processes requires containerized execution (`ContainerExecutor` with `--network=none`).
