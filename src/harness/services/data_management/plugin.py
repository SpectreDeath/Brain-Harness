"""Built-in Harness Plugin for Data Management capabilities."""

from __future__ import annotations

from typing import Any

import structlog

from harness.events.bus import EVENT_BUS_KEY
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.plugins.manifest import PluginManifest
from harness.services.data_management.protocols import DATA_MANAGEMENT_SERVICE_KEY
from harness.services.data_management.service import BuiltinDataManagementService

logger = structlog.get_logger()


class DataManagementPlugin(HarnessPlugin):
    """Built-in plugin providing the Data Management service and registering agent tools."""

    name = "data_management"
    version = "1.0.0"
    description = "Enterprise Data Management, ODCS contracts, quality profiling, and Medallion pipelines"

    def __init__(self) -> None:
        self._service: BuiltinDataManagementService | None = None

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [DATA_MANAGEMENT_SERVICE_KEY]

    @property
    def trusted(self) -> bool:
        return True

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name=self.name,
            version=self.version,
            description=self.description,
            provides=["data_management"],
        )

    async def on_load(self, ctx: ServiceContext) -> None:
        bus = ctx.optional(EVENT_BUS_KEY)
        self._service = BuiltinDataManagementService(event_bus=bus)
        ctx.provide(DATA_MANAGEMENT_SERVICE_KEY, self._service, provider=self.name)
        logger.info("Data management service registered", provider=self.name)

    async def on_unload(self) -> None:
        self._service = None

    async def on_enable(self) -> None:
        pass

    async def on_disable(self) -> None:
        pass

    async def enable(self, ctx: ServiceContext) -> None:
        await self.on_load(ctx)
        await self.on_enable()

    async def disable(self, ctx: ServiceContext | None = None) -> None:
        await self.on_disable()
        await self.on_unload()


# Export instantiated module singleton per Rule 45
plugin = DataManagementPlugin()
