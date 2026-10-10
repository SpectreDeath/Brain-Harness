"""Compound exploit chaining and multi-axis risk calibration."""

from __future__ import annotations

import hashlib
from typing import Any


def chain_exploits(
    findings: list[dict[str, Any]], target_objective: str = ""
) -> dict[str, Any]:
    """Construct multi-stage compound exploit chains from validated findings."""
    target_obj = target_objective or "Remote Code Execution / Privilege Escalation"
    chains: list[dict[str, Any]] = []

    info_leaks = [f for f in findings if f.get("cwe") in ("CWE-798", "CWE-200", "CWE-918")]
    rce_vulns = [f for f in findings if f.get("cwe") in ("CWE-78", "CWE-95", "CWE-502")]

    if info_leaks and rce_vulns:
        chains.append({
            "chain_id": f"chain_{hashlib.sha256(str(findings).encode()).hexdigest()[:8]}",
            "objective": target_obj,
            "steps": [
                {
                    "step": 1,
                    "finding_id": info_leaks[0].get("id"),
                    "tactic": "Credential Exfiltration / SSRF",
                    "description": f"Exfiltrate credentials or bypass network boundary via {info_leaks[0].get('title')}",
                },
                {
                    "step": 2,
                    "finding_id": rce_vulns[0].get("id"),
                    "tactic": "Privileged Code Execution",
                    "description": f"Use obtained access to execute arbitrary commands via {rce_vulns[0].get('title')}",
                },
            ],
            "compound_severity": "critical",
        })

    return {
        "status": "ok",
        "target_objective": target_obj,
        "chains_constructed_count": len(chains),
        "exploit_chains": chains,
    }


def calibrate_risk(
    findings: list[dict[str, Any]], asset_criticality: str = "high"
) -> dict[str, Any]:
    """Calculate multi-axis risk ratings."""
    crit_multiplier = {
        "critical": 1.5, "high": 1.2, "medium": 1.0, "low": 0.7
    }.get(asset_criticality.lower(), 1.0)
    calibrated: list[dict[str, Any]] = []

    for f in findings:
        sev = f.get("severity", "medium").lower()
        base_score = {"critical": 9.5, "high": 7.5, "medium": 5.0, "low": 2.5}.get(sev, 5.0)
        final_score = min(10.0, round(base_score * crit_multiplier, 1))

        calibrated.append({
            "finding_id": f.get("id"),
            "title": f.get("title"),
            "cwe": f.get("cwe"),
            "base_severity": sev,
            "asset_criticality": asset_criticality,
            "calibrated_cvss_score": final_score,
            "calibrated_severity": (
                "critical" if final_score >= 9.0
                else "high" if final_score >= 7.0
                else "medium" if final_score >= 4.0
                else "low"
            ),
        })

    return {
        "status": "ok",
        "asset_criticality": asset_criticality,
        "calibrated_findings_count": len(calibrated),
        "calibrated_findings": calibrated,
    }
