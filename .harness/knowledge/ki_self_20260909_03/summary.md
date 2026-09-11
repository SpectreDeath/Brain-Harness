## Plugin Module Singleton & IoC Container Dynamic Loader Invariant

### Problem
The Harness dynamic plugin loader (`src/harness/plugins/loader.py`) discovers and loads plugins by inspecting entrypoint Python modules (`plugins/<category>/<plugin_name>/main.py`). The loader relies on finding an instantiated `HarnessPlugin` object exported at the module root:
`plugin = MyPlugin()`

If a developer or code-generation agent writes a plugin entrypoint as standalone functions, classes without instantiation, or omits `plugin = ...`:
1. The dynamic loader fails to register the plugin into the IoC container.
2. Services declared in `provides` are never registered into `ServiceContext`.
3. Downstream agent loops requesting `context.require(SERVICE_KEY)` raise `KeyError` or fail at runtime.

### Invariant Contract
Every plugin implementation entrypoint (`plugins/<category>/<name>/main.py`) must:
1. Subclass `HarnessPlugin`.
2. Declare typed service keys in its `provides` property list.
3. Register service instances in `on_load(context)` via `context.provide(KEY, instance)`.
4. **Explicitly export an instantiated module-level singleton**:
   ```python
   plugin = MyPlugin()
   ```

### Codification
- **Rule 45 (AGENTS.md)**: Plugin Module Singleton & IoC Provider Invariant.
- Plugin validators (`PluginValidator`) and architectural linters must verify `hasattr(module, 'plugin')` and `isinstance(module.plugin, HarnessPlugin)`.
