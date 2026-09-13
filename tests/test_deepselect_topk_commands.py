"""Tests for DeepSelect TopK CLI commands and pure async entrypoints."""

from __future__ import annotations

import json
from click.testing import CliRunner
import pytest

from harness.cli import main
from harness.commands import (
    topk_analyze_cmd,
    topk_bounds_cmd,
    topk_recommend_cmd,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_topk_async_command_handlers() -> None:
    """Verify pure async command functions execute cleanly and return expected schemas."""
    # 1. Analyze command
    analysis = await topk_analyze_cmd(
        batch_size=2,
        vocab_size=129280,
        topk=512,
        dtype="bfloat16",
        scenario="lightning_indexer",
    )
    assert analysis["scenario"] == "lightning_indexer"
    assert analysis["cluster_size"] == 16
    assert analysis["requires_stride_padding"] is True
    assert "v3_cluster" in analysis["recommended_variant"]

    # 2. Bounds command
    bounds = await topk_bounds_cmd(
        batch_size=4,
        vocab_size=129280,
        topk=512,
        block_size=1024,
        compact_threshold=1024,
    )
    assert bounds["harmonic_number_hm"] > 5.0
    assert bounds["candidate_rank_bound_l"] == 2560
    assert bounds["expected_candidates_w"] > 0
    assert bounds["speedup_estimate_vs_torch"] >= 2.0

    # 3. Recommend command
    rec = await topk_recommend_cmd(
        batch_size=1,
        vocab_size=65536,
        topk=256,
        dtype="bfloat16",
    )
    assert rec["block_size_b"] == 1024
    assert rec["cluster_size"] == 16


@pytest.mark.unit
def test_topk_click_cli_commands() -> None:
    """Verify Click CLI commands under 'data' execute cleanly via CliRunner."""
    runner = CliRunner()

    # 1. data topk-analyze
    res_analyze = runner.invoke(main, ["data", "topk-analyze", "--batch-size", "4", "--vocab-size", "129280", "--topk", "512"])
    assert res_analyze.exit_code == 0
    assert "DeepSelect TopK Workload Analysis" in res_analyze.output
    assert "lightning_indexer" in res_analyze.output

    # JSON output
    res_analyze_json = runner.invoke(main, ["data", "topk-analyze", "--json"])
    assert res_analyze_json.exit_code == 0
    data = json.loads(res_analyze_json.output)
    assert "recommended_variant" in data

    # 2. data topk-bounds
    res_bounds = runner.invoke(main, ["data", "topk-bounds", "--batch-size", "4", "--vocab-size", "129280", "--topk", "512"])
    assert res_bounds.exit_code == 0
    assert "DeepSelect Analytical Performance Bounds" in res_bounds.output
    assert "Harmonic Number" in res_bounds.output

    # 3. data topk-recommend
    res_rec = runner.invoke(main, ["data", "topk-recommend", "--batch-size", "2", "--vocab-size", "65536", "--topk", "256"])
    assert res_rec.exit_code == 0
    assert "DeepSelect Kernel Recommendation" in res_rec.output
    assert "Block Size B" in res_rec.output
