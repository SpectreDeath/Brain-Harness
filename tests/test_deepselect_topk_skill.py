"""Contract test suite for deepselect-topk-optimizer skill adhering to Craft standards and Rule 43."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Ensure skill scripts directory is on sys.path
_SKILL_SCRIPTS = Path(__file__).parent.parent / ".agents" / "skills" / "deepselect-topk-optimizer" / "scripts"
if str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))

from deepselect_engine import (
    AnalyticalPerformanceBound,
    DeepSelectAlgorithmConfig,
    DeepSelectEngine,
    KernelDispatchPlan,
    TopkWorkloadSpec,
)


@pytest.mark.unit
class TestDeepSelectTopkOptimizer:
    """Validate DeepSelect domain engine, slotted/frozen immutability, and bound calculus."""

    def test_slotted_frozen_dataclasses_immutability(self) -> None:
        """Verify slotted/frozen dataclass immutability using direct assignment per Rule 43."""
        spec = TopkWorkloadSpec(
            batch_size=4,
            vocab_size=129280,
            topk=512,
            dtype="bfloat16",
        )
        config = DeepSelectAlgorithmConfig(
            block_size_b=1024,
            compact_threshold_b2=1024,
            cluster_size=1,
        )
        bounds = DeepSelectEngine.calculate_bounds(spec, config)
        plan = DeepSelectEngine.analyze_workload(spec)

        # Direct attribute assignment must raise AttributeError/TypeError (Rule 43)
        with pytest.raises((AttributeError, TypeError)):
            spec.topk = 1024  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            spec.batch_size = 8  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            config.block_size_b = 2048  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            bounds.harmonic_number_hm = 10.0  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            plan.recommended_variant = "mutated"  # type: ignore

    def test_workload_spec_validation(self) -> None:
        """Verify constructor validation rules for TopkWorkloadSpec."""
        # TopK exceeding 4096 must raise ValueError
        with pytest.raises(ValueError, match="topk must be between 1 and 4096"):
            TopkWorkloadSpec(batch_size=1, vocab_size=10000, topk=5000)

        # TopK exceeding vocab_size must raise ValueError
        with pytest.raises(ValueError, match="cannot exceed vocab_size"):
            TopkWorkloadSpec(batch_size=1, vocab_size=100, topk=200)

        # Invalid dtype must raise ValueError
        with pytest.raises(ValueError, match="dtype must be"):
            TopkWorkloadSpec(batch_size=1, vocab_size=1000, topk=50, dtype="int32")  # type: ignore

    def test_harmonic_number_calculation(self) -> None:
        """Verify harmonic number calculation accuracy across small and large m."""
        assert DeepSelectEngine.compute_harmonic_number(0) == 0.0
        assert abs(DeepSelectEngine.compute_harmonic_number(1) - 1.0) < 1e-6
        assert abs(DeepSelectEngine.compute_harmonic_number(2) - 1.5) < 1e-6
        assert abs(DeepSelectEngine.compute_harmonic_number(3) - (1.0 + 0.5 + 1/3)) < 1e-6

        # Large m asymptotic expansion
        h_1000 = DeepSelectEngine.compute_harmonic_number(1000)
        assert 7.48 < h_1000 < 7.50

    def test_analytical_bound_calculus(self) -> None:
        """Verify DeepSeek mathematical bounds E[W] <= (1 + k/B2) * L * H_m."""
        spec = TopkWorkloadSpec(
            batch_size=4,
            vocab_size=204800,
            topk=512,
            dtype="bfloat16",
        )
        config = DeepSelectAlgorithmConfig(
            block_size_b=1024,
            compact_threshold_b2=1024,
        )

        bounds = DeepSelectEngine.calculate_bounds(spec, config)
        assert bounds.harmonic_number_hm > 5.0
        assert bounds.candidate_rank_bound_l == 512 + 1024 + 1024
        assert bounds.expected_candidates_w > 0.0
        assert bounds.speedup_estimate_vs_torch >= 2.0
        assert bounds.theoretical_memory_reads_bytes == 4 * 204800 * 2

    def test_denormal_fp32_addition_equivalence(self) -> None:
        """Verify IEEE-754 denormal FP32 simulated addition bitwise identity."""
        test_pairs = [
            (0, 0),
            (1, 1),
            (42, 100),
            (1024, 4096),
            (65536, 131072),
            ((1 << 22) - 100, 50),
        ]
        for x, y in test_pairs:
            int_sum, fp_sum, matches = DeepSelectEngine.verify_denormal_addition(x, y)
            assert matches is True
            assert int_sum == fp_sum

        # Out of bound operand (> 2^22) must raise ValueError
        with pytest.raises(ValueError, match=r"Operands must be non-negative and <= 2\^22"):
            DeepSelectEngine.verify_denormal_addition((1 << 23), 10)

    def test_workload_analysis_and_dispatch_planning(self) -> None:
        """Verify dispatch planning across lightning indexer and sampling workloads."""
        # Scenario 1: Lightning Indexer with large vocab & small batch -> Cluster size 16
        spec_lightning = TopkWorkloadSpec(
            batch_size=2,
            vocab_size=129280,
            topk=512,
            dtype="bfloat16",
            scenario="lightning_indexer",
        )
        plan_lightning = DeepSelectEngine.analyze_workload(spec_lightning)
        assert plan_lightning.cluster_size == 16
        assert "v3_cluster" in plan_lightning.recommended_variant
        assert plan_lightning.input_stride_alignment == 1024
        assert plan_lightning.output_stride_alignment == 32

        # Scenario 2: Sampling with fp32
        spec_sampling = TopkWorkloadSpec(
            batch_size=16,
            vocab_size=65536,
            topk=256,
            dtype="float32",
            scenario="sampling",
        )
        plan_sampling = DeepSelectEngine.analyze_workload(spec_sampling)
        assert plan_sampling.cluster_size == 1
        assert "v3_fp32" in plan_sampling.recommended_variant

    def test_monotonic_simulation_parity(self) -> None:
        """Verify python simulation selects 100% correct top-k elements compared to ground truth."""
        # Generate synthetic row with distinct values
        row = [float(i * 3 % 1000) for i in range(2048)]
        topk = 32

        result = DeepSelectEngine.simulate_selection(row, topk, seed=123)
        assert result["status"] == "success"
        assert result["topk"] == topk
        assert result["match_parity"] is True
        assert len(result["selected_indices"]) == topk
        assert result["in_loop_compactions"] >= 1
