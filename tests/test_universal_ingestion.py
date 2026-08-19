"""Tests for Universal Ingestion Pipeline (OpenAPI, Swagger, PyPI)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from harness.ingestion.openapi_converter import OpenAPIConverter
from harness.ingestion.pipeline import PluginIngestionPipeline
from harness.ingestion.pypi_converter import PyPIConverter
from harness.plugins.manifest import IsolationMode


@pytest.mark.unit
class TestOpenAPIConverter:
    def test_convert_openapi_spec(self, tmp_path: Path) -> None:
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Petstore Service",
                "version": "1.0.0",
                "description": "Sample Petstore API",
            },
            "servers": [{"url": "https://petstore.swagger.io/v2"}],
            "paths": {
                "/pets": {
                    "get": {
                        "operationId": "listPets",
                        "summary": "List all pets",
                        "parameters": [
                            {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}},
                        ],
                    },
                    "post": {
                        "operationId": "createPet",
                        "summary": "Create a pet",
                        "parameters": [
                            {"name": "name", "in": "query", "required": True, "schema": {"type": "string"}},
                        ],
                    },
                },
            },
        }

        converter = OpenAPIConverter(output_base_dir=tmp_path)
        out_dir = converter.convert(spec, tmp_path / "petstore_plugin")

        assert out_dir.exists()
        assert (out_dir / "plugin.json").exists()
        assert (out_dir / "main.py").exists()

        manifest_data = json.loads((out_dir / "plugin.json").read_text(encoding="utf-8"))
        assert manifest_data["name"] == "petstore_service"
        assert len(manifest_data["entrypoints"]) == 2
        entrypoint_names = {ep["name"] for ep in manifest_data["entrypoints"]}
        assert "listpets" in entrypoint_names
        assert "createpet" in entrypoint_names


@pytest.mark.unit
@pytest.mark.asyncio
class TestPyPIConverter:
    async def test_convert_pypi_package(self, tmp_path: Path) -> None:
        converter = PyPIConverter(output_base_dir=tmp_path)

        mock_meta = {
            "info": {
                "name": "sample_math",
                "version": "2.4.0",
                "summary": "Fast math algorithms",
                "author": "Math Team",
            }
        }

        with patch.object(converter, "fetch_metadata", return_value=mock_meta):
            out_dir = await converter.convert("pypi:sample_math", tmp_path / "sample_math")

            assert out_dir.exists()
            assert (out_dir / "plugin.json").exists()
            assert (out_dir / "main.py").exists()

            manifest_data = json.loads((out_dir / "plugin.json").read_text(encoding="utf-8"))
            assert manifest_data["name"] == "sample_math"
            assert manifest_data["isolation"] == IsolationMode.VENV.value
            assert "sample_math" in manifest_data["dependencies"]


@pytest.mark.unit
@pytest.mark.asyncio
class TestUniversalPipelineIngest:
    async def test_pipeline_ingest_openapi_file(self, tmp_path: Path) -> None:
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(
            json.dumps({
                "openapi": "3.0.0",
                "info": {"title": "Weather API", "version": "1.0.0"},
                "paths": {
                    "/forecast": {
                        "get": {"operationId": "getForecast", "summary": "Get weather forecast"}
                    }
                },
            }),
            encoding="utf-8",
        )

        pipeline = PluginIngestionPipeline(plugin_dir=tmp_path / "installed_plugins")
        plugin = await pipeline.ingest(f"openapi:{spec_file}")

        assert plugin is not None
        assert plugin.name == "weather_api"
        assert len(plugin.manifest.entrypoints) == 1
        assert plugin.manifest.entrypoints[0].name == "getforecast"

    async def test_pipeline_ingest_pypi_prefix(self, tmp_path: Path) -> None:
        pipeline = PluginIngestionPipeline(plugin_dir=tmp_path / "installed_plugins")

        with patch("harness.ingestion.pypi_converter.PyPIConverter.fetch_metadata", return_value={
            "info": {"name": "slugify_lib", "version": "1.2.0", "summary": "String slugifier"}
        }):
            plugin = await pipeline.ingest("pypi:slugify_lib")
            assert plugin is not None
            assert plugin.name == "slugify_lib"
            assert plugin.manifest.isolation == IsolationMode.VENV
