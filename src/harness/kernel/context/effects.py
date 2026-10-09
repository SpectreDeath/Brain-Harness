"""Revertible effects, accumulator disposal stack, and inverse closures (Definition 8, 12, Theorem 7)."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from .core import ServiceContext
    from .models import ServiceEntry

logger = structlog.get_logger()


def register_effect(context: ServiceContext, callback: Any) -> Any:
    """Realize a revertible effect on the context (Definition 8, Definition 12).

    Executes *callback*, which performs a context transformation and returns
    an inverse callable (left inverse g such that g ∘ f ≃ id_Γ).
    The inverse is prepended to the accumulator φ for LIFO rollback on dispose().

    Returns a self-disposer closure that can be called independently to revert
    this specific effect early before total context disposal.
    """
    inverse = callback()
    if callable(inverse):
        with context._mutation_lock:
            context._dispose_stack.append(inverse)
        disposed = False

        def dispose_one() -> Any:
            nonlocal disposed
            if disposed:
                return None
            disposed = True
            with context._mutation_lock:
                if inverse in context._dispose_stack:
                    context._dispose_stack.remove(inverse)

            if inspect.iscoroutinefunction(inverse):
                return inverse()
            res = inverse()
            return res

        return dispose_one
    return lambda: None


async def dispose_context(context: ServiceContext) -> None:
    """Execute all tracked inverses in LIFO order (Theorem 7, Theorem 16).

    Applies the accumulator φ to recover the context to its pre-composition state.
    """
    with context._mutation_lock:
        stack = list(context._dispose_stack)
        context._dispose_stack.clear()
        teardown_epoch = context._teardown_epoch = (
            getattr(context, "_teardown_epoch", 0) + 1
        )

    while stack:
        inverse = stack.pop()
        if getattr(inverse, "_teardown_epoch", -1) > teardown_epoch:
            continue
        try:
            if inspect.iscoroutinefunction(inverse):
                await inverse()
            else:
                res = inverse()
                if inspect.isawaitable(res):
                    await res
        except Exception as e:
            logger.warning("Error during effect disposal", error=str(e))


def subscribe_event(context: ServiceContext, event_type: Any, handler: Any) -> Any:
    """Subscribe an event handler with automatic effect tracking and disposal.

    When the context is disposed, the handler is automatically unsubscribed.
    """
    bus = context.event_bus
    if bus is None:
        return lambda: None

    def _forward() -> Any:
        if bus is not None:
            bus.on(event_type, handler)
            return lambda: bus.off(handler)
        return lambda: None

    return register_effect(context, _forward)


def create_service_inverse(
    context: ServiceContext,
    key_name: str,
    realm_key: str,
    entry: ServiceEntry,
    provider: str | None,
) -> Any:
    """Create a tracked inverse closure for a provided service entry (Rule 54)."""

    def _inverse() -> None:
        with context._mutation_lock:
            if context._entries.get(realm_key) is entry:
                new_e = dict(context._entries)
                new_e.pop(realm_key, None)
                context._entries = new_e
                context._interceptor_epoch += 1
                r = context._get_root()
                if r is not context:
                    r._interceptor_epoch += 1

            if (
                context._parent is not None
                and context._parent._entries.get(realm_key) is entry
            ):
                new_pe = dict(context._parent._entries)
                new_pe.pop(realm_key, None)
                context._parent._entries = new_pe
                context._parent._interceptor_epoch += 1
                pr = context._parent._get_root()
                if pr is not context._parent:
                    pr._interceptor_epoch += 1

            if provider:
                if (
                    provider in context._plugin_services
                    and realm_key in context._plugin_services[provider]
                ):
                    context._plugin_services[provider].remove(realm_key)
                if (
                    context._parent is not None
                    and provider in context._parent._plugin_services
                    and realm_key in context._parent._plugin_services[provider]
                ):
                    context._parent._plugin_services[provider].remove(realm_key)

        from harness.events.types import EventType

        payload = {"service": key_name, "provider": provider or "core"}
        if realm_key != key_name:
            payload["realm"] = realm_key

        context._emit_event(
            EventType.SERVICE_REVOKED,
            provider or "core",
            payload,
        )

    _inverse._realm_key = realm_key  # type: ignore[attr-defined]
    _inverse._provider = provider  # type: ignore[attr-defined]
    return _inverse
