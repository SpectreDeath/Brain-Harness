"""Service resolution and lookup operations for ServiceContext."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, cast

from .models import ServiceKey, ServiceNotFoundError

if TYPE_CHECKING:
    from .core import ServiceContext

T = TypeVar("T")


def require_service(context: ServiceContext, key: ServiceKey[T]) -> T:
    """Resolve a required service, applying coeffect interception (Definition 31)."""
    realm_key = context._resolve_realm(key.name)
    entry = context._entries.get(realm_key)
    if entry is not None:
        val = entry.instance
        for wrapper in context._collect_interceptors(key.name):
            val = wrapper(val)
        return cast(T, val)

    if context._parent is not None:
        val = context._parent._resolve_raw_service(key, realm_key)
        for wrapper in context._collect_interceptors(key.name):
            val = wrapper(val)
        return cast(T, val)

    raise ServiceNotFoundError(key)


def resolve_raw_service(
    context: ServiceContext,
    key: ServiceKey[T],
    target_realm: str,
) -> T:
    """Internal helper for hierarchical raw service resolution."""
    if target_realm in context._entries:
        return cast(T, context._entries[target_realm].instance)
    if key.name in context._entries:
        return cast(T, context._entries[key.name].instance)
    if context._parent is not None:
        return context._parent._resolve_raw_service(key, target_realm)
    raise ServiceNotFoundError(key)


def has_service(context: ServiceContext, key: ServiceKey[Any]) -> bool:
    """Check whether a service is available (locally or in parent hierarchy)."""
    realm_key = context._resolve_realm(key.name)
    if realm_key in context._entries:
        return True
    if context._parent is not None:
        return context._parent.has(key)
    return False


def set_plugin_services_active(
    context: ServiceContext,
    plugin_name: str,
    active: bool,
) -> None:
    """Activate or deactivate all services registered by a specific plugin."""
    service_names = context._plugin_services.get(plugin_name, [])
    for name in service_names:
        resolved = context._resolve_realm(name)
        if resolved in context._entries:
            context._entries[resolved].is_active = active
        elif name in context._entries:
            context._entries[name].is_active = active
    if context._parent is not None:
        context._parent.set_plugin_services_active(plugin_name, active)


def list_services(context: ServiceContext) -> dict[str, str | None]:
    """List all locally registered services and their provider plugins."""
    return {name: entry.provider_plugin for name, entry in context._entries.items()}
