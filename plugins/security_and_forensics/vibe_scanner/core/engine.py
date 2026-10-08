"""File and directory scanning engine with Rule 52 bounded traversal."""

from __future__ import annotations

import ast
import os
from pathlib import Path
import time
from typing import List, Optional, Set

from plugins.security_and_forensics.vibe_scanner.core.base import BaseDetector
from plugins.security_and_forensics.vibe_scanner.core.detectors import DETECTORS
from plugins.security_and_forensics.vibe_scanner.core.models import ScanReport, ScanResult


def scan_file(
    path: str, detectors: Optional[List[BaseDetector]] = None
) -> ScanResult:
    """Scan a single Python file with all detectors."""
    result = ScanResult(path=path)
    active_detectors = detectors or DETECTORS
    t0 = time.perf_counter()

    try:
        source = Path(path).read_text(encoding="utf-8", errors="replace")
        result.lines_scanned = source.count("\n") + 1
    except Exception:
        result.parse_error = True
        result.scan_ms = (time.perf_counter() - t0) * 1000
        return result

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        result.parse_error = True
        result.scan_ms = (time.perf_counter() - t0) * 1000
        return result

    for detector in active_detectors:
        try:
            findings = detector.detect(tree, source, path)
            result.findings.extend(findings)
        except Exception:
            pass  # never let a detector crash the scan

    result.scan_ms = (time.perf_counter() - t0) * 1000
    return result


def scan_directory(
    root: str,
    ignore_dirs: Optional[Set[str]] = None,
    max_depth: int = 8,
    detectors: Optional[List[BaseDetector]] = None,
) -> ScanReport:
    """Scan all .py files in a directory recursively with Rule 52 bounded depth."""
    ignore = ignore_dirs or {
        ".git", "__pycache__", ".venv", "venv", "env",
        "node_modules", ".mypy_cache", ".pytest_cache",
        "dist", "build", ".gemini", "target",
    }

    report = ScanReport(root=root)
    t0 = time.perf_counter()
    root_path = Path(root).resolve()

    py_files: List[str] = []
    for dirpath, dirnames, filenames in os.walk(str(root_path)):
        rel_parts = Path(dirpath).relative_to(root_path).parts
        if len(rel_parts) >= max_depth:
            dirnames.clear()
            continue

        dirnames[:] = [
            d for d in dirnames
            if d.lower() not in ignore and not d.startswith(".")
        ]
        for fname in filenames:
            if fname.endswith(".py"):
                py_files.append(os.path.join(dirpath, fname))

    for fpath in sorted(py_files):
        result = scan_file(fpath, detectors=detectors)
        report.results.append(result)

    report.total_ms = (time.perf_counter() - t0) * 1000
    return report


__all__ = [
    "scan_directory",
    "scan_file",
]
