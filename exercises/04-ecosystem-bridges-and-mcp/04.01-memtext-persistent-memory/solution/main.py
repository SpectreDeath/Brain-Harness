"""Exercise 04.01: Memtext Persistent Memory Bridge (Solution)."""

from __future__ import annotations

from typing import Any

from harness.bridges.memtext import (
    MEMORY_SERVICE_KEY,
    MemtextService,
    MemtextServicePlugin,
)
from harness.kernel.context import ServiceContext
from harness.services.tools import ToolRegistryPlugin


async def run_memory_workflow() -> list[dict[str, Any]]:
    ctx = ServiceContext()

    tools_plugin = ToolRegistryPlugin()
    await tools_plugin.on_load(ctx)
    await tools_plugin.on_enable()

    mem_plugin = MemtextServicePlugin()
    await mem_plugin.on_load(ctx)
    await mem_plugin.on_enable()

    mem: MemtextService = ctx.require(MEMORY_SERVICE_KEY)
    await mem.remember("user_pref_theme", "dark_mode")
    await mem.remember("user_pref_font", "jetbrains_mono")

    return await mem.recall("user_pref")
