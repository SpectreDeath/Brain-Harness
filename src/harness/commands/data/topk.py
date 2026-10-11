"""DeepSelect TopK workload analysis, bounds estimation, and recommendation commands."""

from __future__ import annotations

from typing import Any


async def topk_analyze_cmd(
    batch_size: int,
    vocab_size: int,
    topk: int,
    dtype: str = "bfloat16",
    scenario: str = "lightning_indexer",
) -> dict[str, Any]:
    """Analyze TopK workload dimensions and determine kernel variant dispatch."""
    from plugins.data_engineering.deepselect_topk.service import DeepSelectTopkService

    service = DeepSelectTopkService()
    return service.analyze_workload(
        batch_size=batch_size,
        vocab_size=vocab_size,
        topk=topk,
        dtype=dtype,
        scenario=scenario,
    )


async def topk_bounds_cmd(
    batch_size: int,
    vocab_size: int,
    topk: int,
    block_size: int = 1024,
    compact_threshold: int = 1024,
    dtype: str = "bfloat16",
) -> dict[str, Any]:
    """Compute theoretical upper bounds on expected elements W and speedup."""
    from plugins.data_engineering.deepselect_topk.service import DeepSelectTopkService

    service = DeepSelectTopkService()
    return service.estimate_bounds(
        batch_size=batch_size,
        vocab_size=vocab_size,
        topk=topk,
        block_size=block_size,
        compact_threshold=compact_threshold,
        dtype=dtype,
    )


async def topk_recommend_cmd(
    batch_size: int,
    vocab_size: int,
    topk: int,
    dtype: str = "bfloat16",
) -> dict[str, Any]:
    """Recommend optimal block sizes and Threadblock Cluster size for workload."""
    from plugins.data_engineering.deepselect_topk.service import DeepSelectTopkService

    service = DeepSelectTopkService()
    return service.recommend_config(
        batch_size=batch_size,
        vocab_size=vocab_size,
        topk=topk,
        dtype=dtype,
    )
