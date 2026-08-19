# Solution: Manage Plugin Lifecycle with Dependencies

## Explanation

The solution loads `PluginA` and `PluginB` into `PluginLifecycle`. When `lifecycle.enable_all()` is executed, the lifecycle engine detects that `PluginB` requires `SERVICE_A_KEY` provided by `PluginA`, automatically topologically sorts them, and enables `PluginA` before `PluginB`.
