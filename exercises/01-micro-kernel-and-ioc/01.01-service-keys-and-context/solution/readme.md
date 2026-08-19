# Solution: Register and Resolve Typed Services

## Explanation

The solution defines `ConfigService` with standard dictionary backing, creates a typed `ServiceKey[ConfigService]("system.config")`, and registers it via `ctx.provide(CONFIG_KEY, config, provider="config.plugin")`.

```python
config = ctx.require(CONFIG_KEY)
config.set("env", "production")
assert config.get("env") == "production"
```
