"""Bounded codebase introspection collector for the Deep Repo Auditor service."""

from __future__ import annotations

from pathlib import Path

from .models import (
    AxisFinding,
    ComputeDimensionVector,
    TopologyNodeSummary,
)
from .scanner import _ScanStats, resolve_nested_project_root, scan_repository_tree


class DeepAuditCollector:
    """Executes 5D complexity scoring, topology classification, and 4-axis extraction."""

    def collect(
        self,
        repo_path: Path,
    ) -> tuple[Path, TopologyNodeSummary, ComputeDimensionVector, tuple[AxisFinding, ...]]:
        """Scan repository safely within bounded depth and compute structured telemetry."""
        resolved_root, manifest_name, nesting_depth = resolve_nested_project_root(repo_path)
        has_git = (resolved_root / ".git").exists() or (repo_path.resolve() / ".git").exists()
        stats = scan_repository_tree(resolved_root)
        compute = self._score_complexity(stats, has_git)
        pattern = self._classify_topology(stats)
        topology = TopologyNodeSummary(
            topology_pattern=pattern,
            root_manifest=manifest_name,
            nesting_depth=nesting_depth,
            total_files_scanned=stats.total_files,
            python_files=stats.python_files,
            plugin_count=stats.plugin_manifests,
            skill_count=stats.skill_specs,
            test_file_count=stats.test_files,
            has_git=has_git,
            blast_radius_modules=tuple((stats.blast_modules or [])[:8]),
        )
        axes = self._build_axes(resolved_root, topology, compute, stats)
        return resolved_root, topology, compute, axes

    def _score_complexity(self, stats: _ScanStats, has_git: bool) -> ComputeDimensionVector:
        span = min(1.0, round(0.15 + (stats.total_files / 600.0), 3))
        depth = min(1.0, round(0.2 + (stats.python_files / 300.0), 3))
        rigor = min(1.0, round(0.25 + (stats.test_files / 80.0) + (0.15 if stats.workflow_files else 0.0), 3))
        concurrency = min(1.0, round(0.15 + (stats.async_hits / 25.0), 3))
        ambiguity = 0.35 if (has_git and stats.total_files > 0) else 0.55
        composite = round(0.15 * ambiguity + 0.25 * span + 0.25 * depth + 0.20 * rigor + 0.15 * concurrency, 3)
        composite = min(1.0, max(0.0, composite))
        tier = "HIGH" if composite >= 0.75 else ("MEDIUM" if composite >= 0.40 else "LOW")
        budget = "HIGH_16K" if tier == "HIGH" else ("MEDIUM_4K" if tier == "MEDIUM" else "LOW_1K")
        return ComputeDimensionVector(
            ambiguity=ambiguity,
            span=span,
            depth=depth,
            rigor=rigor,
            concurrency=concurrency,
            composite=composite,
            tier=tier,
            thinking_budget=budget,
        )

    def _classify_topology(self, stats: _ScanStats) -> str:
        if stats.plugin_manifests >= 5 and stats.skill_specs >= 5:
            return "Graph of Trees (IoC Micro-Kernel + Multi-Layer Skills)"
        if stats.async_hits >= 5:
            return "Priority Queue / Async Rewake Dispatcher"
        if stats.plugin_manifests >= 1:
            return "Hash-Indexed Plugin Registry"
        return "Modular Service Package"

    def _build_axes(
        self,
        root: Path,
        topology: TopologyNodeSummary,
        compute: ComputeDimensionVector,
        stats: _ScanStats,
    ) -> tuple[AxisFinding, ...]:
        seam_status = "PASS" if topology.plugin_count > 0 or topology.python_files > 0 else "WARN"
        traj_status = "PASS" if (topology.has_git or stats.has_changelog) else "WARN"
        gate_status = "PASS" if (topology.test_file_count > 0 and stats.workflow_files > 0) else "WARN"
        delta_status = "PASS" if (topology.skill_count > 0 or stats.async_hits > 0) else "INFO"

        return (
            AxisFinding(
                axis="Axis 1: Architecture & Seams",
                title="Module boundaries, manifest detection & plugin seams",
                status=seam_status,
                summary=(
                    f"Resolved root '{root.name}' ({topology.root_manifest}, depth={topology.nesting_depth}) "
                    f"with {topology.plugin_count} plugins across {topology.python_files} Python files."
                ),
                evidence=topology.blast_radius_modules[:4],
                recommendations=("Enforce ServiceKey IoC boundaries across internal plugins.",),
            ),
            AxisFinding(
                axis="Axis 2: Trajectories & Evolution",
                title="Repository history & release cadence telemetry",
                status=traj_status,
                summary=(
                    f"Git metadata={topology.has_git}, CHANGELOG={stats.has_changelog}, "
                    f"pattern={topology.topology_pattern}."
                ),
                evidence=(f"has_git={topology.has_git}", f"has_changelog={stats.has_changelog}"),
                recommendations=("Track module splits and ADRs alongside commit history.",),
            ),
            AxisFinding(
                axis="Axis 3: Verification Gates",
                title="Automated testing & CI workflow gate density",
                status=gate_status,
                summary=(
                    f"Detected {topology.test_file_count} test files "
                    f"and {stats.workflow_files} CI workflow definitions."
                ),
                evidence=(f"test_files={topology.test_file_count}", f"ci_workflows={stats.workflow_files}"),
                recommendations=("Enforce lint, format, mypy, and test gates in CI.",),
            ),
            AxisFinding(
                axis="Axis 4: Delta Innovations",
                title="Agentic skills, async loops & config hygiene",
                status=delta_status,
                summary=f"Found {topology.skill_count} skills, {stats.async_hits} async modules; compute tier={compute.tier}.",
                evidence=(f"skills={topology.skill_count}", f"async_modules={stats.async_hits}"),
                recommendations=("Backfill Rule 44 config.default.yaml and elevate core skills to IoC services.",),
            ),
        )


__all__ = ["DeepAuditCollector", "resolve_nested_project_root", "scan_repository_tree"]
