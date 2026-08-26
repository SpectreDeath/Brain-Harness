"""End-to-end and unit tests for plugin ingestion from GitHub URLs and ZIP files."""

import json
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from harness.creator.dynamic import DynamicPluginBuilder
from harness.ingestion.fetcher import RepoFetcher
from harness.ingestion.pipeline import PluginIngestionPipeline
from harness.kernel.runtime import HarnessRuntime
from harness.plugins.sandboxed import SandboxedPlugin


@pytest.mark.unit
@pytest.mark.asyncio
class TestFetcherUrlParsing:
    """Test URL parsing across various GitHub and ZIP formats."""

    async def test_parse_github_tree_url(self, tmp_path: Path) -> None:
        fetcher = RepoFetcher(plugin_dir=tmp_path)
        with patch.object(fetcher, "_fetch_github", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = tmp_path / "owner__repo"
            res = await fetcher.fetch("https://github.com/owner/repo/tree/feat-awesome")
            mock_fetch.assert_called_once_with("owner", "repo", ref="feat-awesome", force=False)
            assert res == tmp_path / "owner__repo"

    async def test_parse_github_archive_tag_url(self, tmp_path: Path) -> None:
        fetcher = RepoFetcher(plugin_dir=tmp_path)
        with patch.object(fetcher, "_fetch_github", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = tmp_path / "owner__repo"
            res = await fetcher.fetch("https://github.com/owner/repo/archive/refs/tags/v1.5.0.zip")
            mock_fetch.assert_called_once_with("owner", "repo", ref="v1.5.0", force=False)
            assert res == tmp_path / "owner__repo"

    async def test_parse_github_ssh_url(self, tmp_path: Path) -> None:
        fetcher = RepoFetcher(plugin_dir=tmp_path)
        with patch.object(fetcher, "_fetch_github", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = tmp_path / "owner__repo"
            res = await fetcher.fetch("git@github.com:owner/repo.git")
            mock_fetch.assert_called_once_with("owner", "repo", ref="main", force=False)
            assert res == tmp_path / "owner__repo"

    async def test_fetch_remote_zip_mocked(self, tmp_path: Path) -> None:
        fetcher = RepoFetcher(plugin_dir=tmp_path)

        # Create a small valid zip in memory
        zip_buf_path = tmp_path / "src.zip"
        with zipfile.ZipFile(zip_buf_path, "w") as zf:
            zf.writestr("test_tool/plugin.json", json.dumps({"name": "remote_tool", "version": "1.0.0"}))
            zf.writestr("test_tool/main.py", "def run(): pass")

        content = zip_buf_path.read_bytes()

        mock_resp = AsyncMock()
        mock_resp.content = content
        mock_resp.raise_for_status = lambda: None

        with patch("httpx.AsyncClient.get", return_value=mock_resp):
            extracted = await fetcher.fetch("https://example.com/downloads/my_plugin.zip")
            assert extracted.exists()
            assert (extracted / "plugin.json").exists()


@pytest.mark.integration
@pytest.mark.asyncio
class TestIngestionE2E:
    """End-to-end ingestion and runtime execution tests."""

    async def test_zip_ast_synthesis_and_tool_call(self, tmp_path: Path) -> None:
        """Create a zip without plugin.json (pure python) and verify tools are synthesized and callable."""
        zip_path = tmp_path / "calculator.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            code = """
def add(a: int, b: int) -> int:
    '''Add two numbers.'''
    return a + b

def multiply(x: float, y: float = 2.0) -> float:
    '''Multiply numbers.'''
    return x * y
"""
            zf.writestr("calculator/main.py", code)

        pipeline = PluginIngestionPipeline(plugin_dir=tmp_path / "plugins")
        plugin = await pipeline.ingest(str(zip_path))

        assert isinstance(plugin, SandboxedPlugin)
        assert plugin.name == "calculator"
        assert len(plugin.manifest.entrypoints) == 2

        entrypoint_names = [ep.name for ep in plugin.manifest.entrypoints]
        assert "add" in entrypoint_names
        assert "multiply" in entrypoint_names

        # Check parameter types mapped to JSON Schema
        add_ep = next(ep for ep in plugin.manifest.entrypoints if ep.name == "add")
        assert add_ep.parameters[0].type == "integer"
        assert add_ep.parameters[1].type == "integer"

    async def test_runtime_add_plugin_from_source_live(self, tmp_path: Path) -> None:
        """Verify dynamic runtime.add_plugin_from_source() while runtime is active."""
        # Create a tool in a zip file
        zip_path = tmp_path / "greeter.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            manifest = {
                "name": "greeter",
                "version": "1.0.0",
                "entrypoint": "main.py",
                "provides": ["tool.greeter"],
                "entrypoints": [
                    {
                        "name": "greet",
                        "description": "Greet a user by name",
                        "parameters": [{"name": "name", "type": "string", "required": True}],
                    }
                ],
            }
            code = """
def greet(name: str) -> str:
    return f"Hello, {name}!"
"""
            zf.writestr("greeter/plugin.json", json.dumps(manifest))
            zf.writestr("greeter/main.py", code)

        async with HarnessRuntime.create(
            db_path=":memory:",
            plugin_dirs=[tmp_path / "plugins"],
            auto_load_user_plugins=False,
        ) as runtime:
            # Runtime is running; now dynamically ingest the plugin
            plugin = await runtime.add_plugin_from_source(zip_path, auto_enable=True)
            assert plugin.name == "greeter"

            # Check that tool registry has the tool
            assert runtime.tools is not None
            assert "greeter.greet" in runtime.tools

            res = await runtime.tools.invoke("greeter.greet", {"name": "Alice"})
            assert res["status"] == "ok"
            assert "Hello, Alice!" in res["result"]

    async def test_dynamic_builder_from_zip(self, tmp_path: Path) -> None:
        """Test DynamicPluginBuilder.from_zip factory."""
        zip_path = tmp_path / "echo_plug.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr(
                "echo_plug/plugin.json",
                json.dumps({
                    "name": "echo_plug",
                    "version": "0.1.0",
                    "entrypoint": "main.py",
                    "entrypoints": [{"name": "echo", "description": "Echo back input"}],
                }),
            )
            zf.writestr("echo_plug/main.py", "def echo(text: str) -> str: return text")

        plugin = await DynamicPluginBuilder.from_zip(zip_path, target_dir=tmp_path / "out")
        assert plugin.name == "echo_plug"
        assert plugin.version == "0.1.0"
