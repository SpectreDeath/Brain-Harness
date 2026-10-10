"""Plugin lifecycle manager package facade."""

from __future__ import annotations

from harness.kernel.lifecycle.manager.core import PluginLifecycle
from harness.kernel.lifecycle.manager.resolvers import resolve_plugin_lifecycle

__all__ = [
    "PluginLifecycle",
    "resolve_plugin_lifecycle",
]
