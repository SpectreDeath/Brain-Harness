"""Elephant-Goldfish Governor Domain Engine.

Provides slotted/frozen domain models for spec parsing, semantic boundary isolation
(FeatureRange vs DetailedRange), zero-context finding normalization, and AST codebase drift detection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import Any


@dataclass(slots=True, frozen=True)
class SemanticBoundary:
    """Immutable representation of spec semantic altitude ranges."""

    feature_range_start: int
    feature_range_end: int
    detailed_range_start: int
    detailed_range_end: int
    total_lines: int
    has_boundaries: bool = True

    def __post_init__(self) -> None:
        if self.total_lines < 0:
            raise ValueError("total_lines cannot be negative")
        if self.feature_range_start < 1 and self.total_lines > 0:
            raise ValueError("feature_range_start must be >= 1")


@dataclass(slots=True, frozen=True)
class GoldfishFinding:
    """Immutable finding emitted by a Goldfish reviewer persona."""

    id: str
    severity: str  # "Blocker", "Major", "Nit"
    reviewer_lens: str
    line_start: int
    line_end: int
    description: str
    recommendation: str

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("GoldfishFinding.id cannot be empty")
        if self.severity not in ("Blocker", "Major", "Nit"):
            raise ValueError(f"Invalid severity '{self.severity}'. Must be Blocker, Major, or Nit")
        if not self.description or not self.description.strip():
            raise ValueError("GoldfishFinding.description cannot be empty")


@dataclass(slots=True, frozen=True)
class GoldfishReviewReport:
    """Immutable consolidated Goldfish review deliverable."""

    target_file: str
    stage: str
    findings: tuple[GoldfishFinding, ...]
    completed_reviewers: tuple[str, ...]
    failed_reviewers: tuple[str, ...] = field(default_factory=tuple)
    blocker_count: int = 0
    major_count: int = 0
    nit_count: int = 0

    def __post_init__(self) -> None:
        if not self.target_file:
            raise ValueError("GoldfishReviewReport.target_file cannot be empty")
        calc_blockers = sum(1 for f in self.findings if f.severity == "Blocker")
        calc_majors = sum(1 for f in self.findings if f.severity == "Major")
        calc_nits = sum(1 for f in self.findings if f.severity == "Nit")
        if self.blocker_count != calc_blockers:
            object.__setattr__(self, "blocker_count", calc_blockers)
        if self.major_count != calc_majors:
            object.__setattr__(self, "major_count", calc_majors)
        if self.nit_count != calc_nits:
            object.__setattr__(self, "nit_count", calc_nits)


@dataclass(slots=True, frozen=True)
class DriftDivergence:
    """Immutable divergence identified between living spec and codebase."""

    category: str  # "Missing Feature", "Incomplete Model", "Logic Shortcut", "Architectural Divergence"
    symbol_name: str
    expected_behavior: str
    observed_reality: str
    file_path: str = ""

    def __post_init__(self) -> None:
        valid_cats = ("Missing Feature", "Incomplete Model", "Logic Shortcut", "Architectural Divergence")
        if self.category not in valid_cats:
            raise ValueError(f"Invalid category '{self.category}'. Must be one of {valid_cats}")
        if not self.symbol_name or not self.symbol_name.strip():
            raise ValueError("DriftDivergence.symbol_name cannot be empty")


@dataclass(slots=True, frozen=True)
class DriftReport:
    """Immutable living spec drift assessment deliverable."""

    spec_path: str
    source_root: str
    divergences: tuple[DriftDivergence, ...]
    has_drift: bool
    scanned_files_count: int = 0

    def __post_init__(self) -> None:
        if not self.spec_path:
            raise ValueError("DriftReport.spec_path cannot be empty")
        expected_has_drift = len(self.divergences) > 0
        if self.has_drift != expected_has_drift:
            object.__setattr__(self, "has_drift", expected_has_drift)


class ElephantGoldfishEngine:
    """Core domain engine orchestrating EGM protocols."""

    @staticmethod
    def extract_semantic_boundaries(content: str) -> SemanticBoundary:
        """Extract line ranges for FeatureRange and DetailedRange from spec markdown."""
        lines = content.splitlines()
        total_lines = len(lines)
        if total_lines == 0:
            return SemanticBoundary(1, 1, 1, 1, 0, has_boundaries=False)

        feature_start = 1
        feature_end = total_lines
        detailed_start = total_lines
        detailed_end = total_lines

        detailed_markers = (
            "## implementation",
            "## detailed design",
            "## detailed plan",
            "## implementation details",
            "## detailed implementation",
            "### step-by-step implementation",
            "## code changes",
            "## test plan",
        )

        for idx, line in enumerate(lines, start=1):
            lower = line.strip().lower()
            if any(lower.startswith(m) for m in detailed_markers):
                feature_end = max(1, idx - 1)
                detailed_start = idx
                detailed_end = total_lines
                break

        return SemanticBoundary(
            feature_range_start=feature_start,
            feature_range_end=feature_end,
            detailed_range_start=detailed_start,
            detailed_range_end=detailed_end,
            total_lines=total_lines,
            has_boundaries=(detailed_start < total_lines),
        )

    @staticmethod
    def deduplicate_findings(findings: list[GoldfishFinding]) -> tuple[GoldfishFinding, ...]:
        """Deduplicate findings based on lens, line proximity, and description similarity."""
        unique: list[GoldfishFinding] = []
        seen_keys: set[str] = set()

        for f in findings:
            key = f"{f.reviewer_lens}:{f.line_start}:{f.description.strip().lower()[:40]}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique.append(f)

        # Sort: Blockers first, then Majors, then Nits
        severity_order = {"Blocker": 0, "Major": 1, "Nit": 2}
        unique.sort(key=lambda x: (severity_order.get(x.severity, 3), x.line_start))
        return tuple(unique)

    @staticmethod
    def detect_codebase_drift(
        spec_content: str,
        source_root: Path | str,
    ) -> DriftReport:
        """Analyze living spec content against target codebase files to detect drift."""
        root_path = Path(source_root).resolve()
        divergences: list[DriftDivergence] = []
        scanned_count = 0

        # Extract symbols mentioned in spec (e.g. `ClassName`, `function_name()`, `filename.py`)
        symbol_pattern = re.compile(r"`([A-Za-z0-9_]{3,40}(?:\(\))?)`")
        raw_symbols = set(symbol_pattern.findall(spec_content))
        target_symbols = {s.rstrip("()") for s in raw_symbols if not s.endswith((".md", ".json", ".yaml", ".txt"))}

        # Scan code files
        code_text_corpus: dict[str, str] = {}
        if root_path.exists() and root_path.is_dir():
            for root, dirs, files in os.walk(root_path):
                dirs[:] = [d for d in dirs if d not in (".git", "node_modules", ".venv", "__pycache__", "dist", "build")]
                for f in files:
                    if f.endswith((".py", ".ts", ".js", ".go", ".rs", ".cpp", ".h")):
                        scanned_count += 1
                        file_path = Path(root) / f
                        try:
                            code_text_corpus[str(file_path.relative_to(root_path))] = file_path.read_text(
                                encoding="utf-8", errors="ignore"
                            )
                        except Exception:
                            continue

        # Check for symbols declared in spec that do not appear anywhere in code
        all_code = "\n".join(code_text_corpus.values())
        for sym in sorted(target_symbols):
            # Ignore standard keywords or short acronyms
            if sym in ("True", "False", "None", "self", "init", "main", "args", "kwargs", "data", "test", "path"):
                continue
            if sym not in all_code:
                divergences.append(
                    DriftDivergence(
                        category="Missing Feature",
                        symbol_name=sym,
                        expected_behavior=f"Declared symbol '{sym}' referenced in spec should exist in codebase",
                        observed_reality=f"Symbol '{sym}' not found in {scanned_count} scanned source files",
                    )
                )

        return DriftReport(
            spec_path="spec_document",
            source_root=str(root_path),
            divergences=tuple(divergences[:10]),  # Bound to top 10 divergences
            has_drift=len(divergences) > 0,
            scanned_files_count=scanned_count,
        )

    @staticmethod
    def format_review_report(report: GoldfishReviewReport) -> str:
        """Format review findings into EGM-compliant Markdown deliverable."""
        lines = [
            "# Goldfish Review Report",
            "",
            f"**Target:** `{report.target_file}`",
            f"**Stage:** `{report.stage}`",
            "",
            "## Reviewer Status",
            "",
            "| Reviewer | Status |",
            "| --- | --- |",
        ]
        for r in report.completed_reviewers:
            lines.append(f"| `{r}` | completed |")
        for r in report.failed_reviewers:
            lines.append(f"| `{r}` | not run |")

        lines.extend([
            "",
            f"## Prioritized Findings (Blockers: {report.blocker_count}, Majors: {report.major_count}, Nits: {report.nit_count})",
            "",
        ])

        if not report.findings:
            lines.append("No findings reported. Document satisfies standard criteria.")
            return "\n".join(lines)

        for idx, f in enumerate(report.findings, start=1):
            lines.extend([
                f"### {idx}. {f.description[:60]} — Severity: {f.severity}",
                f"* **Reviewer Lens:** `{f.reviewer_lens}`",
                f"* **Affected Scope:** Lines {f.line_start}-{f.line_end}",
                f"* **Discrepancy Description**: {f.description}",
                f"* **Rationale & Recommendation**: {f.recommendation}",
                "",
            ])

        return "\n".join(lines)

    @staticmethod
    def format_drift_report(report: DriftReport) -> str:
        """Format drift detection deliverable adhering to EGM differential reporting standard."""
        lines = [
            f"# Codebase Drift Report — {report.spec_path}",
            "",
            f"**Source Root:** `{report.source_root}`",
            f"**Scanned Files:** {report.scanned_files_count}",
            "",
        ]

        if not report.has_drift:
            lines.append("No drift detected.")
            return "\n".join(lines)

        lines.extend([
            "## Detected Divergences",
            "",
        ])

        for div in report.divergences:
            lines.extend([
                f"### [{div.category}] {div.symbol_name}",
                f"* **Expected**: {div.expected_behavior}",
                f"* **Observed**: {div.observed_reality}",
                f"* **File**: `{div.file_path or 'Global / Missing'}`",
                "",
            ])

        return "\n".join(lines)

