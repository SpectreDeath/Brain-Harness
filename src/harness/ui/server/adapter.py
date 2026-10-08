"""RuntimeAdapter normalizing access between unified HarnessRuntime and standalone kernel components."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

from harness.agent.base import AGENT_LOOP_KEY
from harness.creator.introspection import RuntimeIntrospector
from harness.events.bus import EventBus
from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle, PluginState
from harness.kernel.runtime import HarnessRuntime
from harness.plugins.base import HarnessPlugin
from harness.ingestion.pipeline import PluginIngestionPipeline
from harness.services.tools import TOOL_REGISTRY_KEY

logger = structlog.get_logger(__name__)


class RuntimeAdapter:
    """Authoritative adapter normalizing access between unified HarnessRuntime and standalone kernel components."""

    def __init__(
        self,
        context_or_runtime: ServiceContext | HarnessRuntime,
        lifecycle: PluginLifecycle | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        if isinstance(context_or_runtime, HarnessRuntime):
            self._runtime: HarnessRuntime | None = context_or_runtime
            self.context: ServiceContext = context_or_runtime.context
            self.lifecycle: PluginLifecycle = context_or_runtime.lifecycle
            self.event_bus: EventBus | None = context_or_runtime.event_bus
        else:
            self._runtime = None
            self.context = context_or_runtime
            if lifecycle is None:
                raise ValueError("lifecycle is required when context is passed")
            self.lifecycle = lifecycle
            self.event_bus = event_bus

    @property
    def is_unified_runtime(self) -> bool:
        return self._runtime is not None

    async def enable_all(self) -> dict[str, bool]:
        """Enable all discovered plugins."""
        if self._runtime is not None:
            return await self._runtime.enable_all_plugins()
        return await self.lifecycle.enable_all()

    async def disable_all(self, *, keep_core: bool = True) -> list[str]:
        """Disable all active plugins with optional core service retention."""
        if self._runtime is not None:
            return await self._runtime.disable_all_plugins(keep_core=keep_core)

        core_plugins = {"tools.registry", "storage.sqlite", "llm.provider"} if keep_core else set()
        disabled: list[str] = []
        for name, entry in list(self.lifecycle.plugins.items()):
            if entry.state == PluginState.ENABLED and name not in core_plugins:
                try:
                    await self.lifecycle.disable(name)
                    disabled.append(name)
                except Exception as e:
                    logger.warning("Failed disabling plugin in UI adapter", plugin=name, error=str(e))
        return disabled

    async def add_plugin_from_source(
        self,
        source: str | Path,
        *,
        ref: str = "main",
        force: bool = False,
        auto_enable: bool = True,
    ) -> HarnessPlugin:
        """Ingest and register a plugin from source."""
        if self._runtime is not None:
            return await self._runtime.add_plugin_from_source(
                source, ref=ref, force=force, auto_enable=auto_enable
            )

        pipeline = PluginIngestionPipeline()
        plugin = await pipeline.ingest(str(source), ref=ref, force=force)
        if auto_enable:
            await self.lifecycle.register_and_enable(plugin)
        else:
            self.lifecycle.discover(plugin)
        return plugin

    async def run_agent(self, task: str, max_steps: int = 10) -> Any:
        """Execute an autonomous agent task."""
        if self._runtime is not None:
            return await self._runtime.run_task(task, max_steps=max_steps)

        agent_loop = self.context.optional(AGENT_LOOP_KEY)
        if not agent_loop:
            raise RuntimeError("No active agent.loop service found")
        return await agent_loop.run_task(task, max_steps=max_steps)

    def get_introspector(self) -> RuntimeIntrospector:
        """Return an authoritative RuntimeIntrospector instance."""
        tools = self.context.optional(TOOL_REGISTRY_KEY)
        return RuntimeIntrospector(self.context, self.lifecycle, tools)

    def get_catalog(self) -> list[dict[str, Any]]:
        """Return enriched catalog report."""
        loader = getattr(self._runtime, "loader", None) if self._runtime else None
        return self.get_introspector().get_catalog_report(loader=loader)

    def get_plugin_guide(self, name: str) -> dict[str, Any]:
        """Return structured guide and manifest card for a plugin."""
        loader = getattr(self._runtime, "loader", None) if self._runtime else None
        return self.get_introspector().get_plugin_guide_report(name, loader=loader)

    def get_sandboxes(self) -> list[dict[str, Any]]:
        """Return runtime sandbox states across all registered plugins."""
        return self.get_introspector().get_sandboxes_report()


__all__ = [
    "RuntimeAdapter",
]
