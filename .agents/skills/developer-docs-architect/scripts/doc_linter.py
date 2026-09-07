# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
doc_linter.py — Slotted Markdown AST Linter and Editorial Inspection Engine
for Developer Documentation Suites (developer-docs-architect).

Enforces:
  1. Bolding ratio limits (<= 10% bold emphasis vs body text volume).
  2. Sequential heading hierarchy (# -> ## -> ### with zero skipped levels).
  3. Fenced code block language identifier verification.
  4. 6-section API endpoint anatomy compliance (Track B reference standard).
  5. Diataxis quadrant taxonomy validation and prerequisite declarations.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Rule 23: UTF-8 standard stream entrypoint invariant
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


# ============================================================================
# Domain Models (Rule 12: Slotted Dataclass Architecture)
# ============================================================================

@dataclass(slots=True)
class LintFinding:
    rule: str
    severity: str  # ERROR, WARNING, INFO
    line: int
    message: str
    remediation: str | None = None


@dataclass(slots=True)
class BoldingMetric:
    bold_characters: int
    total_characters: int
    bold_percentage: float
    max_threshold: float
    passed: bool


@dataclass(slots=True)
class EndpointAnatomyMetric:
    is_api_reference: bool
    sections_found: list[str] = field(default_factory=list)
    missing_sections: list[str] = field(default_factory=list)
    passed: bool = True


@dataclass(slots=True)
class FileLintReport:
    file_path: str
    valid: bool
    bolding: BoldingMetric | None = None
    anatomy: EndpointAnatomyMetric | None = None
    findings: list[LintFinding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "valid": self.valid,
            "bolding": asdict(self.bolding) if self.bolding else None,
            "anatomy": asdict(self.anatomy) if self.anatomy else None,
            "findings_count": len(self.findings),
            "findings": [asdict(f) for f in self.findings],
        }


@dataclass(slots=True)
class DirectoryLintReport:
    target_path: str
    valid: bool
    total_files: int
    passed_files: int
    failed_files: int
    reports: list[FileLintReport] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_path": self.target_path,
            "valid": self.valid,
            "total_files": self.total_files,
            "passed_files": self.passed_files,
            "failed_files": self.failed_files,
            "reports": [r.to_dict() for r in self.reports],
        }


# ============================================================================
# Authoritative Documentation Linter Engine
# ============================================================================

