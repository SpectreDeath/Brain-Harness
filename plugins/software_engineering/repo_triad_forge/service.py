"""Repo-Triad Forge Service implementation."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

# Add skill scripts directory to sys.path
_SKILL_SCRIPTS = Path(__file__).resolve().parents[3] / ".agents" / "skills" / "repo-triad-forge" / "scripts"
if _SKILL_SCRIPTS.exists() and str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))

from triad_pipeline import (  # type: ignore
    RepoTriadPipelineEngine,
)

from harness.services.repo_triad_forge import (
    KiCandidateData,
    RepoInspectionData,
    RepoTriadForgeService,
    TriadBriefData,
    TriadRunData,
)

logger = structlog.get_logger(__name__)


class RepoTriadForgeServiceImpl(RepoTriadForgeService):
    """Implementation of RepoTriadForgeService executing engine transformations."""

    def inspect(self, repo_path: str) -> RepoInspectionData:
        """Inspect repository structure and evaluate 5D compute complexity."""
        res = RepoTriadPipelineEngine.inspect_repository(repo_path)
        return RepoInspectionData(
            repo_path=res.repo_path,
            repo_name=res.repo_name,
            languages=list(res.languages),
            packages=list(res.packages),
            has_git=res.has_git,
            compute_tier=res.compute_tier,
            composite_complexity=res.composite_complexity,
            total_files=res.total_files,
            blast_radius_roots=list(res.blast_radius_roots),
        )

    def generate_briefs(
        self, repo_path: str, output_dir: str | None = None
    ) -> list[TriadBriefData]:
        """Generate 5 interactive HTML visual briefs in output directory (or temp)."""
        inspection = RepoTriadPipelineEngine.inspect_repository(repo_path)
        out_dir = Path(output_dir) if output_dir else None
        files = RepoTriadPipelineEngine.scaffold_visual_briefs(inspection, out_dir)

        brief_titles = {
            "compute-assessor": "5D Compute & Complexity Assessment",
            "data-topology-review": "Causal DAG & Data Topology Map",
            "repo-reader": "Codebase Archaeology & Commit Trajectory",
            "deep-skill-forge": "Deep Skill Specification & Domain Architecture",
            "repo-to-plugin-forge": "Sandboxed Plugin Architecture & IoC Registry",
        }

        brief_data: list[TriadBriefData] = []
        for f in files:
            slug = "visual-brief"
            for s in brief_titles:
                if s in f.stem:
                    slug = s
                    break
            title = brief_titles.get(slug, "Visual Brief")
            brief_data.append(
                TriadBriefData(
                    slug=slug,
                    title=title,
                    html_path=str(f),
                )
            )
        return brief_data

    def extract_kis(self, repo_path: str) -> list[KiCandidateData]:
        """Extract candidate Knowledge Items from repository scan."""
        inspection = RepoTriadPipelineEngine.inspect_repository(repo_path)
        candidates = RepoTriadPipelineEngine.extract_ki_candidates(inspection)
        return [
            KiCandidateData(
                id=c.id,
                title=c.title,
                domain=c.domain,
                claims_count=c.claims_count,
                citations=list(c.citations),
                confidence=c.confidence,
            )
            for c in candidates
        ]

    def commit_kis(
        self, kis_data: list[dict[str, Any]], vault_dir: str | None = None
    ) -> list[str]:
        """Commit Knowledge Items to vault in canonical dual-file format (Rule 40)."""
        v_root = Path(vault_dir) if vault_dir else None
        return RepoTriadPipelineEngine.commit_vault_kis(kis_data, v_root)

    def run_pipeline(
        self, repo_path: str, options: dict[str, Any] | None = None
    ) -> TriadRunData:
        """Execute full 5-stage triad pipeline with bounded in-flight self-repair."""
        opts = options or {}
        try:
            # Stage 1: Inspect
            inspection = RepoTriadPipelineEngine.inspect_repository(repo_path)
            stages = ["Stage 1: Pre-Flight & 5D Complexity"]

            # Stage 2: Briefs
            out_dir = Path(opts.get("briefs_dir")) if opts.get("briefs_dir") else None
            briefs = RepoTriadPipelineEngine.scaffold_visual_briefs(inspection, out_dir)
            stages.append("Stage 2: Visual Briefs Scaffolding")

            # Stage 3: Knowledge Items
            kis = RepoTriadPipelineEngine.extract_ki_candidates(inspection)
            stages.append("Stage 3: Knowledge Item Extraction")

            kis_payload = [
                {
                    "id": k.id,
                    "title": k.title,
                    "source_target": inspection.repo_path,
                    "assertion": k.title,
                    "citations": list(k.citations),
                }
                for k in kis
            ]
            v_dir = Path(opts.get("vault_dir")) if opts.get("vault_dir") else None
            committed = RepoTriadPipelineEngine.commit_vault_kis(kis_payload, v_dir)
            stages.append("Stage 4: Dual-File Vault Commit")

            return TriadRunData(
                success=True,
                stages_completed=stages,
                artifacts_generated=[str(b) for b in briefs],
                kis_committed=committed,
                message=f"Triad pipeline completed successfully for {inspection.repo_name}",
            )
        except Exception as ex:
            logger.error("triad_run_failed", error=str(ex))
            return TriadRunData(
                success=False,
                stages_completed=[],
                artifacts_generated=[],
                kis_committed=[],
                message=f"Triad pipeline failed: {ex}",
            )
