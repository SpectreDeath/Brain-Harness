"""Tests for Creator Mode dynamic plugin builder and runtime introspector."""

from pathlib import Path

import pytest

from harness.creator.dynamic import DynamicPluginBuilder, RuntimeIntrospector
from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistryPlugin


@pytest.mark.unit
@pytest.mark.asyncio
class TestCreatorMode:
    async def test_dynamic_plugin_from_functions(self) -> None:
        def custom_calc(n: int) -> int:
            """Calculate double."""
            return n * 2

        plugin = DynamicPluginBuilder.from_functions(
            name="dynamic-calc",
            functions=[custom_calc],
            description="Dynamic calculation tool",
        )

        ctx = ServiceContext()
        tools_plugin = ToolRegistryPlugin()
        await tools_plugin.on_load(ctx)

        await plugin.on_load(ctx)
        await plugin.on_enable()

        tool_reg = ctx.require(TOOL_REGISTRY_KEY)
        assert "custom_calc" in tool_reg

        # Verify schema generated from type annotations
        spec = tool_reg.get("custom_calc")
        assert spec is not None
        assert spec.parameters_schema.get("properties", {}).get("n", {}).get("type") == "integer"
        assert spec.parameters_schema.get("required") == ["n"]

        res = await tool_reg.invoke("custom_calc", {"n": 21})
        assert res == {"status": "ok", "result": 42}

        await plugin.on_disable()
        assert "custom_calc" not in tool_reg

    async def test_tool_spec_from_callable_direct(self) -> None:
        from harness.services.tools import ToolSpec

        def sample_fn(name: str, count: int = 1, tags: list[str] | None = None) -> str:
            """A sample function."""
            return f"{name}: {count}"

        spec = ToolSpec.from_callable(sample_fn, provider="test_provider")
        assert spec.name == "sample_fn"
        assert spec.description == "A sample function."
        assert spec.provider == "test_provider"
        props = spec.parameters_schema.get("properties", {})
        assert props.get("name", {}).get("type") == "string"
        assert props.get("count", {}).get("type") == "integer"
        assert props.get("count", {}).get("default") == 1
        assert props.get("tags", {}).get("type") == "array"
        assert spec.parameters_schema.get("required") == ["name"]

    async def test_dynamic_plugin_from_code(self) -> None:
        code = """
def string_reverse(s: str) -> str:
    return s[::-1]
"""
        plugin = DynamicPluginBuilder.from_code("dynamic-str", code)

        ctx = ServiceContext()
        tools_plugin = ToolRegistryPlugin()
        await tools_plugin.on_load(ctx)

        await plugin.on_load(ctx)
        await plugin.on_enable()

        tool_reg = ctx.require(TOOL_REGISTRY_KEY)
        assert "string_reverse" in tool_reg

        res = await tool_reg.invoke("string_reverse", {"s": "harness"})
        assert res == {"status": "ok", "result": "ssenrah"}

        await plugin.on_disable()

    async def test_scaffold_project(self, tmp_path: Path) -> None:
        target = tmp_path / "my_new_plugin"
        DynamicPluginBuilder.scaffold_project(target, "my-new-plugin", "Test plugin description")

        assert (target / "plugin.json").exists()
        assert (target / "main.py").exists()

    async def test_runtime_introspector(self) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        tools_plugin = ToolRegistryPlugin()

        lifecycle.discover(tools_plugin)
        await lifecycle.load(tools_plugin.name)
        await lifecycle.validate(tools_plugin.name)
        await lifecycle.enable(tools_plugin.name)

        introspector = RuntimeIntrospector(ctx, lifecycle, tools_plugin._registry)
        report = introspector.get_status_report()

        assert report["plugins_count"] == 1
        assert "tools.registry" in report["plugins"]
        assert report["services_count"] == 1

        mermaid = introspector.generate_mermaid_graph()
        assert "graph TD" in mermaid
        assert "tools.registry" in mermaid
        assert "provides" in mermaid

        # Test requires edge with agent plugin
        from harness.agent.react import ReActAgentPlugin
        agent_plugin = ReActAgentPlugin()
        lifecycle.discover(agent_plugin)
        mermaid2 = introspector.generate_mermaid_graph()
        assert "requires" in mermaid2
