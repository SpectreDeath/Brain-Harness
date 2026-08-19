"""Tests for Plugin Archetypes, ArchetypeRegistry, and polymorphic scaffolding."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.creator.archetypes import (
    ApiWrapperArchetype,
    ArchetypeRegistry,
    GeneralArchetype,
    McpBridgeArchetype,
    ServiceArchetype,
    ToolArchetype,
)
from harness.creator.scaffold import PluginScaffoldEngine, ScaffoldOptions


@pytest.mark.unit
class TestPluginArchetypes:
    def test_archetype_registry_lookup(self) -> None:
        general = ArchetypeRegistry.get("general")
        assert isinstance(general, GeneralArchetype)

        tool = ArchetypeRegistry.get("tool")
        assert isinstance(tool, ToolArchetype)

        api = ArchetypeRegistry.get("api_wrapper")
        assert isinstance(api, ApiWrapperArchetype)

        service = ArchetypeRegistry.get("service")
        assert isinstance(service, ServiceArchetype)

        mcp = ArchetypeRegistry.get("mcp_bridge")
        assert isinstance(mcp, McpBridgeArchetype)

        # Fallback to general
        unknown = ArchetypeRegistry.get("non_existent_preset")
        assert isinstance(unknown, GeneralArchetype)

    def test_list_archetypes(self) -> None:
        archs = ArchetypeRegistry.list_archetypes()
        assert len(archs) >= 5
        names = [a["name"] for a in archs]
        assert "general" in names
        assert "tool" in names
        assert "api_wrapper" in names
        assert "service" in names
        assert "mcp_bridge" in names

    def test_scaffold_api_wrapper_archetype(self, tmp_path: Path) -> None:
        target = tmp_path / "my_api_plugin"
        engine = PluginScaffoldEngine()
        engine.scaffold(
            target,
            options=ScaffoldOptions(
                name="my-api-plugin",
                preset="api_wrapper",
                language="python",
                tools=["fetch_rates", "post_order"],
                dependencies=["httpx>=0.27.0"],
            ),
        )

        assert (target / "plugin.json").exists()
        assert (target / "main.py").exists()
        assert (target / "requirements.txt").exists()
        assert (target / "tests" / "test_plugin.py").exists()

        manifest_data = json.loads((target / "plugin.json").read_text(encoding="utf-8"))
        assert manifest_data["category"] == "bridge"
        assert len(manifest_data["entrypoints"]) == 2
        assert manifest_data["entrypoints"][0]["name"] == "fetch_rates"

        main_code = (target / "main.py").read_text(encoding="utf-8")
        assert "async def fetch_rates" in main_code
        assert "httpx.AsyncClient" in main_code

        reqs = (target / "requirements.txt").read_text(encoding="utf-8")
        assert "httpx>=0.27.0" in reqs

    def test_scaffold_service_archetype(self, tmp_path: Path) -> None:
        target = tmp_path / "my_service_plugin"
        engine = PluginScaffoldEngine()
        engine.scaffold(
            target,
            options=ScaffoldOptions(
                name="vector_store",
                preset="service",
                language="python",
            ),
        )

        assert (target / "plugin.json").exists()
        assert (target / "main.py").exists()
        assert (target / "tests" / "test_plugin.py").exists()

        manifest_data = json.loads((target / "plugin.json").read_text(encoding="utf-8"))
        assert manifest_data["provides"] == ["service.vector_store"]
        assert manifest_data["trusted"] is True

        main_code = (target / "main.py").read_text(encoding="utf-8")
        assert "class VectorStoreService:" in main_code
        assert "class VectorStoreServicePlugin(HarnessPlugin):" in main_code

    def test_scaffold_mcp_bridge_archetype(self, tmp_path: Path) -> None:
        target = tmp_path / "my_mcp_bridge"
        engine = PluginScaffoldEngine()
        engine.scaffold(
            target,
            options=ScaffoldOptions(
                name="mcp_eval",
                preset="mcp_bridge",
                language="python",
            ),
        )

        assert (target / "plugin.json").exists()
        assert (target / "main.py").exists()

        manifest_data = json.loads((target / "plugin.json").read_text(encoding="utf-8"))
        assert manifest_data["category"] == "bridge"
        assert manifest_data["entrypoints"][0]["name"] == "mcp_call"

        main_code = (target / "main.py").read_text(encoding="utf-8")
        assert "def mcp_call" in main_code
