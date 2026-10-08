"""Slotted domain models for Vibe Scanner findings and reports (Rule 12)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(slots=True)
class Finding:
    """A single vulnerability finding."""

    file: str
    line: int
    detector: str
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW
    title: str
    detail: str
    code_snippet: str = ""
    fix_hint: str = ""

    def __repr__(self) -> str:
        return f"[{self.severity}] {self.detector} @ {self.file}:{self.line} — {self.title}"


@dataclass(slots=True)
class ScanResult:
    """Full scan result for one file."""

    path: str
    findings: List[Finding] = field(default_factory=list)
    lines_scanned: int = 0
    parse_error: bool = False
    scan_ms: float = 0.0

    @property
    def critical(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "CRITICAL"]

    @property
    def high(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "HIGH"]


@dataclass(slots=True)
class ScanReport:
    """Aggregated report across all files."""

    root: str
    results: List[ScanResult] = field(default_factory=list)
    total_ms: float = 0.0

    @property
    def effective_ms(self) -> float:
        """Real scan time — from total_ms if set, else sum of individual file times."""
        return self.total_ms if self.total_ms > 0 else sum(r.scan_ms for r in self.results)

    @property
    def all_findings(self) -> List[Finding]:
        return [f for r in self.results for f in r.findings]

    @property
    def by_severity(self) -> Dict[str, List[Finding]]:
        out = defaultdict(list)
        for f in self.all_findings:
            out[f.severity].append(f)
        return dict(out)

    @property
    def by_detector(self) -> Dict[str, List[Finding]]:
        out = defaultdict(list)
        for f in self.all_findings:
            out[f.detector].append(f)
        return dict(out)

    @property
    def files_clean(self) -> int:
        return sum(1 for r in self.results if not r.findings)

    @property
    def files_vulnerable(self) -> int:
        return sum(1 for r in self.results if r.findings)


__all__ = [
    "Finding",
    "ScanReport",
    "ScanResult",
]
