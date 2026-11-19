"""Plugins — Plugin base class, manifest, loader, catalog, and sandbox execution."""

from .artifact_cache import (
    ArtifactCacheEntry,
    ArtifactOffsetRecord,
    BoundedArtifactPrefetcher,
    OffsetManifestIndex,
    PluginArtifactCache,
)
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
    "ArtifactCacheEntry",
    "ArtifactOffsetRecord",
    "BoundedArtifactPrefetcher",
    "EntrypointSpec",
    "HarnessPlugin",
    "InProcessExecutor",
    "IsolationMode",
    "ManifestPlugin",
    "OffsetManifestIndex",
    "ParameterSpec",
    "PluginArtifactCache",
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
