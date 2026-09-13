"""DeepSelect TopK Optimizer Domain Engine.

Provides slotted/frozen dataclass entities, mathematical complexity bound calculus,
hardware ALU contention analysis (denormal FP32 simulation), kernel dispatch planning,
and monotonic threshold filtering simulation for DeepSeek Sparse Attention (DSA).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
import struct
from typing import Any


@dataclass(slots=True, frozen=True)
class TopkWorkloadSpec:
    """Immutable specification of a TopK execution workload."""

    batch_size: int
    vocab_size: int
    topk: int
    dtype: str = "bfloat16"
    sorted_index: bool = False
    return_value: bool = True
    scenario: str = "lightning_indexer"

    def __post_init__(self) -> None:
        if self.batch_size < 1:
            raise ValueError(f"batch_size must be >= 1, got {self.batch_size}")
        if self.vocab_size < 1:
            raise ValueError(f"vocab_size must be >= 1, got {self.vocab_size}")
        if not (1 <= self.topk <= 4096):
            raise ValueError(f"topk must be between 1 and 4096, got {self.topk}")
        if self.topk > self.vocab_size:
            raise ValueError(f"topk ({self.topk}) cannot exceed vocab_size ({self.vocab_size})")
        if self.dtype not in ("bfloat16", "float32"):
            raise ValueError(f"dtype must be 'bfloat16' or 'float32', got {self.dtype}")
        if self.scenario not in ("lightning_indexer", "sampling"):
            raise ValueError(f"scenario must be 'lightning_indexer' or 'sampling', got {self.scenario}")


@dataclass(slots=True, frozen=True)
class DeepSelectAlgorithmConfig:
    """Immutable algorithmic and hardware kernel configuration."""

    block_size_b: int = 1024
    compact_threshold_b2: int = 1024
    max_topk: int = 4096
    num_threads: int = 512
    cluster_size: int = 1
    tma_buffer_depth: int = 3
    use_denormal_addition: bool = True

    def __post_init__(self) -> None:
        if self.block_size_b < 64:
            raise ValueError(f"block_size_b must be >= 64, got {self.block_size_b}")
        if self.compact_threshold_b2 < 64:
            raise ValueError(f"compact_threshold_b2 must be >= 64, got {self.compact_threshold_b2}")
        if self.cluster_size not in (1, 2, 4, 8, 16):
            raise ValueError(f"cluster_size must be 1, 2, 4, 8, or 16, got {self.cluster_size}")


@dataclass(slots=True, frozen=True)
class AnalyticalPerformanceBound:
    """Immutable theoretical performance bound metrics."""

    harmonic_number_hm: float
    candidate_rank_bound_l: int
    expected_candidates_w: float
    expected_in_loop_compactions: float
    theoretical_memory_reads_bytes: int
    speedup_estimate_vs_torch: float
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(slots=True, frozen=True)
class KernelDispatchPlan:
    """Immutable hardware dispatch plan for a given workload."""

    scenario: str
    recommended_variant: str
    cluster_size: int
    input_stride_alignment: int
    output_stride_alignment: int
    requires_stride_padding: bool
    estimated_speedup: float
    reasoning: tuple[str, ...] = field(default_factory=tuple)


class DeepSelectEngine:
    """Domain engine for DeepSelect TopK algorithms and mathematical models."""

    @staticmethod
    def compute_harmonic_number(m: int) -> float:
        """Compute the m-th harmonic number H_m = sum_{i=1}^m 1/i with high precision."""
        if m <= 0:
            return 0.0
        if m < 500:
            return sum(1.0 / i for i in range(1, m + 1))
        # Euler-Mascheroni asymptotic expansion: ln(m) + gamma + 1/(2m) - 1/(12m^2)
        euler_gamma = 0.5772156649015329
        return math.log(m) + euler_gamma + (0.5 / m) - (1.0 / (12.0 * m * m))

    @classmethod
    def calculate_bounds(
        cls,
        spec: TopkWorkloadSpec,
        config: DeepSelectAlgorithmConfig,
    ) -> AnalyticalPerformanceBound:
        """Calculate theoretical upper bounds on expected elements processed per DeepSeek paper."""
        b = config.block_size_b
        b2 = config.compact_threshold_b2
        k = spec.topk
        n = spec.vocab_size

        m = math.ceil(n / b)
        h_m = cls.compute_harmonic_number(m)
        l_bound = k + b + b2

        # DeepSeek bound: E[W] <= (1 + k/B2) * L * H_m
        factor = 1.0 + (k / b2)
        expected_w = factor * l_bound * h_m

        # Expected in-loop TopK calls: E[R] <= E[A] / B2 <= (L * H_m) / B2
        expected_r = (l_bound * h_m) / b2

        # Bytes read per row: bytes_per_elem * N
        bytes_per_elem = 2 if spec.dtype == "bfloat16" else 4
        reads_bytes = spec.batch_size * n * bytes_per_elem

        # Empirical speedup model vs torch.topk
        # torch.topk processes O(N log k) comparisons across global memory.
        # DeepSelect processes O(k log(N/k)) in shared memory + 1 sequential read.
        ratio_work = (n * math.log2(max(k, 2))) / max(expected_w, 1.0)
        speedup = max(1.8, min(round(ratio_work * 0.15, 1), 22.5))
        if not spec.return_value:
            speedup = round(speedup * 1.10, 1)

        notes = (
            f"Harmonic blocks m={m}, rank bound L={l_bound}",
            f"Compaction complexity bounded to O(k log(N/k)) = {round(expected_w, 1)} elements",
            f"Memory read bandwidth decoupled from sorting comparisons",
        )

        return AnalyticalPerformanceBound(
            harmonic_number_hm=round(h_m, 4),
            candidate_rank_bound_l=l_bound,
            expected_candidates_w=round(expected_w, 2),
            expected_in_loop_compactions=round(expected_r, 2),
            theoretical_memory_reads_bytes=reads_bytes,
            speedup_estimate_vs_torch=speedup,
            notes=notes,
        )

    @classmethod
    def recommend_config(cls, spec: TopkWorkloadSpec) -> DeepSelectAlgorithmConfig:
        """Recommend optimal block size B, threshold B2, and cluster size based on workload."""
        k = spec.topk

        # For small k <= 512, B=1024, B2=1024 is optimal
        if k <= 512:
            b, b2 = 1024, 1024
            threads = 256
        elif k <= 2048:
            b, b2 = 2048, 2048
            threads = 512
        else:
            b, b2 = 4096, 4096
            threads = 512

        # Cluster configuration for wave quantization
        # Small batch (< 16) with large vocab (> 64k) benefits from cluster partitioning
        if spec.batch_size <= 4 and spec.vocab_size >= 65536:
            cluster_size = 16
        elif spec.batch_size <= 8 and spec.vocab_size >= 32768:
            cluster_size = 4
        else:
            cluster_size = 1

        return DeepSelectAlgorithmConfig(
            block_size_b=b,
            compact_threshold_b2=b2,
            max_topk=4096,
            num_threads=threads,
            cluster_size=cluster_size,
            tma_buffer_depth=3 if spec.dtype == "float32" else 5,
            use_denormal_addition=True,
        )

    @classmethod
    def analyze_workload(cls, spec: TopkWorkloadSpec) -> KernelDispatchPlan:
        """Analyze workload feasibility, stride requirements, and kernel variant dispatch."""
        config = cls.recommend_config(spec)
        bounds = cls.calculate_bounds(spec, config)

        bytes_per_elem = 2 if spec.dtype == "bfloat16" else 4
        row_bytes = spec.vocab_size * bytes_per_elem
        requires_padding = (row_bytes % 1024) != 0

        # Variant naming convention from DeepSelect csrc
        prefix = "v3_cluster" if config.cluster_size > 1 else ("v3_fp32" if spec.dtype == "float32" else "v3")
        variant_name = (
            f"{prefix}_val_{spec.dtype[:4]}_k{spec.topk}_b{config.block_size_b}"
            f"_c{config.cluster_size}_th{config.num_threads}"
        )

        reasoning = (
            f"Scenario: {spec.scenario} ({spec.dtype})",
            f"Input row size {row_bytes} bytes (stride % 1024 == {row_bytes % 1024})",
            f"Padding {'REQUIRED' if requires_padding else 'SATISFIED'} for 1024-byte alignment",
            f"Selected cluster size {config.cluster_size} (Wave-quantization mitigation)",
        )

        return KernelDispatchPlan(
            scenario=spec.scenario,
            recommended_variant=variant_name,
            cluster_size=config.cluster_size,
            input_stride_alignment=1024,
            output_stride_alignment=32,
            requires_stride_padding=requires_padding,
            estimated_speedup=bounds.speedup_estimate_vs_torch,
            reasoning=reasoning,
        )

    @staticmethod
    def verify_denormal_addition(x: int, y: int) -> tuple[int, int, bool]:
        """Verify the bitwise equivalence of IEEE-754 denormal FP32 addition for integers <= 2^22."""
        if not (0 <= x <= (1 << 22)) or not (0 <= y <= (1 << 22)):
            raise ValueError(f"Operands must be non-negative and <= 2^22 ({1 << 22})")

        int_sum = x + y

        # Emulate __uint_as_float and __float_as_uint via Python struct
        # Packing uint32 as float32, adding, unpacking as uint32
        x_bytes = struct.pack("<I", x)
        y_bytes = struct.pack("<I", y)
        x_float = struct.unpack("<f", x_bytes)[0]
        y_float = struct.unpack("<f", y_bytes)[0]

        float_sum = x_float + y_float
        float_sum_bytes = struct.pack("<f", float_sum)
        simulated_int_sum = struct.unpack("<I", float_sum_bytes)[0]

        matches = int_sum == simulated_int_sum
        return int_sum, simulated_int_sum, matches

    @staticmethod
    def simulate_selection(
        input_row: list[float],
        topk: int,
        config: DeepSelectAlgorithmConfig | None = None,
        seed: int = 42,
    ) -> dict[str, Any]:
        """Simulate DeepSelect randomized block scan and monotonic threshold filtering."""
        n = len(input_row)
        if topk > n or topk < 1:
            raise ValueError(f"Invalid topk {topk} for input length {n}")

        cfg = config or DeepSelectAlgorithmConfig()
        b = cfg.block_size_b
        b2 = cfg.compact_threshold_b2

        num_blocks = math.ceil(n / b)
        # Uniform random block permutation independent of input data
        rng = random.Random(seed)
        block_order = list(range(num_blocks))
        rng.shuffle(block_order)

        candidates: list[tuple[float, int]] = []
        threshold = float("-inf")
        in_loop_compactions = 0
        total_filtered_in = 0

        for block_idx in block_order:
            lo = block_idx * b
            hi = min(lo + b, n)

            # Filter step: only accept elements > current threshold
            for j in range(lo, hi):
                val = input_row[j]
                if val > threshold:
                    candidates.append((val, j))
                    total_filtered_in += 1

            # Compaction step: when candidates >= k + B2, compact back to top-k
            if len(candidates) >= topk + b2:
                candidates.sort(key=lambda item: item[0], reverse=True)
                candidates = candidates[:topk]
                threshold = candidates[-1][0]
                in_loop_compactions += 1

        # Final reduction
        candidates.sort(key=lambda item: item[0], reverse=True)
        final_candidates = candidates[:topk]

        selected_values = [v for v, _ in final_candidates]
        selected_indices = [idx for _, idx in final_candidates]

        # Ground truth check
        ground_truth = sorted([(val, i) for i, val in enumerate(input_row)], key=lambda x: x[0], reverse=True)[:topk]
        gt_indices = set(i for _, i in ground_truth)
        sim_indices = set(selected_indices)

        match_parity = gt_indices == sim_indices

        return {
            "status": "success",
            "topk": topk,
            "vocab_size": n,
            "final_threshold": threshold,
            "total_candidates_admitted": total_filtered_in,
            "in_loop_compactions": in_loop_compactions,
            "selected_values": selected_values,
            "selected_indices": selected_indices,
            "match_parity": match_parity,
        }
