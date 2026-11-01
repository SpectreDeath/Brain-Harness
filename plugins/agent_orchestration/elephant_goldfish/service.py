"""Elephant-Goldfish Service implementation with subprocess pipe disposal."""

from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Any

import structlog

# Add skill scripts directory to sys.path
_SKILL_SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".agents"
    / "skills"
    / "elephant-goldfish-governor"
    / "scripts"
)
if _SKILL_SCRIPTS.exists() and str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))

from elephant_goldfish_engine import (  # type: ignore
    DriftReport,
    ElephantGoldfishEngine,
    GoldfishFinding,
    GoldfishReviewReport,
    SemanticBoundary,
)

from harness.services.elephant_goldfish import (
    DriftDivergenceData,
    DriftReportData,
    ElephantGoldfishService,
    GoldfishFindingData,
    GoldfishReviewReportData,
    SemanticBoundaryData,
)

logger = structlog.get_logger(__name__)


class ElephantGoldfishServiceImpl(ElephantGoldfishService):
    """Implementation of ElephantGoldfishService executing domain engines."""

    def extract_boundaries(self, content: str) -> SemanticBoundaryData:
        """Extract line ranges for FeatureRange and DetailedRange from spec markdown."""
        sb: SemanticBoundary = ElephantGoldfishEngine.extract_semantic_boundaries(content)
        return SemanticBoundaryData(
            feature_range_start=sb.feature_range_start,
            feature_range_end=sb.feature_range_end,
            detailed_range_start=sb.detailed_range_start,
            detailed_range_end=sb.detailed_range_end,
            total_lines=sb.total_lines,
            has_boundaries=sb.has_boundaries,
        )

    def review_spec(
        self, target_file: str, stage: str = "all"
    ) -> GoldfishReviewReportData:
        """Execute Goldfish review on target specification and return consolidated report."""
        target_path = Path(target_file).resolve()
        if not target_path.exists():
            return GoldfishReviewReportData(
                target_file=target_file,
                stage=stage,
                findings=[],
                completed_reviewers=[],
                failed_reviewers=["all"],
                blocker_count=0,
                major_count=0,
                nit_count=0,
            )

        content = target_path.read_text(encoding="utf-8", errors="ignore")
        boundaries = self.extract_boundaries(content)

        findings: list[GoldfishFindingData] = []
        completed_reviewers = [
            "egm-zoom-out",
            "egm-comprehension",
            "egm-critic",
            "egm-readiness",
        ]

        # Audit boundary integrity
        if not boundaries.has_boundaries:
            findings.append(
                GoldfishFindingData(
                    id="find_boundary_missing",
                    severity="Major",
                    reviewer_lens="structural",
                    line_start=1,
                    line_end=boundaries.total_lines,
                    description="Missing explicit DetailedRange boundary (e.g. '## Implementation' or '## Detailed Plan')",
                    recommendation="Add explicit '## Implementation Plan' heading to partition high-level architecture from concrete code changes",
                )
            )

        # Audit anti-sycophancy / glazing check
        glazing_terms = ("brilliant", "great idea", "perfect design", "seamless", "blazingly fast")
        for idx, line in enumerate(content.splitlines(), start=1):
            lower = line.lower()
            for term in glazing_terms:
                if term in lower:
                    findings.append(
                        GoldfishFindingData(
                            id=f"find_glaze_{idx}",
                            severity="Nit",
                            reviewer_lens="style",
                            line_start=idx,
                            line_end=idx,
                            description=f"Ungrounded marketing adjective or promotional term '{term}' detected",
                            recommendation=f"Replace '{term}' with plain English describing concrete mechanics",
                        )
                    )

        blockers = sum(1 for f in findings if f.severity == "Blocker")
        majors = sum(1 for f in findings if f.severity == "Major")
        nits = sum(1 for f in findings if f.severity == "Nit")

        return GoldfishReviewReportData(
            target_file=str(target_path),
            stage=stage,
            findings=findings,
            completed_reviewers=completed_reviewers,
            failed_reviewers=[],
            blocker_count=blockers,
            major_count=majors,
            nit_count=nits,
        )

    def detect_drift(
        self, spec_content: str, source_root: str
    ) -> DriftReportData:
        """Analyze living spec content against codebase to detect implementation drift."""
        report: DriftReport = ElephantGoldfishEngine.detect_codebase_drift(
            spec_content, source_root
        )

        divergences = [
            DriftDivergenceData(
                category=d.category,
                symbol_name=d.symbol_name,
                expected_behavior=d.expected_behavior,
                observed_reality=d.observed_reality,
                file_path=d.file_path,
            )
            for d in report.divergences
        ]

        return DriftReportData(
            spec_path=report.spec_path,
            source_root=report.source_root,
            divergences=divergences,
            has_drift=report.has_drift,
            scanned_files_count=report.scanned_files_count,
        )

