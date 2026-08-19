"""Tests for the RepoInspector."""

import json
from pathlib import Path

import pytest

from harness.ingestion.inspector import RepoInspector
from harness.plugins.manifest import IsolationMode


@pytest.mark.unit
class TestRepoInspector:
    def test_inspect_with_plugin_json(self, tmp_path: Path) -> None:
        manifest = {
            "name": "explicit-plugin",
            "version": "1.0.0",
            "description": "Has a plugin.json",
            "entrypoint": "main.py",
        }
        (tmp_path / "plugin.json").write_text(json.dumps(manifest))
        (tmp_path / "main.py").write_text("def run(): pass")

        inspector = RepoInspector()
        result = inspector.inspect(tmp_path)
        assert result.name == "explicit-plugin"
        assert result.version == "1.0.0"

    def test_inspect_with_pyproject(self, tmp_path: Path) -> None:
        pyproject = """
[project]
name = "pyproject-plugin"
version = "2.0.0"
description = "From pyproject"
dependencies = ["requests"]
"""
        (tmp_path / "pyproject.toml").write_text(pyproject)
        (tmp_path / "main.py").write_text("def hello(name: str): pass")

        inspector = RepoInspector()
        result = inspector.inspect(tmp_path)
        assert result.name == "pyproject-plugin"
        assert result.version == "2.0.0"
        assert "requests" in result.dependencies

    def test_inspect_with_package_json(self, tmp_path: Path) -> None:
        pkg = {
            "name": "node-tool",
            "version": "1.0.0",
            "main": "index.js",
        }
        (tmp_path / "package.json").write_text(json.dumps(pkg))

        inspector = RepoInspector()
        result = inspector.inspect(tmp_path)
        assert result.name == "node-tool"
        assert result.language == "javascript"

    def test_inspect_ast_extraction(self, tmp_path: Path) -> None:
        code = '''
def process_data(input_file: str, output_dir: str = "/tmp"):
    """Process data from input file."""
    pass

def _private():
    pass

def analyze(data: list, verbose: bool = False):
    """Run analysis."""
    pass
'''
        (tmp_path / "main.py").write_text(code)

        inspector = RepoInspector()
        result = inspector.inspect(tmp_path)

        # Should find public functions but not private
        ep_names = [ep.name for ep in result.entrypoints]
        assert "process_data" in ep_names
        assert "analyze" in ep_names
        assert "_private" not in ep_names

    def test_inspect_with_requirements(self, tmp_path: Path) -> None:
        (tmp_path / "requirements.txt").write_text("numpy>=1.20\npandas\n# comment\n")
        (tmp_path / "main.py").write_text("def run(): pass")

        inspector = RepoInspector()
        result = inspector.inspect(tmp_path)
        assert "numpy>=1.20" in result.dependencies
        assert "pandas" in result.dependencies
        assert result.isolation == IsolationMode.VENV  # Has deps → needs venv

    def test_inspect_fallback_minimal(self, tmp_path: Path) -> None:
        """Directory with no recognizable metadata produces a minimal manifest."""
        (tmp_path / "readme.txt").write_text("Just a readme")

        inspector = RepoInspector()
        result = inspector.inspect(tmp_path)
        assert result.name == tmp_path.name

    def test_inspect_nonexistent(self) -> None:
        from harness.ingestion.inspector import InspectionError

        inspector = RepoInspector()
        with pytest.raises(InspectionError):
            inspector.inspect(Path("/nonexistent/path"))

    def test_inspect_mcp_json(self, tmp_path: Path) -> None:
        mcp = {
            "name": "mcp-tool",
            "tools": [
                {
                    "name": "search",
                    "description": "Search for items",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer"},
                        },
                        "required": ["query"],
                    },
                }
            ],
        }
        (tmp_path / "mcp.json").write_text(json.dumps(mcp))

        inspector = RepoInspector()
        result = inspector.inspect(tmp_path)
        assert result.name == "mcp-tool"
        assert len(result.entrypoints) == 1
        assert result.entrypoints[0].name == "search"
        assert len(result.entrypoints[0].parameters) == 2


@pytest.mark.unit
@pytest.mark.asyncio
class TestPluginIngestionPipeline:
    async def test_pipeline_ingest_local_zip(self, tmp_path: Path) -> None:
        import zipfile

        from harness.ingestion.pipeline import PluginIngestionPipeline
        from harness.plugins.sandboxed import SandboxedPlugin

        # Create a sample repo directory and zip it
        repo_src = tmp_path / "sample_tool"
        repo_src.mkdir()
        (repo_src / "plugin.json").write_text(
            json.dumps({
                "name": "sample_tool",
                "version": "1.2.0",
                "entrypoint": "main.py",
                "provides": ["tool.sample"],
                "entrypoints": [{"name": "compute", "description": "Compute something"}],
            })
        )
        (repo_src / "main.py").write_text("def compute(x=1):\n    return x * 2\n")

        zip_file = tmp_path / "sample_tool.zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            for file in repo_src.iterdir():
                zf.write(file, arcname=f"sample_tool/{file.name}")

        plugins_dir = tmp_path / "installed_plugins"
        pipeline = PluginIngestionPipeline(plugin_dir=plugins_dir)

        # Ingest
        plugin = await pipeline.ingest(str(zip_file))
        assert isinstance(plugin, SandboxedPlugin)
        assert plugin.name == "sample_tool"
        assert plugin.version == "1.2.0"
        assert len(pipeline.list_cached()) == 1

        # Inspect
        manifest = pipeline.inspect("sample_tool")
        assert manifest.name == "sample_tool"

        # Remove
        assert pipeline.remove_cached("sample_tool") is True
        assert len(pipeline.list_cached()) == 0
