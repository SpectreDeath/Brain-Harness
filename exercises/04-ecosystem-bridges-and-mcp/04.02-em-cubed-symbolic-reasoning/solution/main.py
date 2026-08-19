"""Exercise 04.02: Em-Cubed Neuro-Symbolic Reasoning Bridge (Solution)."""

from __future__ import annotations

from typing import Any

from harness.bridges.em_cubed import EM_CUBED_BRIDGE_KEY, EmCubedPlugin
from harness.kernel.context import ServiceContext
from harness.services.tools import ToolRegistryPlugin


async def run_logic_reasoning() -> dict[str, Any]:
    ctx = ServiceContext()

    tools_plugin = ToolRegistryPlugin()
    await tools_plugin.on_load(ctx)
    await tools_plugin.on_enable()

    em3_plugin = EmCubedPlugin()
    await em3_plugin.on_load(ctx)
    await em3_plugin.on_enable()

    em3_bridge: EmCubedPlugin = ctx.require(EM_CUBED_BRIDGE_KEY)
    return await em3_bridge.execute_surface("sqlite", "SELECT 42 as result;")
