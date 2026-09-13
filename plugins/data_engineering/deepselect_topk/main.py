"""DeepSelect TopK Selection Plugin for Brain Harness."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Ensure Harness core src is on sys.path
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.deepselect_topk import (
    DEEPSELECT_TOPK_SERVICE_KEY,
    DeepSelectTopkProtocol,
)
from plugins.data_engineering.deepselect_topk.service import DeepSelectTopkService

_SERVICE_INSTANCE = DeepSelectTopkService()


# Top-level entrypoints matching plugin.json
def deepselect_analyze_workload(
    batch_size: int,
    vocab_size: int,
    topk: int,
    dtype: str = "bfloat16",
    scenario: str = "lightning_indexer",
) -> dict[str, Any]:
    """Analyze TopK workload dimensions and determine kernel variant dispatch."""
    return _SERVICE_INSTANCE.analyze_workload(
        batch_size=batch_size,
        vocab_size=vocab_size,
        topk=topk,
        dtype=dtype,
        scenario=scenario,
    )


def deepselect_estimate_bounds(
    batch_size: int,
    vocab_size: int,
    topk: int,
    block_size: int = 1024,
    compact_threshold: int = 1024,
    dtype: str = "bfloat16",
) -> dict[str, Any]:
    """Compute theoretical upper bounds on candidate elements and speedup."""
    return _SERVICE_INSTANCE.estimate_bounds(
        batch_size=batch_size,
        vocab_size=vocab_size,
        topk=topk,
        block_size=block_size,
        compact_threshold=compact_threshold,
        dtype=dtype,
    )


def deepselect_recommend_config(
    batch_size: int,
    vocab_size: int,
    topk: int,
    dtype: str = "bfloat16",
) -> dict[str, Any]:
    """Recommend optimal block sizes and Threadblock Cluster size for workload."""
    return _SERVICE_INSTANCE.recommend_config(
        batch_size=batch_size,
        vocab_size=vocab_size,
        topk=topk,
        dtype=dtype,
    )


def deepselect_simulate_selection(
    input_matrix: list[list[float]],
    topk: int,
    block_size: int = 1024,
    compact_threshold: int = 1024,
) -> dict[str, Any]:
    """Simulate randomized block scanning and monotonic threshold compaction."""
    return _SERVICE_INSTANCE.simulate_selection(
        input_matrix=input_matrix,
        topk=topk,
        block_size=block_size,
        compact_threshold=compact_threshold,
    )


class DeepSelectTopkPlugin(HarnessPlugin):
    """Brain Harness Plugin bridging DeepSelect TopK kernel architecture & DSA routing."""

    @property
    def name(self) -> str:
        return "plugin.deepselect_topk"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "DeepSelect High-Performance TopK Selection & DSA Routing Plugin "
            "with Monotonic Threshold Compaction and Hardware Contention Mitigation"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [DEEPSELECT_TOPK_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(DEEPSELECT_TOPK_SERVICE_KEY, _SERVICE_INSTANCE)

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()


# Module singleton export per Rule 45
plugin = DeepSelectTopkPlugin()
