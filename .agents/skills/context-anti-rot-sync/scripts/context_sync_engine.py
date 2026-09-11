#!/usr/bin/env python3
"""Context Anti-Rot Sync Engine — authoritative domain abstraction for context hygiene & synchronization.

Architectural invariants enforced:
- Slotted and frozen dataclass architecture (Rule 12)
- Rule 11 line budget and negative boundary enforcement
- Rule 44 frontmatter character bounds (100–350 chars)
- UTF-8 stream codec entrypoint on Windows (Rule 23)
- Zero-fork operational configuration (Rule 44)
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


@dataclass(slots=True, frozen=True)
class ContextViolation:
    """Immutable record of an instruction or context defect (Rule 12)."""

    rule_id: str
    file_path: str
    line_number: int
    message: str
    severity: str = "ERROR"

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(slots=True, frozen=True)
class AuditResult:
    """Immutable result of context audit operation (Rule 12)."""

    target_file: str
    total_lines: int
    max_lines_allowed: int
    passed: bool
    violations: tuple[ContextViolation, ...] = field(default_factory=tuple)
    has_negative_boundaries: bool = False
    has_execution_seams: bool = False

    @property
    def violations_count(self) -> int:
        return len(self.violations)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_file": self.target_file,
            "total_lines": self.total_lines,
            "max_lines_allowed": self.max_lines_allowed,
            "passed": self.passed,
            "has_negative_boundaries": self.has_negative_boundaries,
            "has_execution_seams": self.has_execution_seams,
            "violations_count": self.violations_count,
            "violations": [v.to_dict() for v in self.violations],
        }


@dataclass(slots=True, frozen=True)
class CleanResult:
    """Immutable result of context file cleaning and whitespace deduplication (Rule 12)."""

    source_file: str
    output_file: str
    original_lines: int
    cleaned_lines: int
    saved_lines: int

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "output_file": self.output_file,
            "original_lines": self.original_lines,
            "cleaned_lines": self.cleaned_lines,
            "saved_lines": self.saved_lines,
        }


@dataclass(slots=True, frozen=True)
class SyncTargetRecord:
    """Immutable record of a synchronized secondary agent configuration target (Rule 12)."""

    target: str
    rules_projected: int
    status: str = "SYNCHRONIZED"

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "rules_projected": self.rules_projected,
            "status": self.status,
        }


@dataclass(slots=True, frozen=True)
class SyncResult:
    """Immutable result of SSOT rule projection synchronization (Rule 12)."""

    source: str
    total_rules_extracted: int
    targets_synchronized: tuple[SyncTargetRecord, ...] = field(default_factory=tuple)

    def __getitem__(self, item: str) -> Any:
        if item == "targets_synchronized":
            return [t.to_dict() for t in self.targets_synchronized]
        return getattr(self, item)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "total_rules_extracted": self.total_rules_extracted,
            "targets_synchronized": [t.to_dict() for t in self.targets_synchronized],
        }


@dataclass(slots=True, frozen=True)
class LintCheckResult:
    """Immutable result of linter check execution (Rule 12)."""

    file_path: str
    check_type: str
    passed: bool
    details: str

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "check_type": self.check_type,
            "passed": self.passed,
            "details": self.details,
        }


@dataclass(slots=True, frozen=True)
class WorkspaceLintReport:
    """Immutable comprehensive report of workspace anti-rot linting (Rule 12)."""

    scan_root: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    all_passed: bool
    checks: tuple[LintCheckResult, ...] = field(default_factory=tuple)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scan_root": self.scan_root,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "all_passed": self.all_passed,
            "checks": [c.to_dict() for c in self.checks],
        }


@dataclass(slots=True, frozen=True)
class ContextSyncExecutionReport:
    """Immutable comprehensive execution report for the complete context hygiene pipeline (Rule 12)."""

    target_file: str
    audit_result: AuditResult
    clean_result: CleanResult | None
    sync_result: SyncResult | None
    lint_report: WorkspaceLintReport
    success: bool
    duration_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_file": self.target_file,
            "audit": self.audit_result.to_dict(),
            "clean": self.clean_result.to_dict() if self.clean_result else None,
            "sync": self.sync_result.to_dict() if self.sync_result else None,
            "lint": self.lint_report.to_dict(),
            "success": self.success,
            "duration_seconds": round(self.duration_seconds, 3),
        }


class ContextSyncEngine:
    """Core logic engine for context auditing, cleaning, syncing and linting."""

    def __init__(self, workspace_root: Path | str | None = None) -> None:
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()

    def audit_file(self, target_path: Path | str, max_lines: int = 150) -> AuditResult:
        """Audits an instruction file against line limits, lint leaks, and boundaries (Rule 11)."""
        t_path = Path(target_path)
        if not t_path.is_absolute():
            t_path = self.workspace_root / t_path

        if not t_path.exists():
            return AuditResult(
                target_file=str(t_path),
                total_lines=0,
                max_lines_allowed=max_lines,
                passed=False,
                violations=(
                    ContextViolation(
                        rule_id="RULE11_FILE_MISSING",
                        file_path=str(t_path),
                        line_number=0,
                        message=f"Target instruction file does not exist: {t_path}",
                        severity="CRITICAL",
                    ),
                ),
            )

        text = t_path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        total_lines = len(lines)
        violations: list[ContextViolation] = []

        # 1. Line budget check (Rule 11)
        if total_lines > max_lines:
            violations.append(
                ContextViolation(
                    rule_id="RULE11_LINE_BUDGET_OVERFLOW",
                    file_path=str(t_path),
                    line_number=total_lines,
                    message=f"Instruction file exceeds {max_lines} lines budget (found {total_lines} lines)",
                    severity="ERROR",
                )
            )

        # 2. Lint leakage detection
        lint_leak_patterns = [
            (r"Traceback \(most recent call last\):", "Python traceback leakage"),
            (r"npm ERR!", "npm error log leakage"),
            (r"pytest: error:", "Pytest error leakage"),
            (r"SyntaxError:|TypeError:|ValueError:", "Unsanitized language error dump"),
        ]
        for idx, line in enumerate(lines, 1):
            for pattern, desc in lint_leak_patterns:
                if re.search(pattern, line):
                    violations.append(
                        ContextViolation(
                            rule_id="RULE11_LINT_LEAKAGE",
                            file_path=str(t_path),
                            line_number=idx,
                            message=f"Detected lint leakage ({desc}) on line {idx}",
                            severity="WARNING",
                        )
                    )

        # 3. Execution seams & negative boundaries
        has_negative_boundaries = bool(
            re.search(r"negative boundaries|what not to touch|do not touch|boundary", text, re.IGNORECASE)
        )
        has_execution_seams = bool(
            re.search(r"testing|build|pytest|pytest-asyncio|seam", text, re.IGNORECASE)
        )

        if not has_negative_boundaries:
            violations.append(
                ContextViolation(
                    rule_id="RULE11_MISSING_NEGATIVE_BOUNDARIES",
                    file_path=str(t_path),
                    line_number=1,
                    message="Instruction file lacks explicit negative boundaries ('what NOT to touch')",
                    severity="WARNING",
                )
            )

        passed = len([v for v in violations if v.severity in ("ERROR", "CRITICAL")]) == 0

        return AuditResult(
            target_file=str(t_path),
            total_lines=total_lines,
            max_lines_allowed=max_lines,
            passed=passed,
            violations=tuple(violations),
            has_negative_boundaries=has_negative_boundaries,
            has_execution_seams=has_execution_seams,
        )

    def clean_file(self, target_path: Path | str, output_path: Path | str) -> CleanResult:
        """Cleans excess whitespace, redundant empty lines, and trailing spaces."""
        t_path = Path(target_path)
        if not t_path.is_absolute():
            t_path = self.workspace_root / t_path

        out_path = Path(output_path)
        if not out_path.is_absolute():
            out_path = self.workspace_root / out_path

        text = t_path.read_text(encoding="utf-8", errors="ignore")
        lines = [line.rstrip() for line in text.splitlines()]

        cleaned_lines: list[str] = []
        last_blank = False
        for line in lines:
            is_blank = len(line.strip()) == 0
            if is_blank:
                if not last_blank:
                    cleaned_lines.append("")
                last_blank = True
            else:
                cleaned_lines.append(line)
                last_blank = False

        cleaned_text = "\n".join(cleaned_lines) + "\n"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(cleaned_text, encoding="utf-8")

        return CleanResult(
            source_file=str(t_path),
            output_file=str(out_path),
            original_lines=len(lines),
            cleaned_lines=len(cleaned_lines),
            saved_lines=len(lines) - len(cleaned_lines),
        )

    def sync_projections(self, source_path: Path | str, target_paths: list[str] | None = None) -> SyncResult:
        """Generates synchronized rule projections for secondary agent config files."""
        src = Path(source_path)
        if not src.is_absolute():
            src = self.workspace_root / src

        if not src.exists():
            raise FileNotFoundError(f"Source manifest missing: {src}")

        text = src.read_text(encoding="utf-8", errors="ignore")
        rules_match = re.findall(r"(\d+\.\s+\*\*([^*]+)\*\*.*?)(?=\n\d+\.\s+\*\*|\n##|\Z)", text, re.DOTALL)
        extracted_rules = [r[0].strip() for r in rules_match]

        targets = target_paths or ["CLAUDE.md", ".cursorrules"]
        sync_results: list[SyncTargetRecord] = []

        for tgt in targets:
            tgt_path = self.workspace_root / tgt
            header = f"# Derived Agent Rules (Synchronized from {src.name})\n# DO NOT EDIT MANUALLY — Use context-anti-rot-sync\n\n"
            content = header + "\n\n".join(extracted_rules[:15]) + "\n"
            tgt_path.write_text(content, encoding="utf-8")
            sync_results.append(
                SyncTargetRecord(
                    target=str(tgt_path),
                    rules_projected=min(len(extracted_rules), 15),
                    status="SYNCHRONIZED",
                )
            )

        return SyncResult(
            source=str(src),
            total_rules_extracted=len(extracted_rules),
            targets_synchronized=tuple(sync_results),
        )

    def lint_workspace(self, scan_root: Path | str | None = None) -> WorkspaceLintReport:
        """Runs automated anti-rot verification across context and skill files."""
        root = Path(scan_root or self.workspace_root).resolve()
        results: list[LintCheckResult] = []

        # 1. Check root instruction files
        for inst_name in ["AGENTS.md", "CLAUDE.md"]:
            inst_path = root / inst_name
            if inst_path.exists():
                lines = inst_path.read_text(encoding="utf-8", errors="ignore").splitlines()
                passed = len(lines) <= 150
                results.append(
                    LintCheckResult(
                        file_path=str(inst_path),
                        check_type="RULE11_LINE_COUNT",
                        passed=passed,
                        details=f"{len(lines)} lines (max 150)",
                    )
                )

        # 2. Check skill frontmatters (Rule 44: 100 to 350 chars)
        skills_dir = root / ".agents" / "skills"
        if skills_dir.exists():
            for sdir in sorted(skills_dir.iterdir()):
                if not sdir.is_dir() or sdir.name.startswith("."):
                    continue
                skill_file = sdir / "SKILL.md"
                if skill_file.exists():
                    stext = skill_file.read_text(encoding="utf-8", errors="ignore")
                    m = re.search(r"^description:\s*(.*?)(?=\n[a-z_]+:|\n---)", stext, re.DOTALL | re.MULTILINE)
                    if m:
                        desc = m.group(1).strip().strip(">").strip().replace("\n", " ")
                        desc_len = len(desc)
                        passed = 100 <= desc_len <= 350
                        results.append(
                            LintCheckResult(
                                file_path=str(skill_file),
                                check_type="RULE44_FRONTMATTER_BUDGET",
                                passed=passed,
                                details=f"Description length: {desc_len} chars (bounds: 100-350)",
                            )
                        )

        passed_count = sum(1 for r in results if r.passed)
        failed_count = sum(1 for r in results if not r.passed)

        return WorkspaceLintReport(
            scan_root=str(root),
            total_checks=len(results),
            passed_checks=passed_count,
            failed_checks=failed_count,
            all_passed=failed_count == 0,
            checks=tuple(results),
        )

    def execute_pipeline(
        self,
        target_file: Path | str = "AGENTS.md",
        sync_targets: list[str] | None = None,
        scan_root: Path | str | None = None,
        clean_output: Path | str | None = None,
        strict_lint: bool = False,
    ) -> ContextSyncExecutionReport:
        """Executes full end-to-end context hygiene and sync cycle in a single atomic pass."""
        start_time = time.monotonic()

        # 1. Audit
        audit_res = self.audit_file(target_file)

        # 2. Clean (if output path specified)
        clean_res: CleanResult | None = None
        if clean_output:
            clean_res = self.clean_file(target_file, clean_output)

        # 3. Sync
        sync_res: SyncResult | None = None
        t_path = Path(target_file)
        if not t_path.is_absolute():
            t_path = self.workspace_root / t_path
        if t_path.exists():
            sync_res = self.sync_projections(t_path, sync_targets)

        # 4. Lint
        lint_report = self.lint_workspace(scan_root)

        duration = time.monotonic() - start_time
        if strict_lint:
            success = audit_res.passed and lint_report.all_passed
        else:
            success = audit_res.passed

        return ContextSyncExecutionReport(
            target_file=str(target_file),
            audit_result=audit_res,
            clean_result=clean_res,
            sync_result=sync_res,
            lint_report=lint_report,
            success=success,
            duration_seconds=duration,
        )


__all__ = [
    "AuditResult",
    "CleanResult",
    "ContextSyncEngine",
    "ContextSyncExecutionReport",
    "ContextViolation",
    "LintCheckResult",
    "SyncResult",
    "SyncTargetRecord",
    "WorkspaceLintReport",
]
