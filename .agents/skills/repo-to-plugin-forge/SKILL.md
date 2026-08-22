---
name: repo-to-plugin-forge
description: Bridge repository introspection via brain bridge and repo reader directly into the plugin creator to autonomously scaffold, synthesize, and validate Harness plugins from attached codebases. Use when the user asks to forge a plugin from a repo, convert a repository into a plugin, scaffold a plugin from an attached repo, or bridge an external codebase to plugin creator.
---

# Repo-to-Plugin Forge Engine

`repo-to-plugin-forge` is the autonomous bridging engine that connects external repository cognitive introspection (`plugin.brain_bridge` / `repo-reader`) directly to the Brain Harness plugin authoring system (`harness.creator.creator`, `harness.creator.schema`, and `harness.ingestion.pipeline`).

It transforms foreign libraries, GitHub repositories, CLI utilities, and OpenAPI specs into fully-typed, sandboxed, and verified Brain Harness plugins with zero manual boilerplate.

Every repo-to-plugin forging cycle follows a six-stage progression:

```
[1. Attach & AST Introspection] → [2. Archetype & Tool Schema Synthesis] → [3. The Visual Forge Brief] → [4. Mandatory Forge Checkpoint] → [5. Scaffolding & Code Synthesis] → [6. Validation & Invariant Gate]
```

See [CARD.md](CARD.md) for the quick-reference summary card, archetype decision matrix, and invariants checklist.
Consult `/crafting-skills` for skill authoring standards, `/repo-reader` for repository introspection, and `/epistemic-isnad-audit` for chain-of-custody provenance.

---

## 1. Attach & AST Introspection

Mount and interrogate the target codebase using the `plugin.brain_bridge` entrypoint:

1. **Invoke `brain_attach`**:
   - `folder_path`: Target local folder path or remote Git URL (e.g. `https://github.com/org/repo.git`).
   - `alias`: Descriptive mnemonic identifier (e.g., `target_lib`, `upstream_sdk`).
   - `read_commits`: `true` to extract commit trajectories and refactor history.
   - `attach_mode`: `"lens"` (read-only ephemeral introspection).
2. **Detect Language, Manifests & Entrypoints**:
   - Inspect package manifests (`pyproject.toml`, `setup.py`, `package.json`, `Cargo.toml`, `openapi.json`).
   - Identify candidate tool functions, classes, CLI subcommands, and export points.
3. **Log Codebase Signature**:
   - Record total lines of code, primary language, detected framework, and license.

> **Completion criterion**: Target repository attached with `status: "ok"`, primary manifest identified, and AST entrypoints indexed.

---

## 2. Archetype & Tool Schema Synthesis

Synthesize the extracted repository structure into Harness plugin contracts:

1. **Select Operational Mode & Archetype**:
   - **Mode A: Native Plugin Forge (`scaffold`)**: Use when converting clean libraries or SDKs into native Python/TypeScript Harness plugins.
     - `cli_wrapper`: Wraps external CLI binaries or scripts with typed tool arguments.
     - `tool_provider`: Extracts modular functions into `@tool` registry decorators.
     - `service_provider`: Implements a typed `ServiceKey[T]` and lifecycle provider.
     - `agent_worker`: Creates specialized debater, supervisor, or evaluator agents.
   - **Mode B: Sandboxed Ingestion (`ingest`)**: Use when encapsulating large, complex, or untrusted external codebases in subprocess sandboxes via `PluginIngestionPipeline`.
2. **Infer Parameter Schemas with `SchemaInferrer`**:
   - Execute AST analysis (`harness.creator.schema.SchemaInferrer.infer_function_signature`) to produce strict JSON Schemas for all exported tool parameters (types, descriptions, defaults, required flags).
3. **Declare Dependencies & Isolation**:
   - Resolve external dependencies (`pip`, `npm`) into `manifest.json`.
   - Set isolation mode: `IsolationMode.SUBPROCESS` (default for external repos) or `IsolationMode.IN_PROCESS` (for trusted pure utilities).

> **Completion criterion**: Archetype selected, tool list populated with complete JSON parameter schemas, and isolation mode determined.

---

## 3. The Visual Forge Brief

Synthesize the source repository AST and the target plugin topology into an interactive HTML visual brief:

