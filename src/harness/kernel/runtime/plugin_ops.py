"""Runtime plugin and tool lifecycle operations mixin."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from harness.kernel.lifecycle import PluginLifecycle, PluginState
from harness.kernel.runtime.defaults import get_default_plugins
from harness.kernel.runtime.plugins import (
    disable_all_plugins,
    enable_all_plugins,
    ingest_plugin_from_source,
)
from harness.kernel.runtime.tools import (
    disable_tool,
    enable_tool,
    run_runtime_task,
    toggle_tool,
)

if TYPE_CHECKING:
    from harness.plugins.base import HarnessPlugin

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class RuntimePluginOpsMixin:
    """Plugin tracking, tool toggling, and task dispatching operations for HarnessRuntime."""

    _lifecycle: PluginLifecycle

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
        """Ingest a plugin from GitHub URL, ZIP archive, or local path and register it."""
        return await ingest_plugin_from_source(
            self, source, ref=ref, force=force, token=token, auto_enable=auto_enable  # type: ignore[arg-type]
        )

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

    async def enable_all_plugins(self, *, include_sandboxed: bool = False) -> dict[str, bool]:
        """Enable all discovered and validated plugins."""
        return await enable_all_plugins(self, include_sandboxed=include_sandboxed)  # type: ignore[arg-type]

    async def disable_all_plugins(self, *, keep_core: bool = True) -> list[str]:
        """Disable all active plugins."""
        return await disable_all_plugins(self, keep_core=keep_core)  # type: ignore[arg-type]

    def enable_tool(self, name: str) -> bool:
        """Enable an individual tool by name."""
        return enable_tool(self, name)  # type: ignore[arg-type]

    def disable_tool(self, name: str) -> bool:
        """Disable an individual tool by name."""
        return disable_tool(self, name)  # type: ignore[arg-type]

    def toggle_tool(self, name: str, enabled: bool | None = None) -> bool:
        """Toggle an individual tool's enabled state."""
        return toggle_tool(self, name, enabled=enabled)  # type: ignore[arg-type]

    async def run_task(
        self,
        task: str,
        *,
        max_steps: int = 10,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Run an autonomous task using the active agent loop service."""
        return await run_runtime_task(self, task, max_steps=max_steps, context=context)  # type: ignore[arg-type]

    def _get_default_plugins(
        self,
        db_path: Path | str | None = None,
        include_llm: bool = True,
        llm_model: str = "gpt-4o-mini",
    ) -> list[HarnessPlugin]:
        """Construct standard default plugins suite."""
        return get_default_plugins(db_path=db_path, include_llm=include_llm, llm_model=llm_model)


__all__ = ["RuntimePluginOpsMixin"]
