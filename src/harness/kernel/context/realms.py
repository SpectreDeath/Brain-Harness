"""Isolation realm resolution and scope partitioning for ServiceContext (Definition 28 & 29)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .core import ServiceContext
    from .models import ServiceKey


def resolve_realm(context: ServiceContext, key_name: str) -> str:
    """Resolve a service key through the realm mapping ρ (Coeffect Isolation, Definition 28).

    If the current context has a mapped realm for key_name, returns it.
    Otherwise, delegates to parent context if present, or returns key_name.
    """
    if key_name in context._realms:
        return context._realms[key_name]
    if context._parent is not None:
        return context._parent._resolve_realm(key_name)
    return key_name


def create_isolated_context(
    context: ServiceContext,
    key: ServiceKey[Any],
    realm: str | None = None,
) -> ServiceContext:
    """Derive a child context with an isolated coeffect realm for *key* (Definition 29).

    When components in the derived context provide or require *key*, the lookup
    is redirected to the isolated realm without mutating or observing sibling realms.
    """
    child_ctx = context.child()
    target_realm = realm or f"{key.name}:isolated_{uuid.uuid4().hex[:8]}"
    child_ctx._realms[key.name] = target_realm
    return child_ctx
