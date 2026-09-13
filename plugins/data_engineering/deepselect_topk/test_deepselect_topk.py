"""Contract test suite for deepselect_topk plugin validating IoC, lifecycle, and PluginValidator."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.deepselect_topk import DEEPSELECT_TOPK_SERVICE_KEY
from plugins.data_engineering.deepselect_topk.main import (
    DeepSelectTopkPlugin,
    deepselect_analyze_workload,
    deepselect_estimate_bounds,
    deepselect_recommend_config,
    deepselect_simulate_selection,
    plugin,
)


@pytest.mark.unit
class TestDeepSelectTopkPlugin:
    """Verify plugin manifest, entrypoints, IoC lifecycle, and PluginValidator compliance."""

    def test_plugin_validator_compliance(self) -> None:
        """Validate plugin structure, manifest, and signatures using PluginValidator (Rule 34, 38)."""
        plugin_dir = Path(__file__).parent
        report = PluginValidator.validate_sync(plugin_dir)

        # In accordance with Rule 34, evaluate overall boolean status via report.valid
        assert report.valid is True, f"Plugin validation failed with errors: {report.errors}"
        assert len(report.checks) >= 4
        assert all(check.passed for check in report.checks if check.severity == "error")

    @pytest.mark.asyncio
    async def test_plugin_ioc_registration_and_lifecycle(self) -> None:
        """Verify plugin registers DEEPSELECT_TOPK_SERVICE_KEY into IoC container (Rule 2, 45)."""
        ctx = ServiceContext()
        p = DeepSelectTopkPlugin()

        assert p.name == "plugin.deepselect_topk"
        assert DEEPSELECT_TOPK_SERVICE_KEY in p.provides
        assert plugin is not None  # Module singleton invariant (Rule 45)

        await p.enable(ctx)

        # Service must be resolvable via typed ServiceKey (Rule 2)
        service = ctx.require(DEEPSELECT_TOPK_SERVICE_KEY)
        assert service is not None

        # Test workload analysis
        plan = service.analyze_workload(batch_size=4, vocab_size=129280, topk=512)
        assert plan["scenario"] == "lightning_indexer"
        assert plan["cluster_size"] == 16
        assert plan["input_stride_alignment"] == 1024

        # Test bounds estimation
        bounds = service.estimate_bounds(batch_size=4, vocab_size=129280, topk=512)
        assert bounds["harmonic_number_hm"] > 5.0
        assert bounds["expected_candidates_w"] > 0

        # Test recommendation
        rec = service.recommend_config(batch_size=1, vocab_size=65536, topk=256)
        assert rec["block_size_b"] == 1024
        assert rec["cluster_size"] == 16

        # Test simulation
        sim = service.simulate_selection([[10.0, 50.0, 20.0, 80.0, 30.0]], topk=2, block_size=64, compact_threshold=64)
        assert sim["status"] == "ok"
        assert sim["rows_count"] == 1
        assert sim["results"][0]["selected_values"] == [80.0, 50.0]

        await p.disable(ctx)

    def test_top_level_entrypoints_execution(self) -> None:
        """Verify module top-level functions execute cleanly."""
        analysis = deepselect_analyze_workload(batch_size=8, vocab_size=32768, topk=256)
        assert "recommended_variant" in analysis

        bounds = deepselect_estimate_bounds(batch_size=8, vocab_size=32768, topk=256)
        assert "expected_candidates_w" in bounds

        rec = deepselect_recommend_config(batch_size=8, vocab_size=32768, topk=256)
        assert "block_size_b" in rec

        sim = deepselect_simulate_selection([[1.0, 4.0, 2.0, 3.0]], topk=2, block_size=64, compact_threshold=64)
        assert sim["results"][0]["selected_values"] == [4.0, 3.0]
