"""Harness Runtime — unified orchestrator and lifecycle coordinator.

The HarnessRuntime is the primary entry point to a running Harness instance.
It encapsulates the ServiceContext (IoC container), PluginLifecycle manager,
EventBus (observability), and PluginLoader behind a clean, deep interface.

Usage::

    async with HarnessRuntime.create() as rt:
        agent = rt.agent
        if agent:
            result = await agent.run_task("Analyze repository")
"""

from __future__ import annotations

from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any, TypeVar

import structlog

from harness.events.types import EventType, HarnessEvent
from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.lifecycle import PluginLifecycle, PluginState

if TYPE_CHECKING:
    from harness.events.bus import EventBus
    from harness.kernel.reconciler import ConfigurationReconciler, HarnessConfigTree
    from harness.plugins.base import HarnessPlugin
    from harness.plugins.loader import PluginLoader

logger = structlog.get_logger()

T = TypeVar("T")


class HarnessRuntime:
    """Unified runtime orchestrator for the Harness micro-kernel.

    Coordinates service context, plugin lifecycle, event bus, and discovery
    behind an async context manager and declarative lifecycle interface.
    """

    def __init__(
        self,
        context: ServiceContext | None = None,
        lifecycle: PluginLifecycle | None = None,
        event_bus: EventBus | None = None,
        loader: PluginLoader | None = None,
        plugin_dirs: list[Path] | None = None,
        auto_load_user_plugins: bool = True,
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
    ) -> HarnessRuntime:
        """Factory for a standard Harness runtime instance with default plugins.

        Args:
            plugin_dirs: Directories to scan for user plugins.
            db_path: Storage database path.
            event_log_path: Path to JSONL event log file.
            builtins: Custom list of built-in plugins (defaults to standard suite).
            llm: Optional explicit LLMService instance.
            fallback_llm: Optional fallback LLMService instance (alias/fallback for llm).
            llm_model: Default LLM model identifier if using built-in LLMPlugin.
            auto_load_user_plugins: Whether to scan plugin_dirs on startup.

        Returns:
            Configured HarnessRuntime instance.
        """
        from harness.events.bus import EventBus
        from harness.plugins.loader import PluginLoader

        pdirs = plugin_dirs or [Path("plugins")]
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        bus = EventBus(log_file=event_log_path)
        loader = PluginLoader(plugin_dirs=pdirs)

        runtime = cls(
            context=ctx,
            lifecycle=lifecycle,
            event_bus=bus,
            loader=loader,
            plugin_dirs=pdirs,
        )

        active_llm = llm if llm is not None else fallback_llm
        if active_llm is not None:
            from harness.services.llm import LLM_SERVICE_KEY
            runtime.provide(LLM_SERVICE_KEY, active_llm)

        # Register default builtin plugins if not explicitly supplied
        plugins_to_register = builtins
        if plugins_to_register is None:
            plugins_to_register = runtime._get_default_plugins(
                db_path=db_path,
                include_llm=(active_llm is None),
                llm_model=llm_model,
            )

        for p in plugins_to_register:
            runtime.register_plugin(p)

        runtime._auto_load_user_plugins = auto_load_user_plugins
        runtime._initial_config_tree = None
        return runtime

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
        """Create a HarnessRuntime pre-configured with a declarative configuration.

        Args:
            config: Path to YAML/JSON file, HarnessConfigTree, or dictionary specification.
            plugin_dirs: Optional custom plugin directories.
            event_log_path: Path to JSONL event log file.
            llm: Optional explicit LLM service instance.
            auto_load_user_plugins: Whether to scan plugin_dirs on startup.

        Returns:
            HarnessRuntime configured with the declarative reconciler.
        """
        import json
        from harness.kernel.reconciler import HarnessConfigTree, PluginConfigEntry

        parsed_config: HarnessConfigTree
        if isinstance(config, (str, Path)):
            p = Path(config)
            if p.exists():
                text = p.read_text(encoding="utf-8")
                try:
                    import yaml
                    data = yaml.safe_load(text)
                except ImportError:
                    data = json.loads(text)
                parsed_config = HarnessConfigTree.model_validate(data)
            else:
                try:
                    data = json.loads(str(config))
                    parsed_config = HarnessConfigTree.model_validate(data)
                except Exception:
                    raise ValueError(f"Config path does not exist and is not valid JSON: {config}")
        elif isinstance(config, HarnessConfigTree):
            parsed_config = config
        elif isinstance(config, dict):
            parsed_config = HarnessConfigTree.model_validate(config)
        elif isinstance(config, list):
            parsed_config = HarnessConfigTree(
                plugins=[PluginConfigEntry.model_validate(item) for item in config]
            )
        else:
            raise TypeError(f"Unsupported config type: {type(config)}")

        runtime = cls.create(
            plugin_dirs=plugin_dirs,
            event_log_path=event_log_path,
            llm=llm,
            builtins=[],
            auto_load_user_plugins=auto_load_user_plugins,
        )
        runtime._initial_config_tree = parsed_config
        return runtime

    async def reconcile(
        self, config: Any
    ) -> Any:
        """Reconcile runtime state against a declarative configuration tree (Section 5.2).

        Args:
            config: Target declarative configuration.

        Returns:
            ReconciliationResult with detailed change metrics.
        """
        import json
        from harness.kernel.reconciler import ConfigurationReconciler, HarnessConfigTree

        if isinstance(config, (str, Path)):
            p = Path(config)
            if p.exists():
                text = p.read_text(encoding="utf-8")
                try:
                    import yaml
                    data = yaml.safe_load(text)
                except ImportError:
                    data = json.loads(text)
                config_tree = HarnessConfigTree.model_validate(data)
            else:
                data = json.loads(str(config))
                config_tree = HarnessConfigTree.model_validate(data)
        else:
            config_tree = config

        if not hasattr(self, "_reconciler") or self._reconciler is None:
            self._reconciler = ConfigurationReconciler(self)

        return await self._reconciler.reconcile(config_tree)


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

    # --- High-level service properties ---

    @property
    def tools(self) -> Any | None:
        """Tool registry service if available."""
        from harness.services.tools import TOOL_REGISTRY_KEY

        return self._context.optional(TOOL_REGISTRY_KEY)

    @property
    def storage(self) -> Any | None:
        """Storage service if available."""
        from harness.services.storage import STORAGE_SERVICE_KEY

        return self._context.optional(STORAGE_SERVICE_KEY)

    @property
    def llm(self) -> Any | None:
        """LLM service if available."""
        from harness.services.llm import LLM_SERVICE_KEY

        return self._context.optional(LLM_SERVICE_KEY)

    @property
    def agent(self) -> Any | None:
        """Agent loop service if available."""
        from harness.agent.base import AGENT_LOOP_KEY

        return self._context.optional(AGENT_LOOP_KEY)

    @property
    def sessions(self) -> Any | None:
        """Agent session manager service if available."""
        from harness.agent.session import AGENT_SESSION_MANAGER_KEY

        return self._context.optional(AGENT_SESSION_MANAGER_KEY)

    async def export_session(self, session_id: str, format: str = "json") -> str:
        """Export an agent execution session to JSON or Markdown."""
        mgr = self.sessions
        if mgr is None:
            raise RuntimeError("Agent session manager is not available in runtime")
        return str(await mgr.export_session(session_id, format=format))

    # --- Convenience service accessors ---

    def require(self, key: ServiceKey[T]) -> T:
        """Resolve a required service from the context."""
        return self._context.require(key)

    def optional(self, key: ServiceKey[T]) -> T | None:
        """Resolve an optional service from the context."""
        return self._context.optional(key)

    def provide(
        self,
        key: ServiceKey[T],
        instance: T,
        *,
        provider: str | None = None,
        allow_override: bool = False,
    ) -> None:
        """Register a service into the context."""
        self._context.provide(
            key, instance, provider=provider, allow_override=allow_override
        )

    # --- Lifecycle methods ---

    def register_plugin(self, plugin: HarnessPlugin) -> None:
        """Discover and track a plugin."""
        self._lifecycle.discover(plugin)

    async def add_plugin_from_source(
        self,
        source: str | Path,
        *,
        ref: str = "main",
        force: bool = False,
        token: str | None = None,
        auto_enable: bool = True,
    ) -> HarnessPlugin:
        """Ingest a plugin from GitHub URL, ZIP archive, or local path and register it.

        If the runtime is currently running and auto_enable is True, the plugin
        is immediately loaded, validated, and enabled.

        Args:
            source: GitHub URL, owner/repo shorthand, remote/local ZIP path, or directory.
            ref: Git ref (branch/tag) if fetching from GitHub.
            force: Re-fetch even if already cached.
            token: Optional GitHub API token.
            auto_enable: Automatically load, validate, and enable if runtime is active.

        Returns:
            The instantiated and registered HarnessPlugin.
        """
        from harness.ingestion.pipeline import PluginIngestionPipeline

        pipeline = PluginIngestionPipeline(
            plugin_dir=self._plugin_dirs[0] if self._plugin_dirs else None,
            github_token=token,
        )
        plugin = await pipeline.ingest(str(source), ref=ref, force=force)
        self.register_plugin(plugin)

        if self._is_running and auto_enable:
            await self._lifecycle.ensure_enabled(plugin.name)

        return plugin

    async def start(self) -> None:
        """Start the runtime: load, validate, and enable all plugins in topological order."""
        if self._is_running:
            return

        logger.info("Starting Harness runtime")

        # Provide EventBus as a first-class service before plugins load
        from harness.events.bus import EVENT_BUS_KEY

        self._context.provide(
            EVENT_BUS_KEY,
            self._event_bus,
            provider="harness",
            allow_override=True,
        )

        # Discover user plugins if configured
        if self._auto_load_user_plugins:
            user_plugins = self._loader.discover_all()
            for plugin in user_plugins:
                self._lifecycle.discover(plugin)

        # If initial declarative configuration is present, reconcile it
        if getattr(self, "_initial_config_tree", None) is not None:
            await self.reconcile(self._initial_config_tree)

        # Enable all in topological dependency order
        results = await self._lifecycle.enable_all()
        enabled_count = sum(results.values())
        total_count = len(results)

        self._is_running = True

        await self._event_bus.emit(
            HarnessEvent(
                event_type=EventType.HARNESS_STARTED,
                payload={
                    "enabled_plugins": [name for name, ok in results.items() if ok],
                    "total_plugins": total_count,
                    "services": list(self._context.list_services().keys()),
                },
            )
        )

        logger.info(
            "Harness runtime started",
            enabled=f"{enabled_count}/{total_count}",
            services=len(self._context.list_services()),
        )

    async def stop(self) -> None:
        """Stop the runtime: gracefully unload all plugins and close resources."""
        if not self._is_running:
            return

        logger.info("Stopping Harness runtime")

        await self._lifecycle.unload_all()
        await self._context.dispose()
        await self._event_bus.emit(
            HarnessEvent(event_type=EventType.HARNESS_STOPPED)
        )
        await self._event_bus.close()
        self._is_running = False

        logger.info("Harness runtime stopped")

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

    def summary(self) -> dict[str, str]:
        """Summary of tracked plugins and their lifecycle states."""
        return self._lifecycle.summary()

    async def enable_plugin(self, name: str) -> bool:
        """Load, validate, and enable a plugin by name."""
        return await self._lifecycle.ensure_enabled(name)

    async def disable_plugin(self, name: str) -> bool:
        """Disable an active plugin by name."""
        if self._lifecycle.get_state(name) == PluginState.ENABLED:
            await self._lifecycle.disable(name)
            return True
        return False

    async def enable_all_plugins(self) -> dict[str, bool]:
        """Enable all discovered and validated plugins."""
        return await self._lifecycle.enable_all()

    async def disable_all_plugins(self, *, keep_core: bool = True) -> list[str]:
        """Disable all active plugins.

        Args:
            keep_core: If True, keeps core services (tools, storage, llm) running.
        """
        core_plugins = {"tools.registry", "storage.sqlite", "llm.provider"} if keep_core else set()
        disabled: list[str] = []
        for name, entry in list(self._lifecycle.plugins.items()):
            if entry.state == PluginState.ENABLED and name not in core_plugins:
                try:
                    await self._lifecycle.disable(name)
                    disabled.append(name)
                except Exception as e:
                    logger.warning("Failed disabling plugin", plugin=name, error=str(e))
        return disabled

    def enable_tool(self, name: str) -> bool:
        """Enable an individual tool by name."""
        if self.tools is not None:
            return bool(self.tools.enable_tool(name))
        return False

    def disable_tool(self, name: str) -> bool:
        """Disable an individual tool by name."""
        if self.tools is not None:
            return bool(self.tools.disable_tool(name))
        return False

    def toggle_tool(self, name: str, enabled: bool | None = None) -> bool:
        """Toggle an individual tool's enabled state."""
        if self.tools is not None:
            return bool(self.tools.toggle_tool(name, enabled=enabled))
        return False

    async def run_task(
        self,
        task: str,
        *,
        max_steps: int = 10,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run an autonomous task using the active agent loop service."""
        from harness.agent.base import AGENT_LOOP_KEY, AgentLoopService

        agent: AgentLoopService = self._context.require(AGENT_LOOP_KEY)
        return await agent.run_task(task, max_steps=max_steps, context=context)

    # --- Private helpers ---

    def _get_default_plugins(
        self,
        db_path: Path | str | None = None,
        include_llm: bool = True,
        llm_model: str = "gpt-4o-mini",
    ) -> list[HarnessPlugin]:
        """Construct standard default plugins suite."""
        from harness.agent.react import ReActAgentPlugin
        from harness.agent.session import AgentSessionPlugin
        from harness.bridges.base import EcosystemBridgeCatalog
        from harness.services.llm import LLMPlugin
        from harness.services.storage import StoragePlugin
        from harness.services.tools import ToolRegistryPlugin

        target_db = db_path or (Path(".harness") / "storage.db")
        plugins: list[HarnessPlugin] = [
            StoragePlugin(db_path=target_db),
            AgentSessionPlugin(),
            ToolRegistryPlugin(),
        ]
        # Dynamically discover and attach registered ecosystem bridge plugins
        ecosystem_plugins = EcosystemBridgeCatalog.discover_available_plugins()
        plugins.extend(ecosystem_plugins)

        if include_llm:
            plugins.append(LLMPlugin(default_model=llm_model))
        plugins.append(ReActAgentPlugin())
        return plugins
