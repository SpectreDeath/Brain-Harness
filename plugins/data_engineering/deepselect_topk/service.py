"""Implementation of DeepSelectTopkService adhering to Rule 14 pipe drainage."""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Any

# Ensure skill scripts directory is on sys.path
_SKILL_SCRIPTS = Path(__file__).resolve().parents[3] / ".agents" / "skills" / "deepselect-topk-optimizer" / "scripts"
if _SKILL_SCRIPTS.exists() and str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))

from deepselect_engine import (
    DeepSelectAlgorithmConfig,
    DeepSelectEngine,
    TopkWorkloadSpec,
)


class DeepSelectTopkService:
    """Service providing DeepSelect TopK kernel planning, bounds estimation, and simulation."""

    def analyze_workload(
        self,
        batch_size: int,
        vocab_size: int,
        topk: int,
        dtype: str = "bfloat16",
        scenario: str = "lightning_indexer",
    ) -> dict[str, Any]:
        """Analyze workload feasibility and generate kernel dispatch plan."""
        spec = TopkWorkloadSpec(
            batch_size=batch_size,
            vocab_size=vocab_size,
            topk=topk,
            dtype=dtype,
            scenario=scenario,
        )
        plan = DeepSelectEngine.analyze_workload(spec)
        return {
            "scenario": plan.scenario,
            "recommended_variant": plan.recommended_variant,
            "cluster_size": plan.cluster_size,
            "input_stride_alignment": plan.input_stride_alignment,
            "output_stride_alignment": plan.output_stride_alignment,
            "requires_stride_padding": plan.requires_stride_padding,
            "estimated_speedup": plan.estimated_speedup,
            "reasoning": list(plan.reasoning),
        }

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
        spec = TopkWorkloadSpec(
            batch_size=batch_size,
            vocab_size=vocab_size,
            topk=topk,
            dtype=dtype,
        )
        config = DeepSelectAlgorithmConfig(
            block_size_b=block_size,
            compact_threshold_b2=compact_threshold,
        )
        bounds = DeepSelectEngine.calculate_bounds(spec, config)
        return {
            "harmonic_number_hm": bounds.harmonic_number_hm,
            "candidate_rank_bound_l": bounds.candidate_rank_bound_l,
            "expected_candidates_w": bounds.expected_candidates_w,
            "expected_in_loop_compactions": bounds.expected_in_loop_compactions,
            "theoretical_memory_reads_bytes": bounds.theoretical_memory_reads_bytes,
            "speedup_estimate_vs_torch": bounds.speedup_estimate_vs_torch,
            "notes": list(bounds.notes),
        }

    def recommend_config(
        self,
        batch_size: int,
        vocab_size: int,
        topk: int,
        dtype: str = "bfloat16",
    ) -> dict[str, Any]:
        """Recommend optimal block size B, threshold B2, and Threadblock Cluster size."""
        spec = TopkWorkloadSpec(
            batch_size=batch_size,
            vocab_size=vocab_size,
            topk=topk,
            dtype=dtype,
        )
        config = DeepSelectEngine.recommend_config(spec)
        return {
            "block_size_b": config.block_size_b,
            "compact_threshold_b2": config.compact_threshold_b2,
            "max_topk": config.max_topk,
            "num_threads": config.num_threads,
            "cluster_size": config.cluster_size,
            "tma_buffer_depth": config.tma_buffer_depth,
            "use_denormal_addition": config.use_denormal_addition,
        }

    def simulate_selection(
        self,
        input_matrix: list[list[float]],
        topk: int,
        block_size: int = 1024,
        compact_threshold: int = 1024,
    ) -> dict[str, Any]:
        """Simulate randomized block scan and monotonic threshold filtering."""
        if not input_matrix:
            return {"status": "ok", "rows_count": 0, "results": []}

        config = DeepSelectAlgorithmConfig(
            block_size_b=block_size,
            compact_threshold_b2=compact_threshold,
        )

        row_results = []
        for row in input_matrix:
            res = DeepSelectEngine.simulate_selection(row, topk, config)
            row_results.append(res)

        return {
            "status": "ok",
            "rows_count": len(input_matrix),
            "topk": topk,
            "results": row_results,
        }

    async def run_sandboxed_benchmark(self, script_path: Path) -> dict[str, Any]:
        """Run an isolated subprocess benchmark adhering strictly to Rule 14 pipe drainage."""
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_data, stderr_data = b"", b""
        try:
            stdout_data, stderr_data = await asyncio.wait_for(proc.communicate(), timeout=30.0)
            return {
                "returncode": proc.returncode,
                "stdout": stdout_data.decode("utf-8", errors="replace"),
                "stderr": stderr_data.decode("utf-8", errors="replace"),
            }
        finally:
            # Enforce Rule 14 pipe transport disposal invariant across all proactor transports
            for pipe in (proc.stdin, proc.stdout, proc.stderr):
                if pipe is not None:
                    try:
                        pipe.close()
                    except Exception:
                        pass
