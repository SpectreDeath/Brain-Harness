"""Tool entrypoints matching plugin.json specification for Mantis security review."""

from __future__ import annotations

from typing import Any

from plugins.security_and_forensics.mantis_security_review.engine.core import MantisReviewEngine

_GLOBAL_ENGINE = MantisReviewEngine()


def mantis_history_scan(
    repo_path: str, max_commits: int = 100, pattern_filter: str = ""
) -> dict[str, Any]:
    """Mine VCS repository history for historical vulnerabilities and fix patterns."""
    return _GLOBAL_ENGINE.history_scan(
        repo_path=repo_path, max_commits=max_commits, pattern_filter=pattern_filter
    )


def mantis_directory_summary(dir_path: str, recursive: bool = True) -> dict[str, Any]:
    """Generate hierarchical security directory map and asset overview."""
    return _GLOBAL_ENGINE.directory_summary(dir_path=dir_path, recursive=recursive)


def mantis_plan_review(
    threat_model: dict[str, Any],
    target_paths: list[str],
    focus_cwe: list[str] | None = None,
) -> dict[str, Any]:
    """Formulate targeted defensive security review plan from threat model."""
    return _GLOBAL_ENGINE.plan_review(
        threat_model=threat_model, target_paths=target_paths, focus_cwe=focus_cwe or []
    )


def mantis_research_audit(
    target_file: str, code_content: str, focus_cwe: list[str] | None = None
) -> dict[str, Any]:
    """Deep-dive static analysis audit of target source code."""
    return _GLOBAL_ENGINE.research_audit(
        target_file=target_file, code_content=code_content, focus_cwe=focus_cwe or []
    )


def mantis_dedupe_ladder(
    findings: list[dict[str, Any]], mode: str = "syntactic_and_ast"
) -> dict[str, Any]:
    """Consolidate findings through multi-pass syntactic, AST, and semantic deduplication."""
    return _GLOBAL_ENGINE.dedupe_ladder(findings=findings, mode=mode)


def mantis_review_gate(
    finding: dict[str, Any], source_content: str, strictness: str = "high"
) -> dict[str, Any]:
    """Independent validation gate evaluating findings against source semantics."""
    return _GLOBAL_ENGINE.review_gate(
        finding=finding, source_content=source_content, strictness=strictness
    )


def mantis_critic_filter(
    finding: dict[str, Any], check_release_assertions: bool = True
) -> dict[str, Any]:
    """Assess production viability, filtering out debug-only features and assertion traps."""
    return _GLOBAL_ENGINE.critic_filter(
        finding=finding, check_release_assertions=check_release_assertions
    )


def mantis_chain_exploits(
    findings: list[dict[str, Any]], target_objective: str = ""
) -> dict[str, Any]:
    """Analyze individual findings to construct multi-stage compound exploit chains."""
    return _GLOBAL_ENGINE.chain_exploits(
        findings=findings, target_objective=target_objective
    )


def mantis_calibrate_risk(
    findings: list[dict[str, Any]], asset_criticality: str = "high"
) -> dict[str, Any]:
    """Calculate multi-axis risk ratings based on threat intel, impact, and criticality."""
    return _GLOBAL_ENGINE.calibrate_risk(
        findings=findings, asset_criticality=asset_criticality
    )


def mantis_generate_report(
    findings: list[dict[str, Any]],
    exploit_chains: list[dict[str, Any]] | None = None,
    executive_summary: str = "",
) -> dict[str, Any]:
    """Compile stakeholder-facing security review packet from confirmed findings."""
    return _GLOBAL_ENGINE.generate_report(
        findings=findings,
        exploit_chains=exploit_chains or [],
        executive_summary=executive_summary,
    )