1. **Target Location**: Write to `%TEMP%\repo-to-plugin-forge-<timestamp>.html` (Windows) or `/tmp/repo-to-plugin-forge-<timestamp>.html` (Unix).
2. **Visual Standards**:
   - Load Tailwind CSS and Mermaid.js via CDN in sleek dark mode (`#0d1117`).
   - Render a side-by-side **Before vs. After** Mermaid diagram:
     - **Source Repo Graph**: Modules $\rightarrow$ Classes $\rightarrow$ Functions.
     - **Target Plugin Topology**: Manifest $\rightarrow$ `ServiceKey[T]` $\rightarrow$ Tool Registry $\rightarrow$ Subprocess Sandbox.
   - Render an **Interactive Tool Schema Matrix** detailing tool names, parameter types, descriptions, and isolation boundaries.
3. **Surface**: Deliver the absolute, clickable HTML file path to the user.

```html
<!-- Location: %TEMP%\repo-to-plugin-forge-<timestamp>.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Repo to Plugin Forge Brief</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-6xl mx-auto font-sans">
  <header class="border-b border-[#30363d] pb-4 mb-6">
    <h1 class="text-2xl font-bold text-white">Repo-to-Plugin Forge Brief</h1>
    <p class="text-sm text-gray-400 mt-1">Autonomous Repository Introspection & Plugin Synthesis</p>
  </header>
  <!-- Mermaid DAG & Tool Schema Grid -->
</body>
</html>
```

> **Completion criterion**: Standalone HTML visual brief written to `%TEMP%` and delivered to user.

---

## 4. Mandatory Forge Checkpoint

Present the proposed plugin architecture, tool list, and isolation boundary to the user before writing plugin code:

1. Update or create the `implementation_plan.md` artifact detailing:
   - Target plugin folder: `plugins/<category>/<plugin_name>/`
   - Selected Archetype & Mode (Native Forge vs. Sandboxed Ingestion)
   - Exported Tools list with parameter signatures
   - Isolation Mode (`subprocess` vs `in_process`)
   - External dependencies to install
2. Set `RequestFeedback: true` in artifact metadata.
3. **STOP and wait** for explicit user review and approval.

> **Completion criterion**: User review completed; explicit sign-off received.

---

## 5. Scaffolding & Code Synthesis

Once approved, execute the automated scaffolding and code generation via `PluginCreator`:

1. **Invoke `PluginCreator.scaffold` / `PluginCreator.scaffold_archetype`**:
   ```python
   from harness.creator.creator import PluginCreator
   from harness.plugins.manifest import IsolationMode

   result = PluginCreator.scaffold(
       target_dir=f"plugins/{category}/{plugin_name}",
       name=plugin_name,
       description=description,
       language=language,
       tools=tool_names,
       dependencies=dependencies,
       preset=archetype_preset,
       isolation=IsolationMode.SUBPROCESS,
       auto_validate=True,
   )
   ```
2. **Synthesize Tool Executors & Wrappers**:
   - Generate `main.py` implementing the plugin class and mounting the extracted tools with full docstrings and typed handlers.
   - For sandboxed ingestion, generate the IPC bridge / wrapper script.
3. **Commit Provenance Metadata**:
   - Write `metadata.json` / Isnad lineage block citing the origin repository, commit hash, and source file line coordinates.

> **Completion criterion**: Plugin files scaffolded, `manifest.json` written, and tool executors implemented.

---

## 6. Validation & Invariant Gate

Subject the newly scaffolded plugin to comprehensive automated diagnostics before finalizing:

1. **Execute Diagnostic Validation**:
   - Run `PluginValidator.validate(target_dir)` to verify manifest schema, entrypoints, tool schemas, and dependency specifications.
2. **Execute Unit Tests & Lifecycle Verification**:
   - Run `pytest <plugin_dir>/test_<plugin_name>.py` or `pytest tests/ -v`.
   - Verify dynamic loading via `PluginCreator.synthesize_in_memory` or test context registration.
3. **Record in Walkthrough**:
   - Update `walkthrough.md` with the scaffolded plugin path, registered tools, and test results.

> **Completion criterion**: 100% of validation rules pass; test suite executes green with zero regressions.

---

## Anti-Patterns

- **Blind Code Copying** — Dumping raw uncurated files from an external repository directly into `plugins/` without archetype structuring or schema normalization.
- **Missing Parameter Schemas** — Registering tools with empty or unconstrained parameter schemas (`"type": "object"` with no property definitions).
- **In-Process Sandboxing of Untrusted Code** — Setting `IsolationMode.IN_PROCESS` on foreign GitHub repositories without strict isolation security reviews.
- **Unverified Tool Executors** — Generating tool handler stubs that fail at runtime when invoked by the agent.
- **Proceeding Without Plan Checkpoint** — Scaffolding plugins into the codebase before the user reviews and approves `implementation_plan.md`.
