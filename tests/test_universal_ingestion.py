"""Tests for Universal Ingestion Pipeline (OpenAPI, Swagger, PyPI)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from harness.ingestion.openapi_converter import OpenAPIConverter
from harness.ingestion.pipeline import PluginIngestionPipeline
from harness.ingestion.pypi_converter import PyPIConverter, PyPIFetchError
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

    async def test_fetch_metadata_fails_loudly_on_404(self, tmp_path: Path) -> None:
        from unittest.mock import AsyncMock
        converter = PyPIConverter(output_base_dir=tmp_path)

        mock_resp = AsyncMock()
        mock_resp.status_code = 404

        with patch("httpx.AsyncClient.get", return_value=mock_resp):
            with pytest.raises(PyPIFetchError, match="not found on PyPI"):
                await converter.fetch_metadata("nonexistent_package_12345")

    async def test_fetch_metadata_fails_loudly_on_network_error(self, tmp_path: Path) -> None:
        import httpx
        converter = PyPIConverter(output_base_dir=tmp_path)

        with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Connection refused")):
            with pytest.raises(PyPIFetchError, match="Network error contacting PyPI"):
                await converter.fetch_metadata("some_pkg")


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

    async def test_parse_multi_provider_sources(self) -> None:
        from harness.ingestion.providers import RepoProvider, parse_repo_source

        # GitLab
        gl = parse_repo_source("https://gitlab.com/group/subgroup/project/-/tree/v1.0")
        assert gl is not None
        assert gl.provider == RepoProvider.GITLAB
        assert gl.owner == "group/subgroup"
        assert gl.repo == "project"
        assert gl.ref == "v1.0"
        assert "gitlab.com/group/subgroup/project/-/archive/v1.0" in (gl.zip_url or "")

        # Codeberg
        cb = parse_repo_source("https://codeberg.org/forgejo/forgejo/src/branch/main")
        assert cb is not None
        assert cb.provider == RepoProvider.CODEBERG
        assert cb.owner == "forgejo"
        assert cb.repo == "forgejo"
        assert "codeberg.org/forgejo/forgejo/archive/main.zip" in (cb.zip_url or "")

        # Bitbucket
        bb = parse_repo_source("https://bitbucket.org/team/repo")
        assert bb is not None
        assert bb.provider == RepoProvider.BITBUCKET
        assert bb.owner == "team"
        assert bb.repo == "repo"

        # Generic Git
        gg = parse_repo_source("https://custom-git.internal/libs/engine.git")
        assert gg is not None
        assert gg.provider == RepoProvider.GENERIC_GIT
        assert gg.repo == "engine"

    async def test_fetch_gitlab_repository(self, tmp_path: Path) -> None:
        import io
        import zipfile
        from unittest.mock import AsyncMock
        from harness.ingestion.fetcher import RepoFetcher

        # Create mock in-memory zip
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("myrepo/plugin.json", json.dumps({"name": "gitlab_plugin", "version": "1.0.0"}))
            zf.writestr("myrepo/main.py", "def run(): pass")

        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-Length": str(len(buf.getvalue()))}
        mock_resp.content = buf.getvalue()
        mock_resp.raise_for_status = lambda: None

        fetcher = RepoFetcher(plugin_dir=tmp_path / "cache")
        with patch("httpx.AsyncClient.get", return_value=mock_resp):
            target = await fetcher.fetch("https://gitlab.com/myteam/myrepo")
            assert target.exists()
            assert (target / "plugin.json").exists()
            meta = json.loads((target / ".cache_meta.json").read_text(encoding="utf-8"))
            assert meta["source_type"] == "gitlab"

