"""Unified orchestrator and lifecycle coordinator for the Harness micro-kernel."""

from __future__ import annotations

import sys
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any

from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle
from harness.kernel.runtime.factory import (
    create_diagnostic_runtime,
    create_runtime,
    create_runtime_from_config,
)
from harness.kernel.runtime.lifecycle_runner import start_runtime, stop_runtime
from harness.kernel.runtime.plugin_ops import RuntimePluginOpsMixin
from harness.kernel.runtime.reconcile import reconcile_runtime
from harness.kernel.runtime.services import RuntimeServicesMixin

if TYPE_CHECKING:
    from harness.events.bus import EventBus
    from harness.kernel.reconciler import ConfigurationReconciler, HarnessConfigTree
    from harness.plugins.base import HarnessPlugin
    from harness.plugins.loader import PluginLoader

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class HarnessRuntime(RuntimeServicesMixin, RuntimePluginOpsMixin):
    """Unified runtime orchestrator for the Harness micro-kernel."""

    def __init__(
        self,
        context: ServiceContext | None = None,
        lifecycle: PluginLifecycle | None = None,
        event_bus: EventBus | None = None,
        loader: PluginLoader | None = None,
        plugin_dirs: list[Path] | None = None,
        auto_load_user_plugins: bool = True,
        lazy_external_plugins: bool = True,
    ) -> None:
        from harness.events.bus import EventBus as _EventBus

        self._context = context or ServiceContext()
        self._event_bus = event_bus or _EventBus()
        self._context.attach_event_bus(self._event_bus)
        self._lifecycle = lifecycle or PluginLifecycle(self._context)
        self._plugin_dirs = plugin_dirs or [Path("plugins")]
        if loader is None:
            from harness.plugins.loader import PluginLoader

            loader = PluginLoader(plugin_dirs=self._plugin_dirs)
        self._loader = loader
        self._auto_load_user_plugins = auto_load_user_plugins
        self._lazy_external_plugins = lazy_external_plugins
        self._is_running = False
        self._initial_config_tree: HarnessConfigTree | None = None
        self._reconciler: ConfigurationReconciler | None = None

    @classmethod
    def create(
        cls,
        *,
        plugin_dirs: list[Path] | None = None,
        db_path: Path | str | None = None,
        event_log_path: Path | None = None,
        builtins: list[HarnessPlugin] | None = None,
        llm: Any | None = None,
        fallback_llm: Any | None = None,
        llm_model: str = "gpt-4o-mini",
        auto_load_user_plugins: bool = True,
        lazy_external_plugins: bool = True,
    ) -> HarnessRuntime:
        """Factory for a standard Harness runtime instance with default plugins."""
        return create_runtime(
            cls,
            plugin_dirs=plugin_dirs,
            db_path=db_path,
            event_log_path=event_log_path,
            builtins=builtins,
            llm=llm,
            fallback_llm=fallback_llm,
            llm_model=llm_model,
            auto_load_user_plugins=auto_load_user_plugins,
            lazy_external_plugins=lazy_external_plugins,
        )

    @classmethod
    def create_diagnostic(
        cls,
        *,
        db_path: str = ":memory:",
        include_tools: bool = True,
        include_storage: bool = True,
    ) -> HarnessRuntime:
        """Lightweight runtime factory for zero-overhead diagnostics and tests."""
        return create_diagnostic_runtime(
            cls,
            db_path=db_path,
            include_tools=include_tools,
            include_storage=include_storage,
        )

    @classmethod
    def from_config(
        cls,
        config: Any,
        *,
        plugin_dirs: list[Path] | None = None,
        event_log_path: Path | None = None,
        llm: Any | None = None,
        auto_load_user_plugins: bool = False,
    ) -> HarnessRuntime:
        """Create a HarnessRuntime pre-configured with a declarative configuration."""
        return create_runtime_from_config(
            cls,
            config,
            plugin_dirs=plugin_dirs,
            event_log_path=event_log_path,
            llm=llm,
            auto_load_user_plugins=auto_load_user_plugins,
        )

    async def reconcile(self, config: Any) -> Any:
        """Reconcile runtime state against a declarative configuration tree."""
        return await reconcile_runtime(self, config)

    @property
    def context(self) -> ServiceContext:
        """The IoC service context."""
        return self._context

    @property
    def lifecycle(self) -> PluginLifecycle:
        """The plugin lifecycle manager."""
        return self._lifecycle

    @property
    def event_bus(self) -> EventBus:
        """The append-only event bus."""
        return self._event_bus

    @property
    def loader(self) -> PluginLoader:
        """The plugin loader and discovery engine."""
        return self._loader

    @property
    def is_running(self) -> bool:
        """Whether the runtime is currently active."""
        return self._is_running

    async def start(self) -> None:
        """Start the runtime: load, validate, and enable all plugins in topological order."""
        await start_runtime(self)

    async def stop(self) -> None:
        """Stop the runtime: gracefully unload all plugins and close resources."""
        await stop_runtime(self)

    async def __aenter__(self) -> HarnessRuntime:  # noqa: PYI034
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.stop()


__all__ = ["HarnessRuntime"]
