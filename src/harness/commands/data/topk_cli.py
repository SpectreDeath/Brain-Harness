"""DeepSelect TopK Click CLI commands and sub-group registration."""

from __future__ import annotations

import json
import click

from harness.commands._utils import _run_async
from harness.commands.data.topk import (
    topk_analyze_cmd,
    topk_bounds_cmd,
    topk_recommend_cmd,
)


@click.command("topk-analyze")
@click.option("--batch-size", default=4, type=int, help="Batch size")
@click.option("--vocab-size", default=129280, type=int, help="Vocab / sequence length")
@click.option("--topk", default=512, type=int, help="TopK value")
@click.option("--dtype", default="bfloat16", help="Data type (bfloat16 or float32)")
@click.option("--scenario", default="lightning_indexer", help="Scenario (lightning_indexer or sampling)")
@click.option("--json", "json_out", is_flag=True, help="Output JSON result")
def topk_analyze_cli(batch_size: int, vocab_size: int, topk: int, dtype: str, scenario: str, json_out: bool) -> None:
    """Analyze DeepSelect TopK workload feasibility and kernel variant dispatch."""
    res = _run_async(topk_analyze_cmd(batch_size=batch_size, vocab_size=vocab_size, topk=topk, dtype=dtype, scenario=scenario))
    if json_out:
        click.echo(json.dumps(res, indent=2))
        return
    click.echo("\n[DeepSelect TopK Workload Analysis]")
    click.echo(f"  Scenario: {res['scenario']} | Recommended: {res['recommended_variant']}")
    click.echo(f"  Cluster Size: {res['cluster_size']} | Stride Padding: {res['requires_stride_padding']}")
    click.echo(f"  Estimated Speedup: {res['estimated_speedup']}x vs torch.topk")


@click.command("topk-bounds")
@click.option("--batch-size", default=4, type=int, help="Batch size")
@click.option("--vocab-size", default=129280, type=int, help="Vocab / sequence length")
@click.option("--topk", default=512, type=int, help="TopK value")
@click.option("--block-size", default=1024, type=int, help="Block size B")
@click.option("--compact-threshold", default=1024, type=int, help="Compaction threshold B2")
@click.option("--dtype", default="bfloat16", help="Data type")
@click.option("--json", "json_out", is_flag=True, help="Output JSON result")
def topk_bounds_cli(batch_size: int, vocab_size: int, topk: int, block_size: int, compact_threshold: int, dtype: str, json_out: bool) -> None:
    """Compute mathematical bounds on TopK candidate volume and speedup."""
    res = _run_async(topk_bounds_cmd(batch_size=batch_size, vocab_size=vocab_size, topk=topk, block_size=block_size, compact_threshold=compact_threshold, dtype=dtype))
    if json_out:
        click.echo(json.dumps(res, indent=2))
        return
    click.echo("\n[DeepSelect Analytical Performance Bounds]")
    click.echo(f"  Harmonic Number H_m: {res['harmonic_number_hm']} | Rank Bound L: {res['candidate_rank_bound_l']}")
    click.echo(f"  Expected Candidates E[W]: {res['expected_candidates_w']} elements")
    click.echo(f"  Expected Speedup: {res['speedup_estimate_vs_torch']}x vs torch.topk")


@click.command("topk-recommend")
@click.option("--batch-size", default=4, type=int, help="Batch size")
@click.option("--vocab-size", default=129280, type=int, help="Vocab / sequence length")
@click.option("--topk", default=512, type=int, help="TopK value")
@click.option("--dtype", default="bfloat16", help="Data type")
@click.option("--json", "json_out", is_flag=True, help="Output JSON result")
def topk_recommend_cli(batch_size: int, vocab_size: int, topk: int, dtype: str, json_out: bool) -> None:
    """Recommend optimal DeepSelect kernel configurations."""
    res = _run_async(topk_recommend_cmd(batch_size=batch_size, vocab_size=vocab_size, topk=topk, dtype=dtype))
    if json_out:
        click.echo(json.dumps(res, indent=2))
        return
    click.echo("\n[DeepSelect Kernel Recommendation]")
    click.echo(f"  Block Size B: {res['block_size_b']} | Compaction Threshold B2: {res['compact_threshold_b2']}")
    click.echo(f"  Cluster Size: {res['cluster_size']} | Threads: {res['num_threads']}")


def register_topk_commands(group: click.Group) -> None:
    """Register DeepSelect TopK subcommands onto the data CLI group."""
    group.add_command(topk_analyze_cli)
    group.add_command(topk_bounds_cli)
    group.add_command(topk_recommend_cli)
