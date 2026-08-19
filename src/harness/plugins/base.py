"""Base plugin protocol — the contract every harness plugin implements.

A HarnessPlugin declares what services it provides and requires,
and implements lifecycle hooks that the PluginLifecycle manager calls.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from harness.kernel.context import ServiceContext, ServiceKey


class HarnessPlugin(ABC):
    """Abstract base class for all harness plugins.

    Every component in the harness — models, tools, storage, agent loops —
    is a plugin that implements this interface.

    Lifecycle hooks are called in order:
        1. ``on_load(ctx)``    — receive the service context, register services
        2. ``on_enable()``     — start doing work (dependencies are available)
        3. ``on_disable()``    — stop doing work (stay loaded but inactive)
        4. ``on_unload()``     — clean up resources (services will be revoked)

    Example::

        class MyToolPlugin(HarnessPlugin):
            name = "my-tool"
            version = "1.0.0"
            provides = [ServiceKey[ToolRegistry]("tool.my-tool")]
            requires = [ServiceKey[LLMService]("llm.provider")]

            async def on_load(self, ctx):
                self.llm = ctx.require(ServiceKey[LLMService]("llm.provider"))
                ctx.provide(self.provides[0], self)

            async def on_enable(self):
                pass  # Start serving

            async def on_disable(self):
                pass  # Stop serving

            async def on_unload(self):
                pass  # Clean up
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin name (e.g., 'llm.openai', 'tool.git')."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version string (semver recommended)."""

    @property
    def description(self) -> str:
        """Human-readable description of what this plugin does."""
        return f"{self.name} plugin"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        """Service keys this plugin provides to the harness."""
        return []

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        """Service keys this plugin depends on."""
        return []

    @property
    def trusted(self) -> bool:
        """Whether this plugin is trusted to run in-process.

        Untrusted plugins (e.g., from GitHub ingestion) run in subprocess
        sandboxes. Override to True only for built-in or vetted plugins.
        """
        return False

    async def on_load(self, ctx: ServiceContext) -> None:
        """Called when the plugin is loaded into the harness.

        This is where the plugin should:
        - Store a reference to the context
        - Register the services it provides
        - Perform any initialization that doesn't require dependencies

        Args:
            ctx: The harness service context (IoC container).
        """

    async def on_enable(self) -> None:
        """Called when the plugin is enabled and all dependencies are available.

        This is where the plugin should start doing work.
        Dependencies declared in ``requires`` are guaranteed to be available.
        """

    async def on_disable(self) -> None:
        """Called when the plugin is disabled.

        The plugin should stop doing active work but may remain loaded.
        It can be re-enabled later.
        """

    async def on_unload(self) -> None:
        """Called when the plugin is being unloaded from the harness.

        Clean up all resources. After this call, all services provided by
        this plugin are automatically revoked from the context.
        """

    def __repr__(self) -> str:
        return f"<Plugin {self.name}@{self.version}>"
