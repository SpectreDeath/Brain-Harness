"""Service context — IoC container with typed service keys.

The ServiceContext is the heart of the harness. Plugins register services
into the context using typed ServiceKeys, and resolve dependencies from it.

Supports parent-child context trees for scoped plugin isolation:
a child context inherits services from its parent but can override them
locally without affecting siblings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar, cast

import structlog

import uuid
from collections import defaultdict
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

logger = structlog.get_logger()

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


class ServiceContext:
    """IoC container with typed service keys, parent-child scoping, and isolation realms.

    The context holds all services available in the harness. Plugins
    receive a reference to the context and use it to:

    1. **Provide** services they implement (on ``on_load``)
    2. **Require** services they depend on (on ``on_enable``)

    When a plugin is unloaded, all services it provided are automatically
    revoked — this is the "spatiotemporal composability" concept from Cordis.
    """

    def __init__(
        self,
        parent: ServiceContext | None = None,
        event_bus: Any | None = None,
    ) -> None:
        self._entries: dict[str, ServiceEntry] = {}
        self._parent = parent
        self._event_bus: Any | None = event_bus or (parent._event_bus if parent else None)
        # Track which plugin provided which services (for automatic revocation)
        self._plugin_services: dict[str, list[str]] = {}
        # Accumulator φ: LIFO stack of inverse operations (Revertible Effects, Definition 2)
        self._dispose_stack: list[Any] = []
        # Isolation Realms table ρ: K ⇀ R (Coeffect Isolation, Definition 28)
        self._realms: dict[str, str] = {}
        # Interception table ι: (k: K) → list[wrapper] (Coeffect Interception, Definition 30)
        self._interceptors: dict[str, list[Callable[[Any], Any]]] = defaultdict(list)

    @property
    def parent(self) -> ServiceContext | None:
        """Parent context, if this is a child scope."""
        return self._parent

    @property
    def event_bus(self) -> Any | None:
        """Event bus attached to this context, if any."""
        return self._event_bus

    def attach_event_bus(self, event_bus: Any) -> None:
        """Attach an event bus to observe service container mutations."""
        self._event_bus = event_bus

    def _resolve_realm(self, key_name: str) -> str:
        """Resolve a service key through the realm mapping ρ (Definition 28)."""
        if key_name in self._realms:
            return self._realms[key_name]
        if self._parent is not None:
            return self._parent._resolve_realm(key_name)
        return key_name

    def isolate(self, key: ServiceKey[Any], realm: str | None = None) -> ServiceContext:
        """Derive a child context with an isolated coeffect realm for *key* (Definition 29).

        When components in the derived context provide or require *key*, the lookup
        is redirected to the isolated realm without mutating or observing sibling realms.
        """
        child_ctx = self.child()
        target_realm = realm or f"{key.name}:isolated_{uuid.uuid4().hex[:8]}"
        child_ctx._realms[key.name] = target_realm
        return child_ctx

    def intercept(
        self, key: ServiceKey[T], wrapper: Callable[[T], T]
    ) -> ServiceContext:
        """Derive a child context with cross-cutting coeffect interception (Definition 31).

        Attaches capability policies (e.g. read-only wraps, rate limits, telemetry)
        applied dynamically whenever components in the derived context require *key*.
        """
        child_ctx = self.child()
        child_ctx._interceptors[key.name].append(cast(Callable[[Any], Any], wrapper))
        return child_ctx

    def _collect_interceptors(self, key_name: str) -> list[Callable[[Any], Any]]:
        """Collect all interceptors along the context hierarchy."""
        chain: list[Callable[[Any], Any]] = []
        if self._parent is not None:
            chain.extend(self._parent._collect_interceptors(key_name))
        chain.extend(self._interceptors.get(key_name, []))
        return chain

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[ServiceContext]:
        """Execute operations within a transactional effect boundary (Definition 51 & 52).

        If any error occurs within the context block, all effects registered
        during the transaction are rolled back in LIFO order (Theorem 61).
        On success, the entries and inverses are committed and merged into the parent accumulator.
        """
        tx_ctx = self.child()
        try:
            yield tx_ctx
            # Commit: merge transaction entries, services, and effects into parent context
            self._entries.update(tx_ctx._entries)
            for prov, services in tx_ctx._plugin_services.items():
                self._plugin_services.setdefault(prov, []).extend(services)
            self._dispose_stack.extend(tx_ctx._dispose_stack)
            tx_ctx._dispose_stack.clear()
        except Exception:
            # Abort: rollback all intermediate effects in LIFO order
            await tx_ctx.dispose()
            raise

    def effect(self, callback: Any) -> Any:
        """Realize a revertible effect on the context (Definition 8, Definition 12).

        Executes *callback*, which performs a context transformation and returns
        an inverse callable (left inverse g such that g ∘ f ≃ id_Γ).
        The inverse is prepended to the accumulator φ for LIFO rollback on dispose().

        Returns a self-disposer closure that can be called independently to revert
        this specific effect early before total context disposal.
        """
        inverse = callback()
        if callable(inverse):
            self._dispose_stack.append(inverse)
            disposed = False

            def dispose_one() -> Any:
                nonlocal disposed
                if disposed:
                    return None
                disposed = True
                if inverse in self._dispose_stack:
                    self._dispose_stack.remove(inverse)
                import inspect

                if inspect.iscoroutinefunction(inverse):
                    return inverse()
                res = inverse()
                return res

            return dispose_one
        return lambda: None

    async def dispose(self) -> None:
        """Execute all tracked inverses in LIFO order (Theorem 7, Theorem 16).

        Applies the accumulator φ to recover the context to its pre-composition state.
        """
        import inspect

        while self._dispose_stack:
            inverse = self._dispose_stack.pop()
            try:
                if inspect.iscoroutinefunction(inverse):
                    await inverse()
                else:
                    res = inverse()
                    if inspect.isawaitable(res):
                        await res
            except Exception as e:
                logger.warning("Error during effect disposal", error=str(e))

    def subscribe(self, event_type: Any, handler: Any) -> Any:
        """Subscribe an event handler with automatic effect tracking and disposal.

        When the context is disposed, the handler is automatically unsubscribed.
        """
        bus = self._event_bus
        if bus is None:
            return lambda: None

        def _forward() -> Any:
            if bus is not None:
                bus.on(event_type, handler)
                return lambda: bus.off(handler)
            return lambda: None

        return self.effect(_forward)

    def _emit_event(self, event_type: Any, source: str, payload: dict[str, Any]) -> None:
        """Emit an event onto the attached event bus if available."""
        if self._event_bus is not None:
            from harness.events.types import HarnessEvent

            evt = HarnessEvent(
                event_type=event_type,
                source=source,
                payload=payload,
            )
            self._event_bus.fire(evt)

    def for_plugin(self, plugin_name: str) -> ScopedServiceContext:
        """Create a scoped context for a specific plugin."""
        return ScopedServiceContext(self, plugin_name)

    def set_plugin_services_active(self, plugin_name: str, active: bool) -> None:
        """Activate or deactivate all services provided by a specific plugin."""
        service_names = self._plugin_services.get(plugin_name, [])
        for name in service_names:
            resolved = self._resolve_realm(name)
            if resolved in self._entries:
                self._entries[resolved].is_active = active
            elif name in self._entries:
                self._entries[name].is_active = active
        if self._parent is not None:
            self._parent.set_plugin_services_active(plugin_name, active)

    def provide(
        self,
        key: ServiceKey[T],
        instance: T,
        *,
        provider: str | None = None,
        allow_override: bool = False,
    ) -> None:
        """Register a service into the context."""
        realm_key = self._resolve_realm(key.name)
        if realm_key in self._entries and not allow_override:
            raise DuplicateServiceError(key)

        entry = ServiceEntry(key=key, instance=instance, provider_plugin=provider, is_active=True)
        self._entries[realm_key] = entry

        # Track for automatic revocation
        if provider:
            self._plugin_services.setdefault(provider, []).append(realm_key)

        # Register inverse in accumulator φ (Revertible Effects)
        def _inverse() -> None:
            if self._entries.get(realm_key) is entry:
                self._entries.pop(realm_key, None)
            if self._parent is not None and self._parent._entries.get(realm_key) is entry:
                self._parent._entries.pop(realm_key, None)

            if provider:
                if provider in self._plugin_services and realm_key in self._plugin_services[provider]:
                    self._plugin_services[provider].remove(realm_key)
                if self._parent is not None and provider in self._parent._plugin_services and realm_key in self._parent._plugin_services[provider]:
                    self._parent._plugin_services[provider].remove(realm_key)

            from harness.events.types import EventType

            payload = {"service": key.name, "provider": provider or "core"}
            if realm_key != key.name:
                payload["realm"] = realm_key

            self._emit_event(
                EventType.SERVICE_REVOKED,
                provider or "core",
                payload,
            )

        self._dispose_stack.append(_inverse)

        logger.debug(
            "Service provided",
            service=key.name,
            realm=realm_key,
            provider=provider or "core",
        )

        from harness.events.types import EventType

        payload = {"service": key.name, "provider": provider or "core"}
        if realm_key != key.name:
            payload["realm"] = realm_key

        self._emit_event(
            EventType.SERVICE_PROVIDED,
            provider or "core",
            payload,
        )

    def require(self, key: ServiceKey[T]) -> T:
        """Resolve a required service, applying any coeffect interception (Definition 31)."""
        realm_key = self._resolve_realm(key.name)
        entry = self._entries.get(realm_key)
        if entry is not None:
            val = entry.instance
            interceptors = self._collect_interceptors(key.name)
            for wrapper in interceptors:
                val = wrapper(val)
            return cast(T, val)

        if self._parent is not None:
            # Let parent resolve with its own/inherited bindings, then apply local interceptors
            val = self._parent._resolve_raw_service(key, realm_key)
            interceptors = self._collect_interceptors(key.name)
            for wrapper in interceptors:
                val = wrapper(val)
            return cast(T, val)

        raise ServiceNotFoundError(key)

    def _resolve_raw_service(self, key: ServiceKey[T], target_realm: str) -> T:
        """Internal helper for hierarchical service resolution."""
        if target_realm in self._entries:
            return cast(T, self._entries[target_realm].instance)
        if key.name in self._entries:
            return cast(T, self._entries[key.name].instance)
        if self._parent is not None:
            return self._parent._resolve_raw_service(key, target_realm)
        raise ServiceNotFoundError(key)

    def optional(self, key: ServiceKey[T]) -> T | None:
        """Resolve a service, returning None if not found."""
        try:
            return self.require(key)
        except ServiceNotFoundError:
            return None

    def has(self, key: ServiceKey[Any]) -> bool:
        """Check whether a service is available (locally or in parent)."""
        realm_key = self._resolve_realm(key.name)
        if realm_key in self._entries:
            return True
        if self._parent is not None:
            return self._parent.has(key)
        return False

    def revoke(self, key: ServiceKey[Any]) -> bool:
        """Remove a service from the context.

        Args:
            key: The service key to revoke.

        Returns:
            True if the service was found and removed, False otherwise.
        """
        realm_key = self._resolve_realm(key.name)
        entry = self._entries.pop(realm_key, None)
        if entry is None and key.name in self._entries:
            entry = self._entries.pop(key.name, None)

        if entry is not None:
            logger.debug(
                "Service revoked",
                service=key.name,
                realm=realm_key,
                provider=entry.provider_plugin or "core",
            )
            from harness.events.types import EventType

            payload = {"service": key.name, "provider": entry.provider_plugin or "core"}
            if realm_key != key.name:
                payload["realm"] = realm_key

            self._emit_event(
                EventType.SERVICE_REVOKED,
                entry.provider_plugin or "core",
                payload,
            )
            return True
        return False

    def hot_swap(
        self,
        key: ServiceKey[T],
        new_instance: T,
        *,
        provider: str | None = None,
    ) -> None:
        """Atomically replace an existing service without downtime.

        Args:
            key: The typed service key to replace.
            new_instance: The new service instance.
            provider: The plugin providing the new instance.
        """
        old_provider = None
        old_entry = self._entries.get(key.name)
        if old_entry:
            old_provider = old_entry.provider_plugin

        self.provide(
            key, new_instance, provider=provider, allow_override=True
        )

        logger.info(
            "Service hot-swapped",
            service=key.name,
            old_provider=old_provider or "core",
            new_provider=provider or "core",
        )

        from harness.events.types import EventType

        self._emit_event(
            EventType.SERVICE_HOT_SWAPPED,
            provider or "core",
            {"service": key.name, "old_provider": old_provider or "core", "new_provider": provider or "core"},
        )

    def revoke_all_from(self, provider: str) -> list[str]:
        """Revoke all services provided by a given plugin.

        This is called automatically when a plugin is unloaded to ensure
        clean teardown (Cordis-style spatiotemporal composability).

        Args:
            provider: Name of the plugin whose services to revoke.

        Returns:
            List of service key names that were revoked.
        """
        service_names = self._plugin_services.pop(provider, [])
        revoked: list[str] = []
        for name in service_names:
            if name in self._entries:
                del self._entries[name]
                revoked.append(name)

        if revoked:
            logger.info(
                "Services revoked for plugin",
                plugin=provider,
                services=revoked,
            )
            from harness.events.types import EventType

            self._emit_event(
                EventType.SERVICE_REVOKED,
                provider,
                {"services": revoked, "provider": provider},
            )
        return revoked

    def child(self) -> ServiceContext:
        """Create a child context scoped to this one.

        The child inherits all services from the parent via lookup
        delegation, but local registrations don't leak upward.
        """
        return ServiceContext(parent=self)

    def list_services(self) -> dict[str, str | None]:
        """List all locally registered services and their providers.

        Returns:
            Dict mapping service key names to provider plugin names.
        """
        return {
            name: entry.provider_plugin
            for name, entry in self._entries.items()
        }

    def __contains__(self, key: ServiceKey[Any]) -> bool:
        return self.has(key)

    def __repr__(self) -> str:
        local_count = len(self._entries)
        parent_info = f", parent={self._parent!r}" if self._parent else ""
        return f"ServiceContext(services={local_count}{parent_info})"


class ScopedServiceContext(ServiceContext):
    """A plugin-scoped service context.

    Automatically binds any registered service to the owning plugin's name,
    enabling transactional lifecycle management without boilerplate.
    """

    def __init__(self, parent: ServiceContext, plugin_name: str) -> None:
        super().__init__(parent=parent)
        self.plugin_name = plugin_name
        self._provided_keys: set[str] = set()

    def provide(
        self,
        key: ServiceKey[T],
        instance: T,
        *,
        provider: str | None = None,
        allow_override: bool = False,
    ) -> None:
        actual_provider = provider or self.plugin_name
        self._provided_keys.add(key.name)
        if self._parent is not None:
            self._parent.provide(
                key,
                instance,
                provider=actual_provider,
                allow_override=allow_override,
            )
        else:
            super().provide(
                key,
                instance,
                provider=actual_provider,
                allow_override=allow_override,
            )

    @property
    def provided_keys(self) -> set[str]:
        """Names of keys registered through this scoped context."""
        return set(self._provided_keys)

    async def dispose(self) -> None:
        """Dispose all scoped effects and revoke provided services in LIFO order."""
        await super().dispose()
        if self._parent is not None:
            self._parent.revoke_all_from(self.plugin_name)

    def __repr__(self) -> str:
        return f"<ScopedServiceContext plugin={self.plugin_name!r} keys={len(self._provided_keys)}>"

