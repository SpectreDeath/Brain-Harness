"""Exercise 01.01: Service Keys and Service Context (Solution)."""

from __future__ import annotations

from harness.kernel.context import ServiceContext, ServiceKey


class ConfigService:
    def __init__(self) -> None:
        self._entries: dict[str, str] = {}

    def get(self, key: str, default: str = "") -> str:
        return self._entries.get(key, default)

    def set(self, key: str, value: str) -> None:
        self._entries[key] = value


CONFIG_KEY: ServiceKey[ConfigService] = ServiceKey("system.config")


def setup_kernel() -> ServiceContext:
    ctx = ServiceContext()
    config_service = ConfigService()
    ctx.provide(CONFIG_KEY, config_service, provider="config.plugin")
    return ctx
