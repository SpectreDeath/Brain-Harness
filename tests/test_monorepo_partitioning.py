"""Tests for monorepo detection and domain-partitioned plugin synthesis (Rule 18)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.ingestion.converter import RepoConverter
from harness.ingestion.inspector import RepoInspector
from harness.ingestion.monorepo import (
    detect_monorepo_subprojects,
    partition_monorepo,
)
from harness.ingestion.pipeline import PluginIngestionPipeline
from harness.plugins.sandboxed import SandboxedPlugin


@pytest.mark.unit
class TestMonorepoPartitioning:
    def test_single_repo_detection_returns_empty(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'single_pkg'\nversion = '0.1.0'\n", encoding="utf-8")
        (tmp_path / "main.py").write_text("def run(): pass\n", encoding="utf-8")

        subprojects = detect_monorepo_subprojects(tmp_path)
        assert subprojects == []

    def test_conventional_packages_detection(self, tmp_path: Path) -> None:
        pkg_dir = tmp_path / "packages"
        pkg_dir.mkdir()

        # Subproject 1: auth
        auth_dir = pkg_dir / "auth"
        auth_dir.mkdir()
        (auth_dir / "plugin.json").write_text(json.dumps({"name": "auth", "version": "1.0.0"}), encoding="utf-8")
        (auth_dir / "main.py").write_text("def login(): pass\n", encoding="utf-8")

        # Subproject 2: billing
        billing_dir = pkg_dir / "billing"
        billing_dir.mkdir()
        (billing_dir / "plugin.json").write_text(json.dumps({"name": "billing", "version": "1.0.0"}), encoding="utf-8")
        (billing_dir / "main.py").write_text("def invoice(): pass\n", encoding="utf-8")

        subprojects = detect_monorepo_subprojects(tmp_path)
        assert len(subprojects) == 2
        sub_names = {p.name for p in subprojects}
        assert sub_names == {"auth", "billing"}

    def test_partition_monorepo_synthesizes_isolated_plugins(self, tmp_path: Path) -> None:
        # Create root monorepo
        repo_dir = tmp_path / "enterprise_platform"
        repo_dir.mkdir()

        services = repo_dir / "services"
        services.mkdir()

        s1 = services / "analytics"
        s1.mkdir()
        (s1 / "plugin.json").write_text(
            json.dumps({"name": "analytics", "version": "0.1.0", "entrypoints": [{"name": "track"}]}),
            encoding="utf-8",
        )
        (s1 / "main.py").write_text("def track(): pass\n", encoding="utf-8")

        s2 = services / "notifications"
        s2.mkdir()
        (s2 / "plugin.json").write_text(
            json.dumps({"name": "notifications", "version": "0.1.0", "entrypoints": [{"name": "send"}]}),
            encoding="utf-8",
        )
        (s2 / "main.py").write_text("def send(): pass\n", encoding="utf-8")

        inspector = RepoInspector()
        converter = RepoConverter()
        plugins = partition_monorepo(repo_dir, inspector=inspector, converter=converter)

        assert len(plugins) == 2
        for p in plugins:
            assert isinstance(p, SandboxedPlugin)

        plugin_names = {p.name for p in plugins}
        assert "enterprise_platform.analytics" in plugin_names
        assert "enterprise_platform.notifications" in plugin_names

    @pytest.mark.asyncio
    async def test_pipeline_ingest_monorepo(self, tmp_path: Path) -> None:
        repo_dir = tmp_path / "multi_tool"
        repo_dir.mkdir()

        packages = repo_dir / "packages"
        packages.mkdir()

        for tool in ("tool_a", "tool_b"):
            td = packages / tool
            td.mkdir()
            (td / "plugin.json").write_text(
                json.dumps({"name": tool, "version": "1.0.0", "entrypoints": [{"name": "run"}]}),
                encoding="utf-8",
            )
            (td / "main.py").write_text("def run(): pass\n", encoding="utf-8")

        pipeline = PluginIngestionPipeline(plugin_dir=tmp_path / "cache")
        partitioned = await pipeline.ingest_monorepo(repo_dir)

        assert len(partitioned) == 2
        names = {p.name for p in partitioned}
        assert "multi_tool.tool_a" in names
        assert "multi_tool.tool_b" in names
