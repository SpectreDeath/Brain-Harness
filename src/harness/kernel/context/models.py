"""Typed service keys, entry records, and container exceptions for ServiceContext."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

assert not getattr(sys.flags, "nogil", False), "COW registry requires GIL"

T = TypeVar("T")


@dataclass(frozen=True)
class ServiceKey(Generic[T]):
    """Typed key for service registration and lookup.

    Usage::

        llm_key = ServiceKey[LLMService]("llm.provider")
        ctx.provide(llm_key, my_llm_instance)
        llm = ctx.require(llm_key)  # returns LLMService
    """

    name: str

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ServiceKey):
            return self.name == other.name
        return NotImplemented

    def __repr__(self) -> str:
        return f"ServiceKey({self.name!r})"


class ServiceNotFoundError(Exception):
    """Raised when a required service is not available in the context."""

    def __init__(self, key: ServiceKey[Any]) -> None:
        self.key = key
        super().__init__(f"Required service not found: {key.name!r}")


class DuplicateServiceError(Exception):
    """Raised when trying to register a service that already exists."""

    def __init__(self, key: ServiceKey[Any]) -> None:
        self.key = key
        super().__init__(f"Service already registered: {key.name!r}")


@dataclass
class ServiceEntry:
    """An entry in the service registry tracking who provided it."""

    key: ServiceKey[Any]
    instance: Any
    provider_plugin: str | None = None
    """Name of the plugin that provided this service, or None for core."""
    is_active: bool = True
    """Whether this service is currently active in the lifecycle."""
