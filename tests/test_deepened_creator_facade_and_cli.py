"""Comprehensive tests for Deepened Plugin Creator facade, dynamic archetypes, and CLI seams."""

from __future__ import annotations

import collections.abc
from pathlib import Path
from typing import Any, Coroutine

import pytest
from click.testing import CliRunner
from pydantic import BaseModel

from harness.cli import main
from harness.commands.creator import (
    list_archetypes_cmd,
    scaffold_plugin_cmd,
    validate_plugin_cmd,
)
from harness.creator.archetypes import ArchetypeRegistry, PluginArchetype
from harness.creator.creator import PluginCreator
from harness.creator.dynamic import DynamicPluginBuilder
from harness.creator.schema import SchemaInferrer
from harness.kernel.runtime import HarnessRuntime
from harness.plugins.manifest import PluginManifest


class CustomAnalyticsModel(BaseModel):
    metric: str
    value: float


class CustomAnalyticsArchetype(PluginArchetype):
    """Test custom user-defined archetype."""

    @property
    def name(self) -> str:
        return "custom_analytics"

    @property
    def description(self) -> str:
        return "Custom analytics processor archetype"

    def generate_manifest(self, options: Any) -> PluginManifest:
        return PluginManifest(
            name=options.name,
            version=options.version,
            description="Custom analytics manifest",
            language=options.language,
            entrypoint="main.py",
            provides=[f"analytics.{options.name}"],
        )

    def generate_entrypoint_code(self, options: Any) -> str:
        return 'def process(data: dict) -> dict:\n    return {"processed": True}\n'

    def generate_test_code(self, options: Any) -> str:
        return "def test_analytics():\n    assert True\n"

    def generate_project_config(self, options: Any) -> tuple[str, str]:
        return "requirements.txt", "pandas>=2.0.0\n"


@pytest.mark.unit
class TestSchemaInferrerAsyncAndModels:
    def test_coroutine_type_unwrapping(self) -> None:
        async def async_fetch_data(query: str, limit: int = 10) -> dict[str, Any]:
            """Fetch data asynchronously.
            
            Args:
                query: Search query
                limit: Maximum items to return
            """
            return {"query": query, "items": []}

        spec = SchemaInferrer.infer_entrypoint_spec(async_fetch_data)
        assert spec.name == "async_fetch_data"
        assert len(spec.parameters) == 2
        assert spec.parameters[0].name == "query"
        assert spec.parameters[0].type == "string"
        assert spec.parameters[1].name == "limit"
        assert spec.parameters[1].type == "integer"
        assert spec.returns == "object" or spec.returns == "dict"

    def test_pydantic_model_resolution(self) -> None:
        res = SchemaInferrer.python_type_to_schema_type(CustomAnalyticsModel)
        assert res == "object"

    def test_coroutine_annotation_resolution(self) -> None:
        res = SchemaInferrer.python_type_to_schema_type(Coroutine[Any, Any, list[str]])
        assert res == "array"


@pytest.mark.unit
class TestDynamicArchetypeRegistry:
    def setup_method(self) -> None:
        ArchetypeRegistry.reset()

    def teardown_method(self) -> None:
        ArchetypeRegistry.reset()

    def test_register_and_retrieve_custom_archetype(self) -> None:
        assert not ArchetypeRegistry.has("custom_analytics")
        PluginCreator.register_archetype(CustomAnalyticsArchetype)
        assert ArchetypeRegistry.has("custom_analytics")

        arch = PluginCreator.get_archetype("custom_analytics")
        assert arch.name == "custom_analytics"
        assert "Custom analytics" in arch.description

    def test_unregister_archetype(self) -> None:
        PluginCreator.register_archetype(CustomAnalyticsArchetype())
        assert ArchetypeRegistry.has("custom_analytics")
        removed = PluginCreator.unregister_archetype("custom_analytics")
        assert removed is True
        assert not ArchetypeRegistry.has("custom_analytics")


@pytest.mark.asyncio
@pytest.mark.unit
class TestPluginCreatorDeepenedOperations:
    async def test_scaffold_and_mount_on_runtime(self, tmp_path: Path) -> None:
        target = tmp_path / "live_mounted_plugin"

        async with HarnessRuntime.create(db_path=":memory:") as runtime:
            scaffold_res, plugin = await PluginCreator.scaffold_and_mount(
                runtime=runtime,
                target_dir=target,
                name="live_mounted_plugin",
                tools=["calc_sum"],
                auto_enable=True,
            )

            assert scaffold_res.exists()
            assert plugin.name == "live_mounted_plugin"
            assert runtime.lifecycle.get_state("live_mounted_plugin").value == "enabled"

    async def test_pure_async_command_functions(self, tmp_path: Path) -> None:
        target = tmp_path / "cmd_scaffolded_plugin"
        res = await scaffold_plugin_cmd(
            name="cmd_scaffolded_plugin",
            target_dir=target,
            preset="tool",
            language="python",
            tools=["analyze_metrics"],
            auto_validate=True,
        )

        assert res.path.exists()
        assert (res.path / "plugin.json").exists()

        report = await validate_plugin_cmd(target)
        assert report.valid is True

        archetypes = list_archetypes_cmd()
        assert len(archetypes) >= 7
        assert any(a["name"] == "tool" for a in archetypes)


@pytest.mark.unit
class TestCreatorCLISeams:
    def test_cli_top_level_create(self, tmp_path: Path) -> None:
        runner = CliRunner()
        target = tmp_path / "cli_created_tool"
        result = runner.invoke(main, [
            "create",
            "cli_created_tool",
            "--target-dir", str(target),
            "--preset", "tool",
            "--tools", "search,filter",
        ])
        assert result.exit_code == 0
        assert "Created plugin scaffold" in result.output
        assert (target / "plugin.json").exists()

    def test_cli_top_level_validate(self, tmp_path: Path) -> None:
        runner = CliRunner()
        target = tmp_path / "cli_valid_plug"
        runner.invoke(main, ["create", "cli_valid_plug", "--target-dir", str(target)])

        result = runner.invoke(main, ["validate", str(target)])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_cli_top_level_archetypes(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["archetypes"])
        assert result.exit_code == 0
        assert "Available Plugin Archetypes" in result.output
        assert "general" in result.output
        assert "agentic_workflow" in result.output


@pytest.mark.unit
class TestDynamicPluginBuilderDelegation:
    def test_builder_delegates_scaffold(self, tmp_path: Path) -> None:
        target = tmp_path / "builder_scaffolded"
        out_path = DynamicPluginBuilder.scaffold_project(
            target_dir=target,
            name="builder_scaffolded",
            preset="service",
        )
        assert out_path.exists()
        assert (out_path / "plugin.json").exists()

    @pytest.mark.asyncio
    async def test_builder_delegates_validate(self, tmp_path: Path) -> None:
        target = tmp_path / "builder_validated"
        DynamicPluginBuilder.scaffold_project(target_dir=target, name="builder_validated")
        report = await DynamicPluginBuilder.validate_project(target)
        assert report.valid is True
