"""Plugins — Plugin base class, manifest, loader, catalog, and sandbox execution."""

from .base import HarnessPlugin
from .catalog import PluginCatalog, PluginCatalogEntry
from .loader import ManifestPlugin, PluginLoader, PluginLoadError
from .manifest import EntrypointSpec, IsolationMode, ParameterSpec, PluginManifest
from .sandbox import (
    InProcessExecutor,
    SandboxError,
    SandboxExecutor,
    SubprocessExecutor,
    VenvExecutor,
)
from .sandboxed import PluginCallResult, SandboxedPlugin
from .tool_mount import ToolMountMixin
from .watcher import PluginWatcher

__all__ = [
    "EntrypointSpec",
    "HarnessPlugin",
    "InProcessExecutor",
    "IsolationMode",
    "ManifestPlugin",
    "ParameterSpec",
    "PluginCallResult",
    "PluginCatalog",
    "PluginCatalogEntry",
    "PluginLoadError",
    "PluginLoader",
    "PluginManifest",
    "PluginWatcher",
    "SandboxError",
    "SandboxExecutor",
    "SandboxedPlugin",
    "SubprocessExecutor",
    "ToolMountMixin",
    "VenvExecutor",
]
