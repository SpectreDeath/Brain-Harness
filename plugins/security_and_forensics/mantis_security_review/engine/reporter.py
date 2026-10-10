"""Stakeholder-facing security report and markdown packet generation."""

from __future__ import annotations

from typing import Any


def generate_report(
    findings: list[dict[str, Any]],
    exploit_chains: list[dict[str, Any]] | None = None,
    executive_summary: str = "",
) -> dict[str, Any]:
    """Compile stakeholder-facing security review packet."""
    exploit_chains = exploit_chains or []
    summary = (
        executive_summary
        or f"Automated Mantis security review identified {len(findings)} confirmed issues and {len(exploit_chains)} compound exploit chains."
    )

    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        s = f.get("severity", f.get("calibrated_severity", "medium")).lower()
        if s in counts:
            counts[s] += 1

    markdown_report = [
        "# Google Mantis Security Review Packet",
        "",
        "## Executive Summary",
        summary,
        "",
        "## Severity Breakdown",
        f"- **Critical:** {counts['critical']}",
        f"- **High:** {counts['high']}",
        f"- **Medium:** {counts['medium']}",
        f"- **Low:** {counts['low']}",
        "",
        "## Confirmed Findings",
    ]

    for i, f in enumerate(findings, start=1):
        markdown_report.extend([
            f"### {i}. {f.get('title', 'Unknown')} ({f.get('cwe', 'CWE-Unknown')})",
            f"- **File:** `{f.get('filepath', '')}` (Line {f.get('line', '?')})",
            f"- **Severity:** {f.get('severity', f.get('calibrated_severity', 'medium')).upper()}",
            f"- **Description:** {f.get('description', '')}",
            "",
        ])

    if exploit_chains:
        markdown_report.extend(["## Compound Exploit Chains"])
        for ch in exploit_chains:
            markdown_report.extend([
                f"### Chain: {ch.get('objective', '')}",
                f"- **Severity:** {ch.get('compound_severity', 'critical').upper()}",
            ])
            for step in ch.get("steps", []):
                markdown_report.append(
                    f"  {step.get('step')}. **{step.get('tactic')}:** {step.get('description')}"
                )
            markdown_report.append("")

    return {
        "status": "ok",
        "findings_count": len(findings),
        "chains_count": len(exploit_chains),
        "severity_counts": counts,
        "markdown_report": "\n".join(markdown_report),
    }
