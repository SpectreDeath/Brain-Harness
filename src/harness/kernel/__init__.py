"""Kernel — IoC container, plugin lifecycle, and unified runtime."""

from .context import (
    DuplicateServiceError,
    ScopedServiceContext,
    ServiceContext,
    ServiceEntry,
    ServiceKey,
    ServiceNotFoundError,
)
from .graph import topological_sort
from .lifecycle import (
    CyclicDependencyError,
    DependencyError,
    InvalidTransitionError,
    PluginEntry,
    PluginLifecycle,
    PluginState,
)

__all__ = [
    "CyclicDependencyError",
    "DependencyError",
    "DuplicateServiceError",
    "InvalidTransitionError",
    "PluginEntry",
    "PluginLifecycle",
    "PluginState",
    "ScopedServiceContext",
    "ServiceContext",
    "ServiceEntry",
    "ServiceKey",
    "ServiceNotFoundError",
    "topological_sort",
]