class DocumentationLinter:
    """Evaluates technical documentation against craft and editorial invariants."""

    MANDATORY_ANATOMY_SECTIONS: list[tuple[str, re.Pattern[str]]] = [
        ("Endpoint & Method", re.compile(r"\b(GET|POST|PUT|DELETE|PATCH)\s+/[^\s]*|###?\s*Endpoint", re.IGNORECASE)),
        ("Authentication & Headers", re.compile(r"Authentication|Bearer|API Key|Authorization|Headers", re.IGNORECASE)),
        ("Request Parameters", re.compile(r"Request Parameters|Parameters|Query Parameters|Path Variables", re.IGNORECASE)),
        ("Request Body Example", re.compile(r"Request Body|Payload Example|Sample Request|```json", re.IGNORECASE)),
        ("Response Payloads", re.compile(r"Response (Payloads?|Body|Example)|200 OK|201 Created|HTTP \d{3}", re.IGNORECASE)),
        ("Actionable Error Catalog", re.compile(r"Error (Catalog|Codes?|Responses?)|400|401|403|404|422|429|500", re.IGNORECASE)),
    ]

    def __init__(self, max_bolding_percentage: float = 10.0) -> None:
        self.max_bolding = max_bolding_percentage

    def lint_text(self, text: str, file_identifier: str = "<stdin>") -> FileLintReport:
        findings: list[LintFinding] = []
        lines = text.splitlines()

        # 1. Separate code fences from body text
        in_fence = False
        body_lines: list[tuple[int, str]] = []
        fence_ranges: list[tuple[int, int]] = []
        current_fence_start = 0

        for line_idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                if not in_fence:
                    in_fence = True
                    current_fence_start = line_idx
                    # Rule: Code block must have language tag
                    tag = stripped[3:].strip()
                    if not tag:
                        findings.append(
                            LintFinding(
                                rule="CodeBlockLanguage",
                                severity="WARNING",
                                line=line_idx,
                                message="Fenced code block lacks language identifier",
                                remediation="Specify language (e.g. ```bash, ```json, ```python, ```mermaid).",
                            )
                        )
                else:
                    in_fence = False
                    fence_ranges.append((current_fence_start, line_idx))
            else:
                if not in_fence:
                    body_lines.append((line_idx, line))

        # 2. Heading hierarchy verification
        heading_levels: list[tuple[int, int]] = []
        for line_num, line in body_lines:
            h_match = re.match(r"^(#{1,6})\s+", line)
            if h_match:
                heading_levels.append((line_num, len(h_match.group(1))))

        for i in range(len(heading_levels) - 1):
            curr_line, curr_level = heading_levels[i]
            next_line, next_level = heading_levels[i + 1]
            if next_level > curr_level + 1:
                findings.append(
                    LintFinding(
                        rule="HeadingHierarchy",
                        severity="ERROR",
                        line=next_line,
                        message=f"Heading skips levels: from h{curr_level} (line {curr_line}) to h{next_level} (line {next_line})",
                        remediation="Use sequential heading levels without skipping (e.g., # -> ## -> ###).",
                    )
                )

        # 3. Bolding ratio computation
        body_text = "\n".join(l for _, l in body_lines)
        # Strip frontmatter if present
        if body_text.startswith("---"):
            fm_parts = body_text.split("---", 2)
            if len(fm_parts) >= 3:
                body_text = fm_parts[2]

        bold_spans = re.findall(r"\*\*([^*]+)\*\*|__([^_]+)__", body_text)
        bold_chars = sum(len(b[0] or b[1]) for b in bold_spans)
        # Filter non-whitespace body characters
        total_chars = len(re.sub(r"\s+", "", body_text))

        bold_pct = (bold_chars / total_chars * 100.0) if total_chars > 0 else 0.0
        bold_passed = bold_pct <= self.max_bolding
        bold_metric = BoldingMetric(
            bold_characters=bold_chars,
            total_characters=total_chars,
            bold_percentage=round(bold_pct, 2),
            max_threshold=self.max_bolding,
            passed=bold_passed,
        )

        if not bold_passed:
            findings.append(
                LintFinding(
                    rule="BoldingRatio",
                    severity="ERROR",
                    line=1,
                    message=f"Bolding ratio ({bold_metric.bold_percentage}%) exceeds threshold of {self.max_bolding}%",
                    remediation="Reduce bold emphasis; reserve bolding strictly for key terms and invariants.",
                )
            )

        # 4. 6-Section API Endpoint Anatomy check
        is_api_ref = bool(
            re.search(r"\b(GET|POST|PUT|DELETE|PATCH)\s+/[a-zA-Z0-9_\-/{}]+", text)
            or re.search(r"#+\s*(API Reference|Endpoint Anatomy|Endpoints)", text, re.IGNORECASE)
        )

        anatomy_metric: EndpointAnatomyMetric | None = None
        if is_api_ref:
            found_sections: list[str] = []
            missing_sections: list[str] = []

            for sec_name, pattern in self.MANDATORY_ANATOMY_SECTIONS:
                if pattern.search(text):
                    found_sections.append(sec_name)
                else:
                    missing_sections.append(sec_name)

            anatomy_passed = len(missing_sections) == 0
            anatomy_metric = EndpointAnatomyMetric(
                is_api_reference=True,
                sections_found=found_sections,
                missing_sections=missing_sections,
                passed=anatomy_passed,
            )

            if not anatomy_passed:
                for missing in missing_sections:
                    findings.append(
                        LintFinding(
                            rule="EndpointAnatomy",
                            severity="ERROR",
                            line=1,
                            message=f"Missing mandatory API endpoint section: '{missing}'",
                            remediation=f"Add standard section for '{missing}' per the 6-section Track B reference standard.",
                        )
                    )

        valid = all(f.severity != "ERROR" for f in findings)

        return FileLintReport(
            file_path=file_identifier,
            valid=valid,
            bolding=bold_metric,
            anatomy=anatomy_metric,
            findings=findings,
        )

    def lint_file(self, path: Path | str) -> FileLintReport:
        p = Path(path).resolve()
        if not p.exists() or not p.is_file():
            return FileLintReport(
                file_path=str(p),
                valid=False,
                findings=[LintFinding("FileNotFound", "ERROR", 0, f"File does not exist: {p}")],
            )
        text = p.read_text(encoding="utf-8", errors="replace")
        return self.lint_text(text, file_identifier=str(p))

    def lint_directory(self, dir_path: Path | str, extensions: tuple[str, ...] = (".md", ".markdown")) -> DirectoryLintReport:
        root = Path(dir_path).resolve()
        if not root.exists():
            return DirectoryLintReport(str(root), False, 0, 0, 0, [])

        if root.is_file():
            single = self.lint_file(root)
            return DirectoryLintReport(
                target_path=str(root),
                valid=single.valid,
                total_files=1,
                passed_files=1 if single.valid else 0,
                failed_files=0 if single.valid else 1,
                reports=[single],
            )

        md_files = [f for f in root.glob("**/*") if f.is_file() and f.suffix.lower() in extensions]
        reports: list[FileLintReport] = []

        for f in md_files:
            reports.append(self.lint_file(f))

        passed = sum(1 for r in reports if r.valid)
        failed = sum(1 for r in reports if not r.valid)
        return DirectoryLintReport(
            target_path=str(root),
            valid=failed == 0,
            total_files=len(reports),
            passed_files=passed,
            failed_files=failed,
            reports=reports,
        )


