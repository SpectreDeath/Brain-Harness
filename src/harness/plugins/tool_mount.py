"""ToolMountMixin — shared tool registration protocol for plugins.

Encapsulates the mount/unmount contract so plugins that expose tools do not
need to repeat the same ToolRegistry interaction in on_enable/on_disable.

Usage::

    class MyPlugin(ToolMountMixin, HarnessPlugin):
        @property
        def requires(self):
            return super_requires() + self.tool_mount_requires()

        async def on_load(self, ctx):
            self._mount_ctx = ctx

        async def on_enable(self):
            specs = [ToolSpec(name="my.tool", ...)]
            await self.mount_tools(specs)

        async def on_disable(self):
            await self.unmount_tools()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey

if TYPE_CHECKING:
    from harness.services.tools import ToolRegistry, ToolSpec

logger = structlog.get_logger()

TOOL_REGISTRY_KEY: ServiceKey[Any] = ServiceKey("tools.registry")


class ToolMountMixin:
    """Mixin that manages tool mount/unmount against ToolRegistry.

    Subclasses must:
    1. Set ``self._mount_ctx`` (a ``ServiceContext``) in their ``on_load``.
    2. Set ``self._mount_name`` (the provider name string) before calling
       ``mount_tools``; typically ``self.name`` from ``HarnessPlugin``.
    3. Include ``self.tool_mount_requires()`` in their ``requires`` list so
       the dependency is visible in the manifest topology.
    """

    _mount_ctx: ServiceContext | None = None
    _mount_name: str = ""

    def setup_tool_mount(self, ctx: ServiceContext, name: str | None = None) -> None:
        """Initialize context and provider name for tool mounting.

        Args:
            ctx: ServiceContext instance.
            name: Optional provider name (defaults to self.name if available).
        """
        self._mount_ctx = ctx
        self._mount_name = name or getattr(self, "name", "")

    def teardown_tool_mount(self) -> None:
        """Clean up context reference on plugin unload."""
        self._mount_ctx = None

    @staticmethod
    def tool_mount_requires() -> list[ServiceKey[Any]]:
        """Return the service keys this mixin depends on.

        Call from the plugin's ``requires`` property so the dependency on
        ToolRegistry is declared rather than hidden inside a method body::

            @property
            def requires(self):
                return [MY_KEY] + ToolMountMixin.tool_mount_requires()
        """
        return [TOOL_REGISTRY_KEY]

    async def mount_tools(self, specs: list[ToolSpec]) -> None:
        """Register *specs* into ToolRegistry with automatic revertible effect tracking.

        No-ops silently when ToolRegistry is not available.
        """
        ctx = self._mount_ctx
        if not ctx or not ctx.has(TOOL_REGISTRY_KEY):
            return

        registry: ToolRegistry = ctx.require(TOOL_REGISTRY_KEY)
        provider_name = self._mount_name

        def _do_mount() -> Any:
            for spec in specs:
                registry.register(
                    name=spec.name,
                    description=spec.description,
                    executor=spec.executor,
                    parameters_schema=spec.parameters_schema,
                    provider=provider_name or spec.provider,
                )
                logger.debug("Tool mounted", tool=spec.name, provider=provider_name)

            def _inverse() -> None:
                if provider_name:
                    removed = registry.unregister_all_from(provider_name)
                    if removed:
                        logger.debug("Tools unmounted via effect inverse", provider=provider_name, count=len(removed))

            return _inverse

        if hasattr(ctx, "effect"):
            ctx.effect(_do_mount)
        else:
            _do_mount()

    async def unmount_tools(self) -> None:
        """Unregister all tools previously registered under this plugin's name."""
        ctx = self._mount_ctx
        if not ctx or not ctx.has(TOOL_REGISTRY_KEY):
            return

        registry: ToolRegistry = ctx.require(TOOL_REGISTRY_KEY)
        removed = registry.unregister_all_from(self._mount_name)
        if removed:
            logger.debug("Tools unmounted", provider=self._mount_name, count=len(removed))

