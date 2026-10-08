"""AI Blind Spot Scanner — 100% backward-compatible facade (decomposed).

Delegates to specialized core submodules in plugins.security_and_forensics.vibe_scanner.core.
"""

from __future__ import annotations

import sys
from pathlib import Path

from plugins.security_and_forensics.vibe_scanner.core import (
    DETECTORS,
    BaseDetector,
    ExceptionSwallowedDetector,
    Finding,
    HardcodedSecretDetector,
    InputValidationDetector,
    SQLInjectionDetector,
    SEVERITY_ICON,
    SEVERITY_ORDER,
    ScanReport,
    ScanResult,
    UnsafeDeserialiseDetector,
    UnsafeFileAccessDetector,
    WeakCryptoDetector,
    export_json,
    export_sarif,
    print_report,
    scan_directory,
    scan_file,
)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="AI Blind Spot Scanner — catches what vibe coding misses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scanner.py ./my-project
  python scanner.py ./my-project --verbose
  python scanner.py ./my-project --json report.json
  python scanner.py ./my-project --sarif report.sarif
  python scanner.py ./my-project --fail-on-critical
  python scanner.py ./my-project --fail-on HIGH

CI/CD usage (exits with code 1 if CRITICAL findings exist):
  python scanner.py ./src --fail-on-critical

GitHub code scanning (upload SARIF results):
  python scanner.py ./src --sarif results.sarif
  gh code-scanning upload-results --sarif results.sarif
        """,
    )
    parser.add_argument("path", help="Directory or file to scan")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show code snippets and fix hints")
    parser.add_argument("--json", metavar="FILE",
                        help="Export findings as JSON")
    parser.add_argument("--sarif", metavar="FILE",
                        help="Export findings as SARIF 2.1.0 (for GitHub code scanning)")
    parser.add_argument("--fail-on-critical", action="store_true",
                        help="Exit with code 1 if any CRITICAL findings exist (CI/CD use)")
    parser.add_argument("--fail-on", metavar="SEVERITY",
                        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                        help="Exit with code 1 if findings at this severity or above")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"ERROR: path does not exist: {args.path}")
        sys.exit(1)

    if target.is_file():
        result = scan_file(str(target))
        report = ScanReport(root=str(target.parent), results=[result])
    else:
        report = scan_directory(str(target))

    print_report(report, verbose=args.verbose)

    if args.json:
        export_json(report, args.json)

    if args.sarif:
        export_sarif(report, args.sarif)

    # --fail-on-critical shortcut
    if args.fail_on_critical:
        has_critical = any(
            f.severity == "CRITICAL"
            for f in report.all_findings
        )
        if has_critical:
            sys.exit(1)

    # --fail-on SEVERITY
    if args.fail_on:
        threshold = SEVERITY_ORDER[args.fail_on]
        has_blocking = any(
            SEVERITY_ORDER.get(f.severity, 99) <= threshold
            for f in report.all_findings
        )
        if has_blocking:
            sys.exit(1)


if __name__ == "__main__":
    main()

__all__ = [
    "DETECTORS",
    "BaseDetector",
    "ExceptionSwallowedDetector",
    "Finding",
    "HardcodedSecretDetector",
    "InputValidationDetector",
    "SQLInjectionDetector",
    "SEVERITY_ICON",
    "SEVERITY_ORDER",
    "ScanReport",
    "ScanResult",
    "UnsafeDeserialiseDetector",
    "UnsafeFileAccessDetector",
    "WeakCryptoDetector",
    "export_json",
    "export_sarif",
    "main",
    "print_report",
    "scan_directory",
    "scan_file",
]
