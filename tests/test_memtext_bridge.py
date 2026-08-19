"""Tests for Memtext memory bridge."""

from pathlib import Path

import pytest

from harness.bridges.memtext import (
    MEMORY_SERVICE_KEY,
    LocalMemtextService,
    MemtextServicePlugin,
)
from harness.kernel.context import ServiceContext
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry, ToolRegistryPlugin


@pytest.mark.unit
@pytest.mark.asyncio
class TestMemtextBridge:
    async def test_local_memtext_service(self, tmp_path: Path) -> None:
        service = LocalMemtextService(db_dir=tmp_path)
        assert await service.remember("agent_goal", "Solve the task thoroughly")
        assert await service.remember("math_fact", "2 + 2 equals 4")

        # Recall
        results = await service.recall("math")
        assert len(results) == 1
        assert results[0]["key"] == "math_fact"

        # Decision log
        await service.log_decision("agent_1", "Choose Python surface for execution")
        assert len(service._ledger) == 1

    async def test_memtext_plugin_lifecycle(self) -> None:
        ctx = ServiceContext()
        tool_plugin = ToolRegistryPlugin()
        await tool_plugin.on_load(ctx)

        bridge = MemtextServicePlugin()
        assert bridge.provides == [MEMORY_SERVICE_KEY]
        assert bridge.requires == [TOOL_REGISTRY_KEY]

        await bridge.on_load(ctx)
        assert ctx.has(MEMORY_SERVICE_KEY)

        await bridge.on_enable()
        tool_reg: ToolRegistry = ctx.require(TOOL_REGISTRY_KEY)

        assert "memory.store" in tool_reg
        assert "memory.recall" in tool_reg

        # Test tool invocation
        store_res = await tool_reg.invoke("memory.store", {"key": "k1", "content": "hello memory"})
        assert store_res == {"status": "ok", "result": {"status": "ok", "key": "k1"}}

        recall_res = await tool_reg.invoke("memory.recall", {"query": "hello"})
        assert recall_res["status"] == "ok"
        assert len(recall_res["result"]["memories"]) >= 1

        await bridge.on_disable()
        assert "memory.store" not in tool_reg

        await bridge.on_unload()
