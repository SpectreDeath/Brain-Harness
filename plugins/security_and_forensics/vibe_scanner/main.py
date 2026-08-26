"""Vibe Scanner plugin — AST-based AI code vulnerability detector & security auditing.

Detects common AI/vibe-coding anti-patterns and vulnerabilities:
  - SQL Injection (unparameterized f-strings, format, %)
  - Path Traversal & Unsafe File Access
  - Hardcoded API Keys, Passwords & Secrets
  - Unsafe Deserialization (pickle, yaml.load)
  - Weak Cryptography (MD5/SHA1 for auth, random() tokens)
  - Swallowed Exceptions (bare except, pass)
  - Tainted Input Validation & Flow
"""

from __future__ import annotations

import ast
import json
import os
import time
from pathlib import Path
from typing import Any

import structlog

from plugins.security_and_forensics.vibe_scanner.scanner_core import (
    DETECTORS,
    Finding,
    ScanReport,
    ScanResult,
    export_json,
    export_sarif,
    scan_directory as core_scan_directory,
    scan_file as core_scan_file,
)

logger = structlog.get_logger()


def _finding_to_dict(f: Finding) -> dict[str, Any]:
    """Serialize Finding dataclass to a normalized dictionary."""
    return {
        "file": f.file,
        "line": f.line,
        "detector": f.detector,
        "severity": f.severity,
        "title": f.title,
        "detail": f.detail,
        "code_snippet": f.code_snippet,
        "fix_hint": f.fix_hint,
    }


def _scan_result_to_dict(res: ScanResult) -> dict[str, Any]:
    """Serialize ScanResult to a normalized dictionary."""
    return {
        "path": res.path,
        "lines_scanned": res.lines_scanned,
        "parse_error": res.parse_error,
        "scan_ms": round(res.scan_ms, 3),
        "total_findings": len(res.findings),
        "critical_count": len(res.critical),
        "high_count": len(res.high),
        "clean": len(res.findings) == 0,
        "findings": [_finding_to_dict(f) for f in res.findings],
    }


def _scan_code_ast(code: str, file_name: str = "snippet.py") -> ScanResult:
    """Internal helper to scan in-memory code string via AST."""
    result = ScanResult(path=file_name)
    t0 = time.perf_counter()
    result.lines_scanned = code.count("\n") + 1

    try:
        tree = ast.parse(code, filename=file_name)
    except SyntaxError as err:
        result.parse_error = True
        result.scan_ms = (time.perf_counter() - t0) * 1000
        return result

    for detector in DETECTORS:
        try:
            findings = detector.detect(tree, code, file_name)
            result.findings.extend(findings)
        except Exception as exc:
            logger.debug("detector_error", detector=detector.__class__.__name__, error=str(exc))

    result.scan_ms = (time.perf_counter() - t0) * 1000
    return result


def scan_code(code: str, file_name: str = "snippet.py") -> dict[str, Any]:
    """Scan in-memory Python source code string for AI security vulnerabilities and anti-patterns.

    Args:
        code: Python source code string to analyze.
        file_name: Optional synthetic file name for context reporting.

    Returns:
        Dictionary containing scan results, findings breakdown, and fix hints.
    """
    if not code or not code.strip():
        return {
            "status": "ok",
            "clean": True,
            "total_findings": 0,
            "critical_count": 0,
            "high_count": 0,
            "findings": [],
            "lines_scanned": 0,
        }

    res = _scan_code_ast(code, file_name=file_name)
    if res.parse_error:
        return {
            "status": "error",
            "error": f"Failed to parse Python syntax for {file_name}",
            "clean": False,
            "total_findings": 0,
            "findings": [],
        }

    return {
        "status": "ok",
        **_scan_result_to_dict(res),
    }


def scan_file(file_path: str) -> dict[str, Any]:
    """Scan a single Python source file on disk for AST security vulnerabilities.

    Args:
        file_path: Absolute or relative path to the Python file.

    Returns:
        Dictionary containing file findings, severity breakdown, and actionable fix hints.
    """
    path_obj = Path(file_path)
    if not path_obj.exists() or not path_obj.is_file():
        return {
            "status": "error",
            "error": f"File not found or not a valid regular file: {file_path}",
            "clean": False,
            "total_findings": 0,
            "findings": [],
        }

    res = core_scan_file(str(path_obj))
    if res.parse_error:
        return {
            "status": "error",
            "error": f"Syntax error parsing Python file: {file_path}",
            "clean": False,
            "total_findings": 0,
            "findings": [],
        }

    return {
        "status": "ok",
        **_scan_result_to_dict(res),
    }


