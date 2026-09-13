"""DeepSelect TopK Selection Service Protocol and Typed ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from harness.kernel.context import ServiceKey


@runtime_checkable
class DeepSelectTopkProtocol(Protocol):
    """Protocol for DeepSelect TopK selection, bound analysis, and DSA routing."""

    def analyze_workload(
        self,
        batch_size: int,
        vocab_size: int,
        topk: int,
        dtype: str = "bfloat16",
        scenario: str = "lightning_indexer",
    ) -> dict[str, Any]:
        """Analyze workload feasibility and generate kernel dispatch plan."""
        ...

    def estimate_bounds(
        self,
        batch_size: int,
        vocab_size: int,
        topk: int,
        block_size: int = 1024,
        compact_threshold: int = 1024,
        dtype: str = "bfloat16",
    ) -> dict[str, Any]:
        """Estimate mathematical bounds on candidate volume and throughput speedup."""
        ...

    def recommend_config(
        self,
        batch_size: int,
        vocab_size: int,
        topk: int,
        dtype: str = "bfloat16",
    ) -> dict[str, Any]:
        """Recommend optimal block size B, threshold B2, and Threadblock Cluster size."""
        ...

    def simulate_selection(
        self,
        input_matrix: list[list[float]],
        topk: int,
        block_size: int = 1024,
        compact_threshold: int = 1024,
    ) -> dict[str, Any]:
        """Simulate randomized block scan and monotonic threshold filtering."""
        ...


DEEPSELECT_TOPK_SERVICE_KEY: ServiceKey[DeepSelectTopkProtocol] = ServiceKey("deepselect.topk.service")
