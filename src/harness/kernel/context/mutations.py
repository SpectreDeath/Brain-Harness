"""Service registration, revocation, and hot-swapping mutations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

import structlog

from .effects import create_service_inverse
from .models import DuplicateServiceError, ServiceEntry, ServiceKey

if TYPE_CHECKING:
    from .core import ServiceContext

logger = structlog.get_logger()
T = TypeVar("T")


def provide_service(
    context: ServiceContext,
    key: ServiceKey[T],
    instance: T,
    *,
    provider: str | None = None,
    allow_override: bool = False,
) -> None:
    """Register a service into the context with COW safety and inverse effect tracking."""
    with context._mutation_lock:
        realm_key = context._resolve_realm(key.name)
        if realm_key in context._entries and not allow_override:
            raise DuplicateServiceError(key)

        entry = ServiceEntry(
            key=key, instance=instance, provider_plugin=provider, is_active=True
        )
        new_entries = dict(context._entries)
        new_entries[realm_key] = entry
        context._entries = new_entries
        context._interceptor_epoch += 1
        root = context._get_root()
        if root is not context:
            root._interceptor_epoch += 1

        if provider:
            context._plugin_services.setdefault(provider, []).append(realm_key)

        _inv = create_service_inverse(context, key.name, realm_key, entry, provider)
        context._dispose_stack.append(_inv)

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
    context._emit_event(EventType.SERVICE_PROVIDED, provider or "core", payload)


def revoke_service(context: ServiceContext, key: ServiceKey[Any]) -> bool:
    """Remove a service from the context and purge stale inverse closures (Rule 54)."""
    with context._mutation_lock:
        realm_key = context._resolve_realm(key.name)
        new_entries = dict(context._entries)
        entry = new_entries.pop(realm_key, None)
        if entry is None and key.name in new_entries:
            entry = new_entries.pop(key.name, None)

        if entry is not None:
            context._entries = new_entries
            context._interceptor_epoch += 1
            root = context._get_root()
            if root is not context:
                root._interceptor_epoch += 1

            context._dispose_stack = [
                inv
                for inv in context._dispose_stack
                if getattr(inv, "_realm_key", None) not in (realm_key, key.name)
            ]
            logger.debug(
                "Service revoked",
                service=key.name,
                realm=realm_key,
                provider=entry.provider_plugin or "core",
            )
            from harness.events.types import EventType

            payload = {
                "service": key.name,
                "provider": entry.provider_plugin or "core",
            }
            if realm_key != key.name:
                payload["realm"] = realm_key
            context._emit_event(
                EventType.SERVICE_REVOKED,
                entry.provider_plugin or "core",
                payload,
            )
            return True
        return False


def hot_swap_service(
    context: ServiceContext,
    key: ServiceKey[T],
    new_instance: T,
    *,
    provider: str | None = None,
) -> None:
    """Atomically replace an existing service and purge stale inverse closures (Rule 54)."""
    old_provider = None
    with context._mutation_lock:
        realm_key = context._resolve_realm(key.name)
        old_entry = context._entries.get(realm_key) or context._entries.get(key.name)
        if old_entry:
            old_provider = old_entry.provider_plugin

        context._dispose_stack = [
            inv
            for inv in context._dispose_stack
            if getattr(inv, "_realm_key", None) not in (realm_key, key.name)
        ]

    provide_service(
        context, key, new_instance, provider=provider, allow_override=True
    )
    logger.info(
        "Service hot-swapped",
        service=key.name,
        old_provider=old_provider or "core",
        new_provider=provider or "core",
    )
    from harness.events.types import EventType

    context._emit_event(
        EventType.SERVICE_HOT_SWAPPED,
        provider or "core",
        {
            "service": key.name,
            "old_provider": old_provider or "core",
            "new_provider": provider or "core",
        },
    )


def revoke_all_from_provider(context: ServiceContext, provider: str) -> list[str]:
    """Revoke all services provided by a plugin and purge inverse closures (Rule 54)."""
    with context._mutation_lock:
        service_names = context._plugin_services.pop(provider, [])
        revoked: list[str] = []
        new_entries = dict(context._entries)
        for name in service_names:
            if name in new_entries:
                del new_entries[name]
                revoked.append(name)

        if revoked:
            context._entries = new_entries
            context._interceptor_epoch += 1
            root = context._get_root()
            if root is not context:
                root._interceptor_epoch += 1

            revoked_set = set(revoked)
            context._dispose_stack = [
                inv
                for inv in context._dispose_stack
                if getattr(inv, "_provider", None) != provider
                and getattr(inv, "_realm_key", None) not in revoked_set
            ]
        logger.info(
            "Services revoked for plugin",
            plugin=provider,
            services=revoked,
        )
        from harness.events.types import EventType

        context._emit_event(
            EventType.SERVICE_REVOKED,
            provider,
            {"services": revoked, "provider": provider},
        )
    return revoked
