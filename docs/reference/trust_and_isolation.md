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
