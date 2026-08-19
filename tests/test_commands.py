from pathlib import Path

import pytest

from harness.commands.agent import FallbackLLM, run_agent
from harness.commands.system import list_services, run_introspect


@pytest.mark.unit
@pytest.mark.asyncio
class TestCommands:
    async def test_fallback_llm(self) -> None:
        llm = FallbackLLM()
        res = await llm.complete([])
        assert "FINAL ANSWER" in res.content

        chunks = [c async for c in llm.stream([])]
        assert len(chunks) == 1
        assert "FINAL ANSWER" in chunks[0]

    async def test_run_agent(self) -> None:
        result = await run_agent("Test command task", max_steps=3)
        assert result.status in ("completed", "max_steps")
        assert result.final_answer != ""

    async def test_list_services(self) -> None:
        srvs = await list_services()
        assert isinstance(srvs, dict)
        assert "tools.registry" in srvs or "storage.sqlite" in srvs

    async def test_run_introspect(self) -> None:
        report = await run_introspect()
        assert "plugins_count" in report
        assert "services_count" in report
        assert "graph" in report
        assert "graph TD" in report["graph"]

    async def test_tool_and_plugin_commands(self) -> None:
        from harness.commands.tools import (
            disable_tool,
            disable_tool_by_name,
            enable_tool,
            enable_tool_by_name,
            list_tools,
            list_tools_summary,
            toggle_tool,
        )
        from harness.commands.plugins import (
            disable_all_plugins,
            disable_plugin_by_name,
            enable_all_plugins,
            enable_plugin_by_name,
        )
        from harness.services.tools import ToolRegistry

        registry = ToolRegistry()
        async def dummy() -> None: pass
        registry.register("t1", "Tool 1", dummy, provider="p1")

        # Test list_tools
        tools = list_tools(registry)
        assert len(tools) == 1
        assert tools[0]["name"] == "t1"
        assert tools[0]["enabled"] is True

        # Test disable_tool and enable_tool
        assert disable_tool(registry, "t1") is True
        assert list_tools(registry, enabled_only=True) == []

        assert enable_tool(registry, "t1") is True
        assert len(list_tools(registry, enabled_only=True)) == 1

        assert toggle_tool(registry, "t1") is True
        assert list_tools(registry, enabled_only=True) == []

        # Standalone tool commands
        tool_summary = await list_tools_summary()
        assert isinstance(tool_summary, list)

        t_enabled = await enable_tool_by_name("nonexistent_tool_xyz")
        assert t_enabled == []

        t_disabled = await disable_tool_by_name("nonexistent_tool_xyz")
        assert t_disabled == []

        # Standalone plugin commands
        p_enabled = await enable_plugin_by_name("nonexistent_plugin_xyz")
        assert p_enabled == []

        p_disabled = await disable_plugin_by_name("nonexistent_plugin_xyz")
        assert p_disabled == []

        all_enabled = await enable_all_plugins()
        assert isinstance(all_enabled, dict)

        all_disabled = await disable_all_plugins(keep_core=True)
        assert isinstance(all_disabled, list)


    async def test_plugin_catalog_commands(self, tmp_path: Path) -> None:
        import json
        from harness.commands.plugins import get_plugin_guide, get_plugin_manifest, list_plugins

        test_dir = tmp_path / "plugins_cmd"
        test_dir.mkdir(parents=True, exist_ok=True)
        p1 = test_dir / "my-plugin"
        p1.mkdir()
        (p1 / "plugin.json").write_text(
            json.dumps({"name": "cmd-test-plugin", "version": "1.0.0", "description": "Test"})
        )

        catalog = list_plugins(plugin_dir=test_dir)
        assert len(catalog) == 1
        assert catalog[0]["name"] == "cmd-test-plugin"

        manifest = get_plugin_manifest("cmd-test-plugin", plugin_dir=test_dir)
        assert manifest is not None
        assert manifest.name == "cmd-test-plugin"

        guide_res = get_plugin_guide("cmd-test-plugin", plugin_dir=test_dir)
        assert guide_res is not None
        m, guide_txt = guide_res
        assert m.name == "cmd-test-plugin"
        assert "# Quick Start Guide" in guide_txt
