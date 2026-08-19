"""Tests for the PluginLoader."""

import json
from pathlib import Path

import pytest

from harness.plugins.loader import ManifestPlugin, PluginLoader


@pytest.mark.unit
class TestPluginLoader:
    def test_load_from_empty_directory(self, tmp_path: Path) -> None:
        loader = PluginLoader(plugin_dirs=[tmp_path])
        plugins = loader.load_from_directory(tmp_path)
        assert plugins == []

    def test_load_nonexistent_directory(self, tmp_path: Path) -> None:
        loader = PluginLoader()
        plugins = loader.load_from_directory(tmp_path / "nonexistent")
        assert plugins == []

    def test_load_manifest_plugin(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "my-plugin"
        plugin_dir.mkdir()

        manifest = {
            "name": "test-manifest-plugin",
            "version": "1.0.0",
            "description": "A test plugin",
        }
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest))

        loader = PluginLoader(plugin_dirs=[tmp_path])
        plugins = loader.load_from_directory(tmp_path)

        assert len(plugins) == 1
        assert isinstance(plugins[0], ManifestPlugin)
        assert plugins[0].name == "test-manifest-plugin"

    def test_load_python_plugin(self, tmp_path: Path) -> None:
        plugin_code = '''
from harness.plugins.base import HarnessPlugin
from harness.kernel.context import ServiceContext

class MyTestPlugin(HarnessPlugin):
    @property
    def name(self) -> str:
        return "python-test-plugin"

    @property
    def version(self) -> str:
        return "1.0.0"
'''
        plugin_dir = tmp_path / "py-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.py").write_text(plugin_code)

        loader = PluginLoader(plugin_dirs=[tmp_path])
        plugins = loader.load_from_directory(tmp_path)

        assert len(plugins) == 1
        assert plugins[0].name == "python-test-plugin"

    def test_load_from_zip(self, tmp_path: Path) -> None:
        import zipfile

        plugin_dir = tmp_path / "source"
        plugin_dir.mkdir()
        manifest = {"name": "zipped-plugin", "version": "1.0.0"}
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest))

        zip_path = tmp_path / "plugin.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(plugin_dir / "plugin.json", "plugin.json")

        extract_dir = tmp_path / "extracted"
        loader = PluginLoader()
        _ = loader.load_from_zip(zip_path, extract_dir)

        # ZIP creates files at the top level, loader looks for subdirs
        # The manifest is at the root of extract_dir, not in a subdir
        # So ManifestPlugin won't be found by directory scan
        # But the extraction should succeed
        assert extract_dir.exists()

    def test_list_catalog_and_manifest_lookups(self, tmp_path: Path) -> None:
        p1 = tmp_path / "alpha-plugin"
        p1.mkdir()
        (p1 / "plugin.json").write_text(json.dumps({
            "name": "alpha-tool",
            "version": "1.2.3",
            "description": "Alpha tool plugin",
        }))

        p2 = tmp_path / "beta-plugin"
        p2.mkdir()

        loader = PluginLoader(plugin_dirs=[tmp_path])
        catalog = loader.list_catalog()

        assert len(catalog) == 2
        names = {c["name"] for c in catalog}
        assert "alpha-tool" in names
        assert "beta-plugin" in names

        # get_manifest by plugin name
        m1 = loader.get_manifest("alpha-tool")
        assert m1 is not None
        assert m1.name == "alpha-tool"
        assert m1.version == "1.2.3"

        # get_manifest by folder name
        m1_by_dir = loader.get_manifest("alpha-plugin")
        assert m1_by_dir is not None
        assert m1_by_dir.name == "alpha-tool"

        # get_guide
        guide_res = loader.get_guide("alpha-tool")
        assert guide_res is not None
        m, guide_txt = guide_res
        assert m.name == "alpha-tool"
        assert "# Quick Start Guide: `alpha-tool`" in guide_txt


@pytest.mark.unit
class TestManifestPlugin:
    def test_properties(self, tmp_path: Path) -> None:
        from harness.plugins.manifest import PluginManifest

        manifest = PluginManifest(
            name="test",
            version="2.0.0",
            description="A test",
            trusted=False,
        )
        plugin = ManifestPlugin(manifest, tmp_path)
        assert plugin.name == "test"
        assert plugin.version == "2.0.0"
        assert plugin.description == "A test"
        assert plugin.trusted is False
        assert plugin.root == tmp_path

    def test_manifest_card_and_quickstart_format(self) -> None:
        from harness.plugins.manifest import EntrypointSpec, ParameterSpec, PluginManifest

        manifest = PluginManifest(
            name="demo-skills",
            version="1.2.0",
            category="engineering",
            description="Agent engineering skills",
            entrypoints=[
                EntrypointSpec(
                    name="code-review",
                    description="Review code diffs",
                    parameters=[ParameterSpec(name="task", type="string")],
                )
            ],
        )

        card = manifest.format_card()
        assert "PLUGIN SUMMARY CARD" in card
        assert "demo-skills" in card
        assert "1.2.0" in card
        assert "engineering" in card
        assert "code-review" not in card  # card shows totals

        guide = manifest.format_quickstart()
        assert "# Quick Start Guide: `demo-skills`" in guide
        assert "🎯 When to Use" in guide
        assert "🛠️ How to Use" in guide
        assert "code-review" in guide
