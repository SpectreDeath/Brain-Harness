"""Exercise 01.01: Service Keys and Service Context (Problem)."""

from __future__ import annotations

from harness.kernel.context import ServiceContext, ServiceKey


class ConfigService:
    def __init__(self) -> None:
        self._entries: dict[str, str] = {}

    def get(self, key: str, default: str = "") -> str:
        # TODO: Return value for key, or default if not present
        raise NotImplementedError

    def set(self, key: str, value: str) -> None:
        # TODO: Store key and value
        raise NotImplementedError


# TODO: Define CONFIG_KEY with type ConfigService
CONFIG_KEY: ServiceKey[ConfigService] = None  # type: ignore[assignment]


def setup_kernel() -> ServiceContext:
    ctx = ServiceContext()
    # TODO: Instantiate ConfigService and provide it to ctx under CONFIG_KEY
    return ctx
