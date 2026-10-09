"""Core ServiceContext IoC container and hierarchical service registry."""

from __future__ import annotations

import threading
from collections import defaultdict
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, TypeVar

from .effects import (
    dispose_context,
    register_effect,
    subscribe_event,
)
from .interceptors import collect_interceptors, create_intercepted_context
from .lookup import (
    has_service,
    list_services,
    require_service,
    resolve_raw_service,
    set_plugin_services_active,
)
from .models import (
    ServiceEntry,
    ServiceKey,
    ServiceNotFoundError,
)
from .mutations import (
    hot_swap_service,
    provide_service,
    revoke_all_from_provider,
    revoke_service,
)
from .realms import create_isolated_context, resolve_realm

if TYPE_CHECKING:
    from .scoped import ScopedServiceContext

T = TypeVar("T")


class ServiceContext:
    """IoC container with typed service keys, parent-child scoping, and isolation realms."""

    def __init__(
        self,
        parent: ServiceContext | None = None,
        event_bus: Any | None = None,
    ) -> None:
        self._entries: dict[str, ServiceEntry] = {}
        self._parent = parent
        self._event_bus: Any | None = event_bus or (
            parent._event_bus if parent else None
        )
        self._plugin_services: dict[str, list[str]] = {}
        self._dispose_stack: list[Any] = []
        self._realms: dict[str, str] = {}
        self._interceptors: dict[str, list[Callable[[Any], Any]]] = defaultdict(list)
        self._compiled_interceptors: dict[str, Any] = {}
        self._mutation_lock = threading.RLock()
        self._teardown_epoch: int = 0
        self._interceptor_epoch: int = 0

    @property
    def parent(self) -> ServiceContext | None:
        return self._parent

    @property
    def event_bus(self) -> Any | None:
        return self._event_bus

    def attach_event_bus(self, event_bus: Any) -> None:
        self._event_bus = event_bus

    def _resolve_realm(self, key_name: str) -> str:
        return resolve_realm(self, key_name)

    def isolate(self, key: ServiceKey[Any], realm: str | None = None) -> ServiceContext:
        return create_isolated_context(self, key, realm)

    def _get_root(self) -> ServiceContext:
        curr = self
        while curr._parent is not None:
            curr = curr._parent
        return curr

    def intercept(
        self, key: ServiceKey[T], wrapper: Callable[[T], T]
    ) -> ServiceContext:
        return create_intercepted_context(self, key, wrapper)

    def _collect_interceptors(self, key_name: str) -> list[Callable[[Any], Any]]:
        return collect_interceptors(self, key_name)

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[ServiceContext]:
        from .transactions import execute_transaction

        async with execute_transaction(self) as tx_ctx:
            yield tx_ctx

    def effect(self, callback: Any) -> Any:
        return register_effect(self, callback)

    async def dispose(self) -> None:
        await dispose_context(self)

    def subscribe(self, event_type: Any, handler: Any) -> Any:
        return subscribe_event(self, event_type, handler)

    def _emit_event(
        self, event_type: Any, source: str, payload: dict[str, Any]
    ) -> None:
        if self._event_bus is not None:
            from harness.events.types import HarnessEvent

            evt = HarnessEvent(
                event_type=event_type,
                source=source,
                payload=payload,
            )
            self._event_bus.fire(evt)

    def for_plugin(self, plugin_name: str) -> ScopedServiceContext:
        from .scoped import ScopedServiceContext

        return ScopedServiceContext(self, plugin_name)

    def set_plugin_services_active(self, plugin_name: str, active: bool) -> None:
        set_plugin_services_active(self, plugin_name, active)

    def provide(
        self,
        key: ServiceKey[T],
        instance: T,
        *,
        provider: str | None = None,
        allow_override: bool = False,
    ) -> None:
        provide_service(
            self, key, instance, provider=provider, allow_override=allow_override
        )

    def require(self, key: ServiceKey[T]) -> T:
        return require_service(self, key)

    def _resolve_raw_service(self, key: ServiceKey[T], target_realm: str) -> T:
        return resolve_raw_service(self, key, target_realm)

    def optional(self, key: ServiceKey[T]) -> T | None:
        try:
            return self.require(key)
        except ServiceNotFoundError:
            return None

    def has(self, key: ServiceKey[Any]) -> bool:
        return has_service(self, key)

    def revoke(self, key: ServiceKey[Any]) -> bool:
        return revoke_service(self, key)

    def hot_swap(
        self,
        key: ServiceKey[T],
        new_instance: T,
        *,
        provider: str | None = None,
    ) -> None:
        hot_swap_service(self, key, new_instance, provider=provider)

    def revoke_all_from(self, provider: str) -> list[str]:
        return revoke_all_from_provider(self, provider)

    def child(self) -> ServiceContext:
        return ServiceContext(parent=self)

    def list_services(self) -> dict[str, str | None]:
        return list_services(self)

    def __contains__(self, key: ServiceKey[Any]) -> bool:
        return self.has(key)

    def __repr__(self) -> str:
        local_count = len(self._entries)
        parent_info = f", parent={self._parent!r}" if self._parent else ""
        return f"ServiceContext(services={local_count}{parent_info})"
