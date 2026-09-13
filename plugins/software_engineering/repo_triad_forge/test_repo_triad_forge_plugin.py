"""Contract test suite for Repo-Triad Forge Plugin."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure plugin directory is on sys.path
_PLUGIN_DIR = Path(__file__).parent
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.repo_triad_forge import (
    REPO_TRIAD_FORGE_SERVICE_KEY,
    RepoTriadForgeService,
)
from plugins.software_engineering.repo_triad_forge.main import (
    RepoTriadForgePlugin,
    plugin,
    triad_briefs,
    triad_inspect,
    triad_ki_candidates,
    triad_run,
)


@pytest.mark.unit
class TestRepoTriadForgePlugin:
    """Validate Repo-Triad Forge Plugin lifecycle, IoC registration, and service protocol."""

    def test_plugin_validator_compliance(self) -> None:
        """Verify plugin passes PluginValidator checks adhering to Rule 34 and Rule 38."""
        report = PluginValidator.validate_sync(_PLUGIN_DIR)
        assert report.valid is True, f"Plugin validation failed: {report.errors}"

    def test_plugin_metadata_and_singleton(self) -> None:
        """Verify plugin metadata, provides key, and singleton export per Rule 45."""
        assert plugin.name == "plugin.repo_triad_forge"
        assert plugin.version == "1.0.0"
        assert REPO_TRIAD_FORGE_SERVICE_KEY in plugin.provides
        assert isinstance(plugin, RepoTriadForgePlugin)
        assert isinstance(plugin, RepoTriadForgeService)

    @pytest.mark.asyncio
    async def test_ioc_context_provision_and_resolution(self) -> None:
        """Verify plugin registers into ServiceContext and resolves via REPO_TRIAD_FORGE_SERVICE_KEY."""
        ctx = ServiceContext()
        await plugin.on_load(ctx)

        resolved = ctx.require(REPO_TRIAD_FORGE_SERVICE_KEY)
        assert resolved is plugin

    def test_triad_inspect_tool(self) -> None:
        """Verify triad_inspect tool executes on current repository."""
        workspace_root = Path(__file__).resolve().parents[3]
        res = plugin.inspect(str(workspace_root))
        assert res.repo_name == "Brain Harness"
        assert "Python" in res.languages
        assert res.total_files > 0
        assert res.compute_tier in ("High", "Medium", "Low")

    def test_triad_briefs_tool(self, tmp_path: Path) -> None:
        """Verify triad_briefs tool generates HTML visual briefs."""
        workspace_root = Path(__file__).resolve().parents[3]
        briefs = plugin.generate_briefs(str(workspace_root), output_dir=str(tmp_path))
        assert len(briefs) == 5
        for b in briefs:
            assert Path(b.html_path).exists()
            assert b.slug in ("compute-assessor", "data-topology-review", "repo-reader", "deep-skill-forge", "repo-to-plugin-forge")

    def test_triad_ki_candidates_tool(self) -> None:
        """Verify triad_ki_candidates tool extracts candidate items."""
        workspace_root = Path(__file__).resolve().parents[3]
        kis = plugin.extract_kis(str(workspace_root))
        assert len(kis) >= 3
        for k in kis:
            assert k.id.startswith("ki_Brain Harness_")
            assert len(k.citations) >= 1
            assert k.confidence >= 0.85

    def test_triad_run_pipeline_tool(self, tmp_path: Path) -> None:
        """Verify end-to-end triad pipeline tool execution."""
        workspace_root = Path(__file__).resolve().parents[3]
        options = {
            "briefs_dir": str(tmp_path / "briefs"),
            "vault_dir": str(tmp_path / "vault"),
        }
        res = plugin.run_pipeline(str(workspace_root), options)
        assert res.success is True
        assert len(res.stages_completed) == 4
        assert len(res.artifacts_generated) == 5
        assert len(res.kis_committed) >= 3

    def test_top_level_entrypoint_functions(self, tmp_path: Path) -> None:
        """Verify top-level function wrappers declared in manifest function properly."""
        workspace_root = str(Path(__file__).resolve().parents[3])

        ins_res = triad_inspect(workspace_root)
        assert ins_res["repo_name"] == "Brain Harness"

        briefs_res = triad_briefs(workspace_root, output_dir=str(tmp_path))
        assert len(briefs_res) == 5

        kis_res = triad_ki_candidates(workspace_root)
        assert len(kis_res) >= 3

        run_res = triad_run(workspace_root, {"briefs_dir": str(tmp_path / "b"), "vault_dir": str(tmp_path / "v")})
        assert run_res["success"] is True
