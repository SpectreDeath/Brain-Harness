"""Exercise 04.01: Memtext Persistent Memory Bridge (Problem)."""

from __future__ import annotations

from typing import Any

from harness.bridges.memtext import MemtextServicePlugin
from harness.kernel.context import ServiceContext
from harness.services.tools import ToolRegistryPlugin


async def run_memory_workflow() -> list[dict[str, Any]]:
    ctx = ServiceContext()

    tools_plugin = ToolRegistryPlugin()
    await tools_plugin.on_load(ctx)
    await tools_plugin.on_enable()

    mem_plugin = MemtextServicePlugin()  # noqa: F841
    # TODO: Load and enable mem_plugin
    # TODO: Get memory service from ctx under MEMORY_SERVICE_KEY
    # TODO: Store memory "user_pref_theme" with "dark_mode"
    # TODO: Store memory "user_pref_font" with "jetbrains_mono"
    # TODO: Recall memories matching "user_pref" and return results
    raise NotImplementedError
