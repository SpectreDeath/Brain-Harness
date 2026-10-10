"""Single-seam IoC resolver factory for PluginLifecycle (Rule 58)."""

from __future__ import annotations

from typing import Any

from harness.kernel.lifecycle.manager.core import PluginLifecycle
from harness.kernel.lifecycle.models import PLUGIN_LIFECYCLE_KEY


def resolve_plugin_lifecycle(context: Any) -> PluginLifecycle:
    """Resolve or instantiate PluginLifecycle through single-seam IoC (Rule 58)."""
    if hasattr(context, "lifecycle") and isinstance(context.lifecycle, PluginLifecycle):
        return context.lifecycle
    if hasattr(context, "_lifecycle") and isinstance(context._lifecycle, PluginLifecycle):
        return context._lifecycle

    if hasattr(context, "optional") and callable(context.optional):
        existing = context.optional(PLUGIN_LIFECYCLE_KEY)
        if existing is not None and isinstance(existing, PluginLifecycle):
            return existing

    lc = PluginLifecycle(context)
    if hasattr(context, "provide") and callable(context.provide):
        context.provide(PLUGIN_LIFECYCLE_KEY, lc, provider="kernel.lifecycle")
    return lc


__all__ = ["resolve_plugin_lifecycle"]
