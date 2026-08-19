"""Tests for the PluginManifest schema."""

import json
from pathlib import Path

import pytest

from harness.plugins.manifest import (
    EntrypointSpec,
    IsolationMode,
    ParameterSpec,
    PluginManifest,
)


@pytest.mark.unit
class TestPluginManifest:
    def test_minimal(self) -> None:
        m = PluginManifest.minimal("test-plugin")
        assert m.name == "test-plugin"
        assert m.version == "0.0.0"
        assert m.isolation == IsolationMode.SUBPROCESS

    def test_full_manifest(self) -> None:
        m = PluginManifest(
            name="my-tool",
            version="1.2.3",
            description="A cool tool",
            language="python",
            entrypoint="main.py",
            provides=["tool.my-tool"],
            requires=["llm.provider"],
            isolation=IsolationMode.VENV,
            entrypoints=[
                EntrypointSpec(
                    name="run",
                    description="Execute",
                    parameters=[
                        ParameterSpec(name="input", type="string", required=True)
                    ],
                )
            ],
            dependencies=["requests>=2.28"],
        )
        assert m.name == "my-tool"
        assert len(m.entrypoints) == 1
        assert m.entrypoints[0].parameters[0].name == "input"

    def test_from_file(self, tmp_path: Path) -> None:
        manifest_data = {
            "name": "file-plugin",
            "version": "2.0.0",
            "description": "From file",
            "language": "python",
            "entrypoint": "main.py",
        }
        path = tmp_path / "plugin.json"
        path.write_text(json.dumps(manifest_data))

        m = PluginManifest.from_file(path)
        assert m.name == "file-plugin"
        assert m.version == "2.0.0"

    def test_to_file(self, tmp_path: Path) -> None:
        m = PluginManifest(name="write-test", version="1.0.0")
        path = tmp_path / "plugin.json"
        m.to_file(path)

        assert path.exists()
        loaded = json.loads(path.read_text())
        assert loaded["name"] == "write-test"

    def test_roundtrip(self, tmp_path: Path) -> None:
        original = PluginManifest(
            name="roundtrip",
            version="3.0.0",
            description="Test roundtrip",
            provides=["svc.a", "svc.b"],
            requires=["svc.c"],
            isolation=IsolationMode.VENV,
            dependencies=["numpy", "pandas"],
        )
        path = tmp_path / "plugin.json"
        original.to_file(path)
        loaded = PluginManifest.from_file(path)

        assert loaded.name == original.name
        assert loaded.version == original.version
        assert loaded.provides == original.provides
        assert loaded.requires == original.requires
        assert loaded.isolation == original.isolation
        assert loaded.dependencies == original.dependencies

    def test_from_package_json(self, tmp_path: Path) -> None:
        pkg = {
            "name": "my-node-tool",
            "version": "1.0.0",
            "description": "A node tool",
            "main": "index.js",
        }
        path = tmp_path / "package.json"
        path.write_text(json.dumps(pkg))

        m = PluginManifest.from_package_json(path)
        assert m.name == "my-node-tool"
        assert m.language == "javascript"
        assert m.entrypoint == "index.js"


class TestIsolationMode:
    def test_default_is_subprocess(self) -> None:
        m = PluginManifest(name="test")
        assert m.isolation == IsolationMode.SUBPROCESS

    def test_trusted_override(self) -> None:
        m = PluginManifest(name="test", trusted=True, isolation=IsolationMode.IN_PROCESS)
        assert m.trusted is True
        assert m.isolation == IsolationMode.IN_PROCESS
