"""Built-in plugin exposing SwarmCoordinator service (Rule 1, Rule 2, Rule 45)."""

from __future__ import annotations

from harness.agent.swarm.coordinator import SWARM_COORDINATOR_KEY, SwarmCoordinator
from harness.kernel.context import ServiceContext
from harness.plugins.base import HarnessPlugin


class SwarmCoordinatorPlugin(HarnessPlugin):
    """Built-in plugin exposing the SwarmCoordinator service."""

    name = "agent.swarm"
    version = "1.0.0"
    description = "Hierarchical multi-agent swarm and consensus orchestrator"
    provides = [SWARM_COORDINATOR_KEY]

    def __init__(self) -> None:
        self._coordinator: SwarmCoordinator | None = None

    @property
    def trusted(self) -> bool:
        return True

    async def on_load(self, ctx: ServiceContext) -> None:
        from harness.events.bus import EVENT_BUS_KEY

        bus = ctx.optional(EVENT_BUS_KEY)
        self._coordinator = SwarmCoordinator(context=ctx, event_bus=bus)
        ctx.provide(SWARM_COORDINATOR_KEY, self._coordinator)


# Module-level singleton export per Rule 45
plugin = SwarmCoordinatorPlugin()

__all__ = ["SwarmCoordinatorPlugin", "plugin"]
