#!/usr/bin/env python3
"""
run-devskim.py - Pre-commit Multi-File Dispatcher & Security Gate

Bridges pre-commit's argument-appending behavior by delegating to the
authoritative PreCommitSecurityGuardEngine. Scans all passed staged files
for SAST vulnerabilities and secret leaks, failing with Exit 1 if any
security violations are discovered.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Ensure co-located script directory is on sys.path
_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

try:
    from pre_commit_security_engine import PreCommitSecurityGuardEngine
except ImportError:
    # Fallback to direct parent discovery
    from .pre_commit_security_engine import PreCommitSecurityGuardEngine


def main() -> None:
    """Entrypoint for pre-commit multi-file hook execution."""
    files_to_scan = sys.argv[1:]

    if not files_to_scan:
        sys.exit(0)

    engine = PreCommitSecurityGuardEngine()
    report = engine.scan_files(files_to_scan)

    if not report.passed:
        for finding in report.findings:
            if finding.severity in ("critical", "high"):
                print(
                    f"[{finding.severity.upper()}] {finding.file_path}:{finding.line_number or 1} "
                    f"- {finding.name} ({finding.rule_id})",
                    file=sys.stderr,
                )
                if finding.message:
                    print(f"  Message: {finding.message}", file=sys.stderr)
                if finding.remediation:
                    print(f"  Remediation: {finding.remediation}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
