# Problem: Register and Resolve Typed Services

## Objective

Create a custom `ConfigService` class, define a typed `ServiceKey`, register the service in a `ServiceContext`, and resolve it safely.

## Tasks

1. Define `ConfigService` with `get(key: str, default: str = "") -> str` and `set(key: str, value: str) -> None`.
2. Define `CONFIG_KEY: ServiceKey[ConfigService] = ServiceKey("system.config")`.
3. Complete `setup_kernel()` in `main.py` to register and verify the service.
