"""Contract test suite for elephant-goldfish-governor domain engine."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Ensure skill scripts directory is on sys.path
_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from elephant_goldfish_engine import (
    DriftDivergence,
    DriftReport,
    ElephantGoldfishEngine,
    GoldfishFinding,
    GoldfishReviewReport,
    SemanticBoundary,
)


@pytest.mark.unit
class TestElephantGoldfishEngine:
    """Validate EGM slotted domain models, immutability, boundary extraction, and drift detection."""

    def test_semantic_boundary_immutability(self) -> None:
        """Verify SemanticBoundary enforces slotted/frozen immutability (Rule 12, Rule 43)."""
        boundary = SemanticBoundary(
            feature_range_start=1,
            feature_range_end=50,
            detailed_range_start=51,
            detailed_range_end=120,
            total_lines=120,
            has_boundaries=True,
        )
        assert boundary.feature_range_start == 1
        assert boundary.detailed_range_end == 120

        # Rule 43: Direct attribute assignment verification
        with pytest.raises((AttributeError, TypeError)):
            boundary.feature_range_end = 99  # type: ignore

    def test_goldfish_finding_validation_and_immutability(self) -> None:
        """Verify GoldfishFinding validates severity and enforces immutability (Rule 12, Rule 43)."""
        finding = GoldfishFinding(
            id="find_01",
            severity="Blocker",
            reviewer_lens="zoom_out",
            line_start=10,
            line_end=25,
            description="Premature optimization: async queue caching introduces unnecessary complexity",
            recommendation="Remove async queue and use direct in-memory call per YAGNI standard",
        )
        assert finding.severity == "Blocker"

        # Invalid severity rejection
        with pytest.raises(ValueError, match="Invalid severity"):
            GoldfishFinding(
                id="find_02",
                severity="InvalidSeverity",  # type: ignore
                reviewer_lens="zoom_out",
                line_start=1,
                line_end=5,
                description="test",
                recommendation="test",
            )

        # Rule 43 immutability
        with pytest.raises((AttributeError, TypeError)):
            finding.severity = "Nit"  # type: ignore

    def test_boundary_extraction_from_markdown(self) -> None:
        """Verify semantic boundary discovery separates FeatureRange from DetailedRange."""
        markdown_doc = """# Webhook Feature Spec

## Overview
High altitude architecture describing webhook delivery.

## Goals vs Non-Goals
* In-scope: idempotent delivery.
* Out-of-scope: custom retries.

## Detailed Implementation Plan
### Step 1: Create WebhookDispatcher
Concrete python class in `src/webhooks/dispatcher.py`.

### Step 2: Add Database Models
Create migrations for `WebhookEvent`.
"""
        boundary = ElephantGoldfishEngine.extract_semantic_boundaries(markdown_doc)
        assert boundary.has_boundaries is True
        assert boundary.feature_range_start == 1
        assert boundary.detailed_range_start > 1
        assert boundary.feature_range_end < boundary.detailed_range_start

    def test_finding_deduplication_and_sorting(self) -> None:
        """Verify findings are deduplicated and sorted by severity (Blocker -> Major -> Nit)."""
        f1 = GoldfishFinding("f1", "Nit", "style", 10, 10, "Wordy phrasing", "Simplify")
        f2 = GoldfishFinding("f2", "Blocker", "zoom_out", 5, 15, "YAGNI violation", "Strip cache")
        f3 = GoldfishFinding("f3", "Major", "design_critic", 20, 30, "Missing race condition handling", "Add mutex")
        f4 = GoldfishFinding("f4", "Nit", "style", 10, 10, "Wordy phrasing", "Simplify")  # Duplicate

        deduped = ElephantGoldfishEngine.deduplicate_findings([f1, f2, f3, f4])
        assert len(deduped) == 3
        # Ensure Blocker is first, then Major, then Nit
        assert deduped[0].severity == "Blocker"
        assert deduped[1].severity == "Major"
        assert deduped[2].severity == "Nit"

    def test_report_formatting(self) -> None:
        """Verify report markdown adheres to EGM layout standards."""
        finding = GoldfishFinding(
            id="f1",
            severity="Blocker",
            reviewer_lens="zoom_out",
            line_start=10,
            line_end=15,
            description="Spec introduces speculative distributed cache",
            recommendation="Revert to simple SQLite storage",
        )
        report = GoldfishReviewReport(
            target_file="docs/designs/test.md",
            stage="Stage 5: Initial Zoom Out",
            findings=(finding,),
            completed_reviewers=("egm-zoom-out",),
            failed_reviewers=(),
        )
        assert report.blocker_count == 1
        output = ElephantGoldfishEngine.format_review_report(report)
        assert "# Goldfish Review Report" in output
        assert "Blockers: 1" in output
        assert "egm-zoom-out" in output

