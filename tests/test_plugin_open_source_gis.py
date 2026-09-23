"""Test contracts for open_source_gis plugin, lifecycle, and exposed tools."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from harness.kernel.context import ServiceContext
from harness.services.open_source_gis import (
    OPEN_SOURCE_GIS_SERVICE_KEY,
    OpenSourceGisService,
)
from plugins.geospatial_and_osint.open_source_gis.main import (
    OpenSourceGisPlugin,
    gis_architect_workload,
    gis_audit_topology,
    gis_route_workload,
    gis_validate_pipeline,
    plugin,
)

PLUGIN_DIR = Path(__file__).parent.parent / "plugins" / "geospatial_and_osint" / "open_source_gis"


@pytest.mark.unit
class TestOpenSourceGisPluginContract:
    """Verify plugin manifest, singleton export, and lifecycle methods."""

    def test_plugin_module_singleton_export(self) -> None:
        """Rule 45: Verify plugin exports an instantiated module-level singleton."""
        assert isinstance(plugin, OpenSourceGisPlugin)
        assert isinstance(plugin, OpenSourceGisService)
        assert plugin.name == "plugin.open_source_gis"
        assert plugin.version == "1.0.0"
        assert OPEN_SOURCE_GIS_SERVICE_KEY in plugin.provides
        assert plugin.requires == []

    def test_plugin_json_manifest(self) -> None:
        """Verify plugin.json exists, declares trusted=true and matches tool entrypoints."""
        manifest_p = PLUGIN_DIR / "plugin.json"
        assert manifest_p.exists()
        manifest = json.loads(manifest_p.read_text(encoding="utf-8"))
        assert manifest["name"] == "plugin.open_source_gis"
        assert manifest["trusted"] is True
        assert "service.open_source_gis" in manifest["provides"]
        entrypoint_names = {ep["name"] for ep in manifest["entrypoints"]}
        assert "gis_route_workload" in entrypoint_names
        assert "gis_validate_pipeline" in entrypoint_names
        assert "gis_audit_topology" in entrypoint_names
        assert "gis_architect_workload" in entrypoint_names

    def test_config_default_yaml_schema(self) -> None:
        """Rule 44: Verify co-located config.default.yaml exists with operational budgets."""
        cfg_p = PLUGIN_DIR / "config.default.yaml"
        assert cfg_p.exists()
        cfg = yaml.safe_load(cfg_p.read_text(encoding="utf-8"))
        assert "operational_budgets" in cfg
        assert cfg["operational_budgets"]["max_raster_memory_mb"] == 4096
        assert "scoring_weights" in cfg
        assert "domain_gates" in cfg

    @pytest.mark.asyncio
    async def test_plugin_lifecycle_and_ioc_registration(self) -> None:
        """Verify on_load provides service into IoC context, and lifecycle hooks execute cleanly."""
        context = ServiceContext()
        test_plugin = OpenSourceGisPlugin()

        await test_plugin.on_load(context)
        resolved = context.require(OPEN_SOURCE_GIS_SERVICE_KEY)
        assert resolved is test_plugin
        assert isinstance(resolved, OpenSourceGisService)

        await test_plugin.on_enable()
        await test_plugin.on_disable()
        await test_plugin.on_unload()


@pytest.mark.unit
class TestPluginEntrypointTools:
    """Verify tool functions serialize cleanly to dictionaries for agent execution."""

    def test_tool_gis_route_workload(self) -> None:
        result = gis_route_workload(
            domain="lidar_hydrology",
            geometry_type="point_cloud",
            data_formats=["LAS", "LAZ"],
            has_lidar=True,
        )
        assert isinstance(result, dict)
        assert result["routing_path"] == "lidar_hydrology_whitebox_gat"
        assert result["primary_engine"]["name"] == "Whitebox GAT"
        assert result["primary_engine"]["fitness_score"] >= 0.95
        assert result["secondary_engine"]["name"] == "SAGA GIS"

    def test_tool_gis_validate_pipeline(self) -> None:
        valid_steps = [
            {
                "step_id": 1,
                "operation": "reproject",
                "engine": "qgis",
                "input_crs": "EPSG:4326",
                "output_crs": "EPSG:32632",
            },
            {
                "step_id": 2,
                "operation": "buffer",
                "engine": "qgis",
                "input_crs": "EPSG:32632",
                "output_crs": "EPSG:32632",
            },
        ]
        res = gis_validate_pipeline(valid_steps)
        assert res["is_valid"] is True
        assert res["total_steps"] == 2

    def test_tool_gis_audit_topology(self) -> None:
        features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]]],
                },
                "properties": {"area_m2": 100.0},
            }
        ]
        res = gis_audit_topology(features)
        assert res["is_valid"] is True
        assert res["severity"] == "OK"
        assert res["sliver_count"] == 0

    def test_tool_gis_architect_workload(self) -> None:
        profile = {
            "domain": "terrain_morphometry",
            "geometry_type": "raster_dem",
            "analysis": "twi",
            "data_formats": ["GeoTIFF"],
        }
        res = gis_architect_workload(workload_profile=profile, generate_brief=True)
        assert res["primary_engine"] == "SAGA GIS"
        assert res["pipeline_valid"] is True
        assert res["visual_brief_path"] is not None
        assert Path(res["visual_brief_path"]).exists()
