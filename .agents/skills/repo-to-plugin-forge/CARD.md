# 🧠 Skill Summary Card: `repo-to-plugin-forge`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        repo-to-plugin-forge                      │
│ Category:    engineering / plugin-generation           │
│ Invocation:  /repo-to-plugin-forge                     │
│ Trigger:     "forge plugin from repo",                 │
│              "convert repo to plugin",                 │
│              "scaffold plugin from attached repo",     │
│              "bridge repo to plugin creator"           │
│ Version:     1.0.0                                     │
│ Requires:    "repo-reader", "crafting-skills"          │
│ Provides:    "plugin_forging"                          │
├────────────────────────────────────────────────────────┤
│ Target:      Bridge repository AST introspection into  │
│              PluginCreator to forge verified plugins.  │
└────────────────────────────────────────────────────────┘
```

---

## 🔄 The 6-Stage Loop at a Glance

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Attach & AST** | Mount repo via `brain_attach` & index classes/functions | AST Index & Manifest | Repo attached `status: "ok"` & entrypoints indexed |
| **2. Archetype & Schemas** | Map to archetype & infer JSON tool parameter schemas | Schema Mapping & Preset | Archetype selected & parameter schemas generated |
| **3. Visual Brief** | Generate interactive HTML with before/after Mermaid DAG | `%TEMP%\repo-to-plugin-forge-*.html` | Temp HTML report written & path surfaced |
| **4. Checkpoint** | Present plugin layout, isolation mode & tool specs | `implementation_plan.md` | User review & explicit approval |
| **5. Scaffolding** | Synthesize plugin files, tool handlers & manifest | `PluginCreator.scaffold()` | Plugin files & tool handlers generated |
| **6. Validation & Gate**| Run `PluginValidator`, unit tests & hot-reload verification | `pytest` & `walkthrough.md` | **100% pass rate** on validation & tests |

---

## 🧰 Vocabulary & Archetype Cheat Sheet

- **Native Forge (Mode A)**: Translating repository libraries into native Harness plugins with first-class `@tool` registrations.
- **Sandboxed Ingestion (Mode B)**: Wrapping complex/untrusted external codebases in subprocess sandboxes with auto-generated IPC bridges.
- **`cli_wrapper` Archetype**: Wraps CLI command-line tools into deterministic agent tools.
- **`tool_provider` Archetype**: Standard tool library exposing domain functions to agent workflows.
- **`service_provider` Archetype**: Long-running background service registering a typed `ServiceKey[T]`.
- **`agent_worker` Archetype**: Specialized autonomous agent (debater, critic, supervisor, planner).
- **`SchemaInferrer`**: AST engine that automatically extracts types, docstrings, and defaults into JSON Schema.

---

## 🚫 Anti-Patterns Cheat Sheet

- **Blind Code Copying**: Dumping raw uncurated files from external repositories without archetype structuring.
- **Missing Parameter Schemas**: Registering tools with empty or unconstrained parameter schemas.
- **In-Process Sandboxing of Untrusted Code**: Setting in-process execution on external repos without security review.
- **Unverified Tool Executors**: Generating tool handler stubs that fail at runtime when invoked.

---

## 🛡️ Guardrails & Invariants

- [ ] **Mandatory Subprocess Isolation**: Always enforce `IsolationMode.SUBPROCESS` for untrusted or external GitHub repositories.
- [ ] **Strict Tool Parameter Schemas**: Every exported tool must have typed parameter properties and descriptions (no empty schemas).
- [ ] **Pre-Commit Plan Checkpoint**: Never scaffold code without explicit user sign-off on `implementation_plan.md`.
- [ ] **Zero-Error Diagnostic Validation**: The scaffolded plugin must pass 100% of `PluginValidator` rules before completion.
- [ ] **Cryptographic Lineage**: Plugin metadata must record source repository provenance, commit hash, and file coordinates.
- [ ] **Visual Brief Delivery**: Always emit an interactive `%TEMP%` HTML report with Before/After Mermaid DAG before code modification.