def scan_project(
    dir_path: str,
    ignore_dirs: list[str] | None = None,
    fail_on_critical: bool = False,
) -> dict[str, Any]:
    """Recursively scan a directory of Python files, skipping virtual environments and caches.

    Args:
        dir_path: Root directory path to scan.
        ignore_dirs: Optional list of directory names to ignore.
        fail_on_critical: If True, flags status as failed when critical vulnerabilities exist.

    Returns:
        Aggregated security report with metrics, findings per file, and severity counts.
    """
    root_path = Path(dir_path)
    if not root_path.exists() or not root_path.is_dir():
        return {
            "status": "error",
            "error": f"Directory not found: {dir_path}",
            "total_files_scanned": 0,
            "total_findings": 0,
            "findings": [],
        }

    ignore_set = set(ignore_dirs) if ignore_dirs else None
    report = core_scan_directory(str(root_path), ignore_dirs=ignore_set)

    all_findings_dicts = [_finding_to_dict(f) for f in report.all_findings]
    critical_count = len(report.by_severity.get("CRITICAL", []))
    high_count = len(report.by_severity.get("HIGH", []))
    medium_count = len(report.by_severity.get("MEDIUM", []))
    low_count = len(report.by_severity.get("LOW", []))

    passed = critical_count == 0 if fail_on_critical else True

    return {
        "status": "ok" if passed else "failed_critical",
        "passed": passed,
        "root": report.root,
        "total_files_scanned": len(report.results),
        "files_clean": report.files_clean,
        "files_vulnerable": report.files_vulnerable,
        "total_findings": len(all_findings_dicts),
        "critical_count": critical_count,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
        "total_ms": round(report.effective_ms, 3),
        "findings": all_findings_dicts,
        "results": [_scan_result_to_dict(r) for r in report.results],
    }


def compare_benchmark(vulnerable_code: str, secure_code: str) -> dict[str, Any]:
    """Compare vulnerable code against remediated/secure code to verify risk reduction.

    Args:
        vulnerable_code: Source code prior to security remediation.
        secure_code: Remediated source code after applying fix hints.

    Returns:
        Side-by-side benchmark comparison metrics, resolved findings, and risk reduction percentage.
    """
    vuln_res = _scan_code_ast(vulnerable_code, file_name="vulnerable.py")
    sec_res = _scan_code_ast(secure_code, file_name="secure.py")

    vuln_count = len(vuln_res.findings)
    sec_count = len(sec_res.findings)
    reduction = 100.0 if vuln_count > 0 and sec_count == 0 else (
        round(((vuln_count - sec_count) / vuln_count) * 100.0, 2) if vuln_count > 0 else 0.0
    )

    return {
        "status": "ok",
        "vulnerable": {
            "total_findings": vuln_count,
            "critical": len(vuln_res.critical),
            "high": len(vuln_res.high),
            "findings": [_finding_to_dict(f) for f in vuln_res.findings],
        },
        "secure": {
            "total_findings": sec_count,
            "critical": len(sec_res.critical),
            "high": len(sec_res.high),
            "findings": [_finding_to_dict(f) for f in sec_res.findings],
        },
        "findings_eliminated": max(0, vuln_count - sec_count),
        "risk_reduction_pct": reduction,
        "fully_remediated": sec_count == 0,
    }


def generate_sarif_report(dir_path: str, output_path: str) -> dict[str, Any]:
    """Scan a project directory and export a standard SARIF v2.1.0 security report.

    Args:
        dir_path: Root project directory to scan.
        output_path: Target path to write the SARIF json file.

    Returns:
        Status and metadata for the generated SARIF artifact.
    """
    root_path = Path(dir_path)
    if not root_path.exists() or not root_path.is_dir():
        return {"status": "error", "error": f"Directory not found: {dir_path}"}

    report = core_scan_directory(str(root_path))
    export_sarif(report, output_path)

    return {
        "status": "ok",
        "output_path": str(Path(output_path).resolve()),
        "total_findings": len(report.all_findings),
        "critical_count": len(report.by_severity.get("CRITICAL", [])),
        "sarif_version": "2.1.0",
    }


def generate_json_report(dir_path: str, output_path: str) -> dict[str, Any]:
    """Scan a project directory and export a structured JSON security report.

    Args:
        dir_path: Root project directory to scan.
        output_path: Target path to write the JSON findings file.

    Returns:
        Status and metadata for the generated JSON file.
    """
    root_path = Path(dir_path)
    if not root_path.exists() or not root_path.is_dir():
        return {"status": "error", "error": f"Directory not found: {dir_path}"}

    report = core_scan_directory(str(root_path))
    export_json(report, output_path)

    return {
        "status": "ok",
        "output_path": str(Path(output_path).resolve()),
        "total_findings": len(report.all_findings),
        "total_files_scanned": len(report.results),
    }


class VibeScannerService:
    """Service class for in-process or kernel lifecycle integration."""

    def scan_code(self, code: str, file_name: str = "snippet.py") -> dict[str, Any]:
        return scan_code(code, file_name=file_name)

    def scan_file(self, file_path: str) -> dict[str, Any]:
        return scan_file(file_path)

    def scan_project(
        self,
        dir_path: str,
        ignore_dirs: list[str] | None = None,
        fail_on_critical: bool = False,
    ) -> dict[str, Any]:
        return scan_project(dir_path, ignore_dirs=ignore_dirs, fail_on_critical=fail_on_critical)

    def compare_benchmark(self, vulnerable_code: str, secure_code: str) -> dict[str, Any]:
        return compare_benchmark(vulnerable_code, secure_code)

    def generate_sarif(self, dir_path: str, output_path: str) -> dict[str, Any]:
        return generate_sarif_report(dir_path, output_path)

    def generate_json(self, dir_path: str, output_path: str) -> dict[str, Any]:
        return generate_json_report(dir_path, output_path)