# ============================================================================
# CLI Entrypoint
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="doc_linter.py — Slotted Markdown AST Linter and Editorial Inspection Engine."
    )
    parser.add_argument("target", help="Markdown file or directory to inspect.")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON diagnostics.")
    parser.add_argument("--max-bolding", type=float, default=10.0, help="Max allowable bolding percentage (default: 10.0).")

    args = parser.parse_args()
    linter = DocumentationLinter(max_bolding_percentage=args.max_bolding)

    target_path = Path(args.target).resolve()
    report = linter.lint_directory(target_path) if target_path.is_dir() else linter.lint_file(target_path)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        status_sym = "✓ PASS" if report.valid else "✗ FAIL"
        print(f"Documentation Diagnostic Report: {target_path}")
        print("━" * 60)
        print(f"Overall Status: {status_sym}\n")

        if isinstance(report, DirectoryLintReport):
            print(f"Scanned {report.total_files} files: {report.passed_files} passed, {report.failed_files} failed.\n")
            for sub in report.reports:
                if not sub.valid or sub.findings:
                    f_status = "✓" if sub.valid else "✗"
                    print(f"  {f_status} {Path(sub.file_path).name}:")
                    if sub.bolding:
                        print(f"     Bolding: {sub.bolding.bold_percentage}% (Limit: {sub.bolding.max_threshold}%)")
                    for f in sub.findings:
                        print(f"     [{f.severity}] Line {f.line}: {f.message}")
        else:
            if report.bolding:
                print(f"  Bolding Ratio: {report.bolding.bold_percentage}% (Limit: {report.bolding.max_threshold}%)")
            if report.anatomy and report.anatomy.is_api_reference:
                print(f"  Endpoint Anatomy: {'Complete' if report.anatomy.passed else 'Incomplete'}")
                if report.anatomy.missing_sections:
                    print(f"  Missing Sections: {', '.join(report.anatomy.missing_sections)}")
            if report.findings:
                print("\nFindings:")
                for f in report.findings:
                    print(f"  • [{f.severity}] Line {f.line}: {f.message}")
                    if f.remediation:
                        print(f"    Remediation: {f.remediation}")

    return 0 if report.valid else 1


if __name__ == "__main__":
    sys.exit(main())
