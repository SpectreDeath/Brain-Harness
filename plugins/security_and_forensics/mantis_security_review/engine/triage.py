"""Deduplication ladder, semantic review gate, and release viability critic."""

from __future__ import annotations

from typing import Any

from plugins.security_and_forensics.mantis_security_review.engine.db import compute_stable_signature


def dedupe_ladder(
    findings: list[dict[str, Any]], mode: str = "syntactic_and_ast"
) -> dict[str, Any]:
    """Consolidate findings to eliminate redundant reports."""
    if mode == "off":
        return {
            "status": "ok",
            "mode": "off",
            "original_count": len(findings),
            "deduped_count": len(findings),
            "findings": findings,
        }

    seen_signatures: set[str] = set()
    seen_locations: set[tuple[str, int, str]] = set()
    deduped: list[dict[str, Any]] = []
    duplicates_removed = 0

    for f in findings:
        fp = f.get("filepath", "")
        line = f.get("line", 0)
        cwe = f.get("cwe", "")
        sig = f.get("signature") or compute_stable_signature(fp, cwe, f.get("target_symbol", ""))

        if sig in seen_signatures:
            duplicates_removed += 1
            continue

        loc_key = (fp, line, cwe)
        if loc_key in seen_locations:
            duplicates_removed += 1
            continue

        seen_signatures.add(sig)
        seen_locations.add(loc_key)
        f_copy = dict(f)
        f_copy["signature"] = sig
        deduped.append(f_copy)

    return {
        "status": "ok",
        "mode": mode,
        "original_count": len(findings),
        "deduped_count": len(deduped),
        "duplicates_removed": duplicates_removed,
        "findings": deduped,
    }


def review_gate(
    finding: dict[str, Any], source_content: str, strictness: str = "high"
) -> dict[str, Any]:
    """Evaluate finding against source semantics to eliminate false positives."""
    line_num = finding.get("line", 0)
    cwe = finding.get("cwe", "")
    lines = source_content.splitlines()

    if line_num <= 0 or line_num > len(lines):
        return {
            "status": "ok",
            "verdict": "REJECTED",
            "confidence": 0.95,
            "reason": f"Target line {line_num} does not exist in source file (total lines: {len(lines)}).",
        }

    target_line = lines[line_num - 1]
    context_window = lines[max(0, line_num - 5):min(len(lines), line_num + 5)]
    context_str = "\n".join(context_window)

    has_sanitizer = any(
        term in context_str.lower()
        for term in ["shlex.quote", "escape", "parameterized", "validate", "sanitize", "allowed_hosts"]
    )
    if has_sanitizer:
        return {
            "status": "ok",
            "verdict": "REJECTED_FALSE_POSITIVE",
            "confidence": 0.85,
            "reason": "Surrounding context contains explicit sanitization or input validation.",
        }

    return {
        "status": "ok",
        "verdict": "CONFIRMED_VALID",
        "confidence": 0.90 if strictness == "high" else 0.75,
        "target_snippet": target_line.strip(),
        "reason": f"Vulnerability {cwe} confirmed on line {line_num} without detected sanitizers.",
    }


def critic_filter(
    finding: dict[str, Any], check_release_assertions: bool = True
) -> dict[str, Any]:
    """Assess production viability, filtering out debug-only features and assertion traps."""
    desc = (finding.get("description", "") + " " + finding.get("title", "")).lower()

    if check_release_assertions and ("assert " in desc or "assertion" in desc):
        return {
            "status": "ok",
            "viable_in_production": False,
            "verdict": "DROPPED_ASSERTION_TRAP",
            "reason": "Vulnerability relies on python 'assert' statement which is stripped in release builds (PYTHONOPTIMIZE / -O).",
        }

    if "debug" in desc or "test_" in finding.get("filepath", ""):
        return {
            "status": "ok",
            "viable_in_production": False,
            "verdict": "DROPPED_TEST_OR_DEBUG_ONLY",
            "reason": "Finding located in test harness or debug-only module not reachable in production.",
        }

    return {
        "status": "ok",
        "viable_in_production": True,
        "verdict": "CONFIRMED_PRODUCTION_VIABLE",
        "reason": "Vulnerability triggerable in production release configuration without assertions.",
    }
