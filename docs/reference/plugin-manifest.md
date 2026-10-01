# Plugin Manifest Reference (`plugin.json`)

The `plugin.json` file is the declarative manifest required in the root directory of every Brain Harness plugin. It specifies plugin metadata, entrypoints, IoC dependencies, and sandboxing requirements.

---

## Example `plugin.json` Manifest

```json
{
  "name": "my_analytics",
  "version": "1.0.0",
  "category": "data_engineering",
  "description": "High-throughput dataset profiling and causal anomaly detection.",
  "entrypoint": "main.py",
  "provides": [
    "data_engineering.my_analytics"
  ],
  "requires": [
    "core.storage"
  ],
  "trusted": true,
  "sandbox": {
    "type": "in_process",
    "timeout_seconds": 60,
    "memory_limit_mb": 512
  }
}
```

---

## Manifest Field Specifications

| Field | Type | Mandatory | Description |
|---|---|---|---|
| `name` | `string` | **Yes** | Unique identifier for the plugin (alphanumeric and underscores). |
| `version` | `string` | **Yes** | Semantic version string (e.g. `"1.0.0"`). |
| `category` | `string` | **Yes** | One of the 11 domain categories (e.g. `data_engineering`, `agent_orchestration`). |
| `description` | `string` | **Yes** | Concise statement of the plugin's central function and capabilities. |
| `entrypoint` | `string` | **Yes** | Relative path to execution script (e.g. `"main.py"`). |
| `provides` | `list[string]` | **Yes** | Service keys registered into the IoC container upon loading. |
| `requires` | `list[string]` | **Yes** | Service keys required before this plugin can transition to `ENABLED`. |
| `trusted` | `boolean` | No | Defaults to `false`. If `false`, executes in an isolated subprocess. |
| `sandbox` | `object` | No | Advanced sandboxing configuration (timeouts, memory boundaries). |

---

## Domain Categories

Plugins must declare one of the following 11 canonical domain categories (Rule 18):
- `agent_orchestration`
- `ai_native_harness`
- `data_engineering`
- `developer_tooling`
- `ecosystem_bridges`
- `infra_and_cloud`
- `integration_and_io`
- `memory_and_epistemics`
- `science_and_biology`
- `security_and_forensics`
- `software_engineering`

---

## Lifecycle States & State Transitions

Brain Harness validates and manages plugins through a 6-state lifecycle:

```
[DISCOVERED] ──► [VALIDATED] ──► [LOADED] ──► [ENABLED]
                                   │              │
                                   ▼              ▼
                               [FAILED]     [DISABLED]
```

1. **DISCOVERED**: The directory and `plugin.json` exist on disk.
2. **VALIDATED**: Passed AST signature verification, schema assertions, and security checks.
3. **LOADED**: Services registered into IoC container via `context.provide()`.
4. **ENABLED**: All `requires` dependencies resolved; tools registered in `ToolRegistry`.
5. **DISABLED**: Inactive; services revoked and tools detached.
6. **FAILED**: Encountered runtime exception during initialization.

---

## Zero-Fork Default Configuration (`config.default.yaml`)

Production plugins provide a co-located `config.default.yaml` defining baseline operational budgets (timeouts, token bounds, retry limits) for 3-tier zero-fork configuration (Rule 44):

```yaml
# config.default.yaml
timeout_seconds: 30
max_retries: 3
token_budget: 10000
cache_ttl_seconds: 3600
```

---

## Validation Rules & Architectural Invariants

When executing `harness creator validate <path>`, the plugin validator asserts:
- **`ManifestSchemaRule`**: All mandatory fields present and strictly typed.
- **`DirectoryExistenceRule`**: Standard layout exists.
- **`EntrypointFileRule`**: File declared in `entrypoint` exists on disk.
- **`AstSignatureMatchingRule`**: Entrypoint declares `on_load(context)` accepting `ServiceContext`.
- **`PluginModuleSingleton` (Rule 45)**: Entrypoint subclasses `HarnessPlugin` and exports `plugin = MyPlugin()`.
