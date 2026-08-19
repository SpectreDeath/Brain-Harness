"""Tests for Skill Flywheel bridge."""

import json
from pathlib import Path

import pytest

from harness.bridges.flywheel import FLYWHEEL_BRIDGE_KEY, FlywheelBridgePlugin
from harness.kernel.context import ServiceContext
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry, ToolRegistryPlugin


@pytest.mark.unit
@pytest.mark.asyncio
class TestFlywheelBridge:
    async def test_flywheel_plugin_lifecycle(self, tmp_path: Path) -> None:
        # Create mock skill registry
        reg_file = tmp_path / "skill_registry.json"
        reg_file.write_text(
            json.dumps({
                "code_reviewer": {"description": "Performs code review"},
                "git_fetch": {"description": "Fetches git branches"},
            })
        )

        ctx = ServiceContext()
        tool_plugin = ToolRegistryPlugin()
        await tool_plugin.on_load(ctx)

        bridge = FlywheelBridgePlugin(flywheel_path=tmp_path)
        assert bridge.provides == [FLYWHEEL_BRIDGE_KEY]

        await bridge.on_load(ctx)
        assert ctx.has(FLYWHEEL_BRIDGE_KEY)

        await bridge.on_enable()
        tool_reg: ToolRegistry = ctx.require(TOOL_REGISTRY_KEY)

        assert "skill.code_reviewer" in tool_reg

        # Invoke
        res = await tool_reg.invoke("skill.code_reviewer", {"params": {"file": "main.py"}})
        assert res["status"] == "ok"
        assert res["result"]["skill"] == "code_reviewer"

        await bridge.on_disable()
        assert "skill.code_reviewer" not in tool_reg

        await bridge.on_unload()
