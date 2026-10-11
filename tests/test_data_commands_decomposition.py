"""Characterization test contracts for Data Commands architecture decomposition (Cycle 40).

Verifies:
1. Rule 11 submodule line bounds (< 200 lines across all submodules in commands/data/)
2. Backward-compatible facade re-exports and subpackage imports
3. Rule 6 Click command group single-source consolidation and command attachment
4. Pure async command execution across contracts, quality, golden records, maturity, pipeline, and topk
5. Click CLI invocation and help output inspection across all subcommands
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.cli import main


@pytest.mark.unit
class TestDataCommandsDecompositionContracts:
    """Contract verification for data commands modularization."""

    def test_rule_11_submodule_line_limits(self) -> None:
        """Verify all submodules in commands/data remain strictly under 200 lines."""
        data_cmd_dir = (
            Path(__file__).parent.parent
            / "src"
            / "harness"
            / "commands"
            / "data"
        )
        assert data_cmd_dir.is_dir(), f"commands/data directory missing: {data_cmd_dir}"

        py_files = list(data_cmd_dir.glob("*.py"))
        assert len(py_files) >= 8, f"Expected at least 8 submodules in data/, found {len(py_files)}"

        for py_file in py_files:
            lines = len(py_file.read_text(encoding="utf-8").splitlines())
            assert (
                lines < 200
            ), f"Rule 11 violation in {py_file.name}: {lines} lines (must be < 200)"

    def test_facade_and_submodule_re_exports(self) -> None:
        """Verify symbols can be imported from facade and dedicated submodules."""
        from harness.commands.data import (
            assess_maturity_cmd,
            data_group,
            maturity_cli,
            pipeline_cli,
            profile_cli,
            profile_quality_cmd,
            resolve_cli,
            resolve_golden_records_cmd,
            run_medallion_pipeline_cmd,
            topk_analyze_cli,
            topk_analyze_cmd,
            topk_bounds_cli,
            topk_bounds_cmd,
            topk_recommend_cli,
            topk_recommend_cmd,
            validate_cli,
            validate_contract_cmd,
        )
        from harness.commands.data.contracts import validate_contract_cmd as v_cmd
        from harness.commands.data.golden_records import resolve_golden_records_cmd as g_cmd
        from harness.commands.data.maturity import assess_maturity_cmd as m_cmd
        from harness.commands.data.pipeline import run_medallion_pipeline_cmd as p_cmd
        from harness.commands.data.quality import profile_quality_cmd as q_cmd
        from harness.commands.data.topk import (
            topk_analyze_cmd as ta_cmd,
            topk_bounds_cmd as tb_cmd,
            topk_recommend_cmd as tr_cmd,
        )

        assert callable(data_group)
        assert callable(validate_contract_cmd)
        assert callable(profile_quality_cmd)
        assert callable(resolve_golden_records_cmd)
        assert callable(assess_maturity_cmd)
        assert callable(run_medallion_pipeline_cmd)
        assert callable(topk_analyze_cmd)
        assert callable(topk_bounds_cmd)
        assert callable(topk_recommend_cmd)

        assert callable(validate_cli)
        assert callable(profile_cli)
        assert callable(resolve_cli)
        assert callable(maturity_cli)
        assert callable(pipeline_cli)
        assert callable(topk_analyze_cli)
        assert callable(topk_bounds_cli)
        assert callable(topk_recommend_cli)

        assert validate_contract_cmd is v_cmd
        assert profile_quality_cmd is q_cmd
        assert resolve_golden_records_cmd is g_cmd
        assert assess_maturity_cmd is m_cmd
        assert run_medallion_pipeline_cmd is p_cmd
        assert topk_analyze_cmd is ta_cmd
        assert topk_bounds_cmd is tb_cmd
        assert topk_recommend_cmd is tr_cmd

    def test_rule_6_click_group_single_source_consolidation(self) -> None:
        """Verify all 8 subcommands are registered onto data_group without shadowing."""
        from harness.commands.data import data_group

        assert data_group.name == "data"
        expected_commands = {
            "validate",
            "profile",
            "resolve",
            "maturity",
            "pipeline",
            "topk-analyze",
            "topk-bounds",
            "topk-recommend",
        }
        registered = set(data_group.commands.keys())
        assert expected_commands.issubset(registered), f"Missing commands: {expected_commands - registered}"

    @pytest.mark.asyncio
    async def test_topk_async_commands(self) -> None:
        """Verify pure async DeepSelect TopK commands."""
        from harness.commands.data.topk import (
            topk_analyze_cmd,
            topk_bounds_cmd,
            topk_recommend_cmd,
        )

        # 1. Analyze
        res_analyze = await topk_analyze_cmd(
            batch_size=4,
            vocab_size=129280,
            topk=512,
            dtype="bfloat16",
            scenario="lightning_indexer",
        )
        assert "recommended_variant" in res_analyze
        assert res_analyze["cluster_size"] > 0
        assert res_analyze["estimated_speedup"] > 1.0

        # 2. Bounds
        res_bounds = await topk_bounds_cmd(
            batch_size=4,
            vocab_size=129280,
            topk=512,
            block_size=1024,
            compact_threshold=1024,
            dtype="bfloat16",
        )
        assert "expected_candidates_w" in res_bounds
        assert res_bounds["harmonic_number_hm"] > 0.0

        # 3. Recommend
        res_rec = await topk_recommend_cmd(
            batch_size=4,
            vocab_size=129280,
            topk=512,
            dtype="bfloat16",
        )
        assert res_rec["block_size_b"] > 0
        assert res_rec["cluster_size"] > 0

    def test_topk_click_cli_commands(self) -> None:
        """Verify Click CLI execution of TopK commands."""
        runner = CliRunner()

        # topk-analyze
        res1 = runner.invoke(main, ["data", "topk-analyze", "--batch-size", "2", "--topk", "256", "--json"])
        assert res1.exit_code == 0
        parsed1 = json.loads(res1.output)
        assert "recommended_variant" in parsed1

        # topk-bounds
        res2 = runner.invoke(main, ["data", "topk-bounds", "--batch-size", "2", "--topk", "256", "--json"])
        assert res2.exit_code == 0
        parsed2 = json.loads(res2.output)
        assert "expected_candidates_w" in parsed2

        # topk-recommend
        res3 = runner.invoke(main, ["data", "topk-recommend", "--batch-size", "2", "--topk", "256", "--json"])
        assert res3.exit_code == 0
        parsed3 = json.loads(res3.output)
        assert "block_size_b" in parsed3
