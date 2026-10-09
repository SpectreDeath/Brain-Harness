"""Coeffect interception pipeline and dynamic wrapper caching (Definition 30 & 31)."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar, cast

if TYPE_CHECKING:
    from .core import ServiceContext
    from .models import ServiceKey

T = TypeVar("T")


def create_intercepted_context(
    context: ServiceContext,
    key: ServiceKey[T],
    wrapper: Callable[[T], T],
) -> ServiceContext:
    """Derive a child context with cross-cutting coeffect interception (Definition 31).

    Attaches capability policies (e.g. read-only wraps, rate limits, telemetry)
    applied dynamically whenever components in the derived context require *key*.
    """
    child_ctx = context.child()
    root = context._get_root()
    with root._mutation_lock:
        child_ctx._interceptors[key.name].append(cast(Callable[[Any], Any], wrapper))
        child_ctx._compiled_interceptors.pop(key.name, None)
        root._interceptor_epoch = getattr(root, "_interceptor_epoch", 0) + 1
    return child_ctx


def collect_interceptors(
    context: ServiceContext,
    key_name: str,
) -> list[Callable[[Any], Any]]:
    """Collect all interceptors along the context hierarchy with epoch caching."""
    root = context._get_root()
    root_epoch = getattr(root, "_interceptor_epoch", 0)
    cached = context._compiled_interceptors.get(key_name)
    if cached is not None and isinstance(cached, tuple):
        cached_epoch, chain = cached
        if cached_epoch == root_epoch:
            return list(chain)

    with root._mutation_lock:
        root_epoch = getattr(root, "_interceptor_epoch", 0)
        cached = context._compiled_interceptors.get(key_name)
        if cached is not None and isinstance(cached, tuple):
            cached_epoch, chain = cached
            if cached_epoch == root_epoch:
                return list(chain)

        chain: list[Callable[[Any], Any]] = []
        if context._parent is not None:
            chain.extend(context._parent._collect_interceptors(key_name))
        chain.extend(list(context._interceptors.get(key_name, [])))
        new_compiled = dict(context._compiled_interceptors)
        new_compiled[key_name] = (root_epoch, chain)
        context._compiled_interceptors = new_compiled
        return list(chain)
