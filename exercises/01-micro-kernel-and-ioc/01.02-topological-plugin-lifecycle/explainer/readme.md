# Topological Plugin Lifecycle

## Overview

Brain Harness plugins declare dependencies (`requires`) and capabilities (`provides`). When enabling a set of plugins, `PluginLifecycle` uses Kahn's algorithm for topological sorting:

```
[StoragePlugin] (provides storage.key)
       ▲
       │ requires
[DatabasePlugin] (provides database.key)
       ▲
       │ requires
[AgentPlugin]
```

## Lifecycle States

1. `DISCOVERED`: Detected by `PluginLoader`.
2. `LOADED`: Manifest parsed, `on_load(scoped_ctx)` executed.
3. `VALIDATED`: Dependencies verified in IoC container.
4. `ENABLED`: `on_enable()` called, services activated.
5. `DISABLED`: `on_disable()` called, services suspended.
6. `UNLOADED`: `on_unload()` called, services revoked from container.
