# Harness Plugin Architecture (`harness.plugins`)

The `harness.plugins` package implements the plugin lifecycle engine, manifest schema validation, dynamic discovery loader, and process sandbox transports for Brain Harness.

---

## Architecture & Design

- **Subprocess Isolation by Default (Rule 5)**: External, untrusted, or GitHub-sourced plugins run inside subprocess or venv sandboxes. Only explicitly trusted plugins run via `InProcessExecutor`.
- **Lazy Subprocess Staging (Rule 7)**: External plugins with subprocess/venv isolation remain in `DISCOVERED`/`VALIDATED` state during kernel startup, lazily provisioning virtual environments on first tool invocation.
- **Pipe Transport Disposal Invariant (Rule 14)**: Asynchronous sandbox transports explicitly drain and close stdin/stdout/stderr pipes inside `finally` blocks to guarantee clean resource disposal across OS platforms.

---

## Key Modules

| Module | Core Classes | Responsibility |
|---|---|---|
| [`base.py`](base.py) | `HarnessPlugin`, `PluginContext` | Base class defining lifecycle hooks (`on_load`, `on_enable`, `on_disable`, `on_unload`). |
| [`manifest.py`](manifest.py) | `PluginManifest`, `IsolationMode` | Pydantic v2 schema for `plugin.json` declaring dependencies, tools, and isolation levels. |
| [`loader.py`](loader.py) | `PluginLoader` | Dynamic module importer and filesystem scanner for drop-in plugin bundles. |
| [`sandbox.py`](sandbox.py) | `SubprocessSandbox`, `VenvManager` | Process isolation, venv staging, and timeout-bounded process execution. |
| [`sandboxed.py`](sandboxed.py) | `SandboxedPlugin` | Adapter wrapping sandboxed processes into standard `HarnessPlugin` interfaces. |
| [`transport.py`](transport.py) | `StdioJsonRpcTransport` | Strict JSON-RPC 2.0 framing and async pipe transport for child processes. |
| [`catalog.py`](catalog.py) | `PluginCatalog` | Searchable registry of discovered, loaded, and available plugins. |
| [`tool_mount.py`](tool_mount.py) | `ToolMounter` | Bridges plugin tools and entrypoints into the kernel `ToolRegistry`. |
| [`watcher.py`](watcher.py) | `PluginWatcher` | Hot-reloading file watcher detecting plugin modifications on disk. |

---

## Related Documentation
- [Kernel Architecture](../kernel/README.md)
- [CLI Plugin Commands](../commands/README.md)
- [User Manual](../../../USER_MANUAL.md)
