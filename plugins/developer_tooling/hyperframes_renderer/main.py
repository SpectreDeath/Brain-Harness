"""HyperFrames programmatic video renderer plugin entrypoint."""
from __future__ import annotations

import logging
from typing import Any

from harness.kernel.context import ServiceContext
from harness.plugins.base import HarnessPlugin
from harness.services.hyperframes.keys import HYPERFRAMES_SERVICE_KEY
from harness.services.hyperframes.protocols import HyperFramesService
from harness.services.hyperframes.service import DefaultHyperFramesService
from plugins.developer_tooling.hyperframes_renderer.tools import (
    hyperframes_preview_html,
    hyperframes_render_pr_diff_timeline,
    hyperframes_render_trajectory_video,
    hyperframes_runtime_status,
)

logger = logging.getLogger(__name__)


class HyperFramesPlugin(HarnessPlugin):
    """Plugin providing programmatic multimedia video rendering via HyperFrames."""

    name = "domain.hyperframes_renderer"
    version = "0.1.0"
    category = "developer_tooling"
    trusted = True

    def __init__(self, service: HyperFramesService | None = None) -> None:
        self._service = service or DefaultHyperFramesService()

    @property
    def provides(self) -> list[Any]:
        return [HYPERFRAMES_SERVICE_KEY]

    @property
    def requires(self) -> list[Any]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register the DefaultHyperFramesService into the IoC container."""
        logger.info("Initializing HyperFramesPlugin", plugin=self.name)
        context.provide(HYPERFRAMES_SERVICE_KEY, self._service, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("HyperFramesPlugin enabled", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("HyperFramesPlugin disabled", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("HyperFramesPlugin unloaded", plugin=self.name)

    def get_tools(self) -> list[Any]:
        """Expose multimedia video generation tools."""
        return [
            hyperframes_runtime_status,
            hyperframes_preview_html,
            hyperframes_render_trajectory_video,
            hyperframes_render_pr_diff_timeline,
        ]


# Rule 45: instantiated module singleton export
plugin = HyperFramesPlugin()
