"""Terminal, JSON, and SARIF 2.1.0 reporting formatting."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict

from plugins.security_and_forensics.vibe_scanner.core.models import ScanReport

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
SEVERITY_ICON = {
    "CRITICAL": "🔴",
    "HIGH":     "🟠",
    "MEDIUM":   "🟡",
    "LOW":      "🔵",
}


def print_report(report: ScanReport, verbose: bool = False) -> None:
    width = 72
    print("\n" + "═" * width)
    print("  AI BLIND SPOT SCANNER")
    print(f"  Root: {report.root}")
    print("═" * width)

    all_findings = report.all_findings
    by_sev = report.by_severity

    # Summary
    total_files = len(report.results)
    total_findings = len(all_findings)
    critical = len(by_sev.get("CRITICAL", []))
    high = len(by_sev.get("HIGH", []))
    medium = len(by_sev.get("MEDIUM", []))

    print(f"\n  Files scanned : {total_files}")
    print(f"  Files clean   : {report.files_clean}")
    print(f"  Files flagged : {report.files_vulnerable}")
    print(f"  Total findings: {total_findings}")
    print(f"  🔴 CRITICAL   : {critical}")
    print(f"  🟠 HIGH       : {high}")
    print(f"  🟡 MEDIUM     : {medium}")
    real_ms = report.effective_ms
    scan_time_str = f"{real_ms:.1f}ms"
    print(f"  Scan time     : {scan_time_str}")

    # By detector
    print(f"\n{'─' * width}")
    print("  BY DETECTOR")
    print(f"{'─' * width}")
    print(f"  {'Detector':<25} {'Findings':>8}  Description")
    for det_name, findings in sorted(
        report.by_detector.items(),
        key=lambda x: len(x[1]), reverse=True
    ):
        icon = SEVERITY_ICON.get(findings[0].severity, "  ")
        print(f"  {det_name:<25} {len(findings):>8}  {icon}")

    # Findings
    if all_findings:
        print(f"\n{'─' * width}")
        print("  FINDINGS (sorted by severity)")
        print(f"{'─' * width}")

        sorted_findings = sorted(
            all_findings,
            key=lambda f: (SEVERITY_ORDER.get(f.severity, 99), f.file, f.line)
        )

        for f in sorted_findings:
            icon = SEVERITY_ICON.get(f.severity, "  ")
            rel_path = os.path.relpath(f.file, report.root)
            print(f"\n  {icon} [{f.severity}] {f.detector}")
            print(f"     File   : {rel_path}:{f.line}")
            print(f"     Issue  : {f.title}")
            if verbose:
                print(f"     Detail : {f.detail}")
                if f.code_snippet:
                    print("     Code   :")
                    for line in f.code_snippet.splitlines():
                        print(f"              {line}")
                if f.fix_hint:
                    print(f"     Fix    : {f.fix_hint}")

    print(f"\n{'═' * width}")
    if critical > 0:
        print(f"  ⛔  {critical} CRITICAL finding(s) — fix before shipping.")
    elif high > 0:
        print(f"  ⚠️   {high} HIGH finding(s) — review before shipping.")
    elif total_findings == 0:
        print("  ✅  No findings. Clean scan.")
    else:
        print(f"  ℹ️   {medium} MEDIUM finding(s) — low risk but worth reviewing.")
    print("═" * width + "\n")


def export_json(report: ScanReport, output_path: str) -> None:
    """Export report as JSON for CI integration."""
    data = {
        "root": report.root,
        "total_ms": round(report.total_ms, 2),
        "summary": {
            "files_scanned": len(report.results),
            "files_clean": report.files_clean,
            "files_vulnerable": report.files_vulnerable,
            "total_findings": len(report.all_findings),
            "by_severity": {
                sev: len(findings)
                for sev, findings in report.by_severity.items()
            },
        },
        "findings": [
            {
                "file": os.path.relpath(f.file, report.root),
                "line": f.line,
                "detector": f.detector,
                "severity": f.severity,
                "title": f.title,
                "detail": f.detail,
                "fix_hint": f.fix_hint,
            }
            for f in sorted(
                report.all_findings,
                key=lambda f: (SEVERITY_ORDER.get(f.severity, 99), f.file, f.line)
            )
        ],
    }
    Path(output_path).write_text(json.dumps(data, indent=2))
    print(f"JSON report written to: {output_path}")


def export_sarif(report: ScanReport, output_path: str) -> None:
    """
    Export findings as SARIF 2.1.0 for GitHub code scanning.
    Upload to GitHub via: gh code-scanning upload-results --sarif report.sarif
    """
    rules = []
    seen_rules = set()
    results = []

    for f in report.all_findings:
        rule_id = f.detector
        if rule_id not in seen_rules:
            seen_rules.add(rule_id)
            rules.append({
                "id": rule_id,
                "name": rule_id,
                "shortDescription": {"text": f.title},
                "fullDescription": {"text": f.detail},
                "properties": {
                    "tags": ["security", "ai-generated-code"],
                    "severity": f.severity.lower(),
                },
            })

        # SARIF severity mapping
        sarif_level = {
            "CRITICAL": "error",
            "HIGH": "error",
            "MEDIUM": "warning",
            "LOW": "note",
        }.get(f.severity, "warning")

        rel_path = os.path.relpath(f.file, report.root).replace("\\", "/")

        results.append({
            "ruleId": rule_id,
            "level": sarif_level,
            "message": {"text": f"{f.title}. {f.detail}"},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": rel_path,
                        "uriBaseId": "%SRCROOT%",
                    },
                    "region": {
                        "startLine": f.line,
                    },
                }
            }],
            "fixes": [{
                "description": {"text": f.fix_hint},
            }] if f.fix_hint else [],
        })

    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "AI Blind Spot Scanner",
                    "version": "1.0.0",
                    "informationUri": "https://github.com/Emmimal/vibe-scanner/",
                    "rules": rules,
                }
            },
            "results": results,
            "artifacts": [
                {
                    "location": {
                        "uri": os.path.relpath(r.path, report.root).replace("\\", "/"),
                        "uriBaseId": "%SRCROOT%",
                    }
                }
                for r in report.results
            ],
        }],
    }

    Path(output_path).write_text(json.dumps(sarif, indent=2))
    print(f"SARIF report written to: {output_path}")




__all__ = [
    "SEVERITY_ICON",
    "SEVERITY_ORDER",
    "export_json",
    "export_sarif",
    "print_report",
]
