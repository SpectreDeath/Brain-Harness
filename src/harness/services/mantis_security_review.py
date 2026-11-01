"""Mantis Autonomous Security Review & Triage Service protocol, models, and single-seam resolver."""

from __future__ import annotations

import sys
from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from plugins.security_and_forensics.mantis_security_review.engine.models import (
    MANTIS_SECURITY_REVIEW_KEY,
    ExploitChain,
    ExploitStep,
    MantisFinding,
    MantisSecurityReviewService,
)

logger = structlog.get_logger(__name__)


class MantisSecurityReviewAdapter(MantisSecurityReviewService):
    """Rule 58 Adapter for MantisSecurityReviewService handling SandboxedPlugin and test mocks."""

    def __init__(self, provider: Any) -> None:
        self._provider = provider

    def history_scan(self, repo_path: str, max_commits: int = 100, pattern_filter: str = "") -> dict[str, Any]:
        if hasattr(self._provider, "history_scan"):
            return self._provider.history_scan(repo_path, max_commits, pattern_filter)
        if hasattr(self._provider, "invoke_sync"):
            return self._provider.invoke_sync("mantis_history_scan", {"repo_path": repo_path, "max_commits": max_commits, "pattern_filter": pattern_filter})
        from plugins.security_and_forensics.mantis_security_review.engine import history_scan
        return history_scan(repo_path, max_commits, pattern_filter)

    def directory_summary(self, dir_path: str, recursive: bool = True) -> dict[str, Any]:
        if hasattr(self._provider, "directory_summary"):
            return self._provider.directory_summary(dir_path, recursive)
        from plugins.security_and_forensics.mantis_security_review.engine import directory_summary
        return directory_summary(dir_path, recursive)

    def plan_review(self, threat_model: dict[str, Any], target_paths: list[str], focus_cwe: list[str] | None = None) -> dict[str, Any]:
        if hasattr(self._provider, "plan_review"):
            return self._provider.plan_review(threat_model, target_paths, focus_cwe)
        from plugins.security_and_forensics.mantis_security_review.engine import plan_review
        return plan_review(threat_model, target_paths, focus_cwe)

    def research_audit(self, target_file: str, code_content: str, focus_cwe: list[str] | None = None) -> dict[str, Any]:
        if hasattr(self._provider, "research_audit"):
            return self._provider.research_audit(target_file, code_content, focus_cwe)
        from plugins.security_and_forensics.mantis_security_review.engine import research_audit
        return research_audit(target_file, code_content, focus_cwe)

    def dedupe_ladder(self, findings: list[dict[str, Any]], mode: str = "syntactic_and_ast") -> dict[str, Any]:
        if hasattr(self._provider, "dedupe_ladder"):
            return self._provider.dedupe_ladder(findings, mode)
        from plugins.security_and_forensics.mantis_security_review.engine import dedupe_ladder
        return dedupe_ladder(findings, mode)

    def review_gate(self, finding: dict[str, Any], source_content: str, strictness: str = "high") -> dict[str, Any]:
        if hasattr(self._provider, "review_gate"):
            return self._provider.review_gate(finding, source_content, strictness)
        from plugins.security_and_forensics.mantis_security_review.engine import review_gate
        return review_gate(finding, source_content, strictness)

    def critic_filter(self, finding: dict[str, Any], check_release_assertions: bool = True) -> dict[str, Any]:
        if hasattr(self._provider, "critic_filter"):
            return self._provider.critic_filter(finding, check_release_assertions)
        from plugins.security_and_forensics.mantis_security_review.engine import critic_filter
        return critic_filter(finding, check_release_assertions)

    def chain_exploits(self, findings: list[dict[str, Any]], target_objective: str = "") -> dict[str, Any]:
        if hasattr(self._provider, "chain_exploits"):
            return self._provider.chain_exploits(findings, target_objective)
        from plugins.security_and_forensics.mantis_security_review.engine import chain_exploits
        return chain_exploits(findings, target_objective)

    def calibrate_risk(self, findings: list[dict[str, Any]], asset_criticality: str = "high") -> dict[str, Any]:
        if hasattr(self._provider, "calibrate_risk"):
            return self._provider.calibrate_risk(findings, asset_criticality)
        from plugins.security_and_forensics.mantis_security_review.engine import calibrate_risk
        return calibrate_risk(findings, asset_criticality)

    def generate_report(self, findings: list[dict[str, Any]], exploit_chains: list[dict[str, Any]] | None = None, executive_summary: str = "") -> dict[str, Any]:
        if hasattr(self._provider, "generate_report"):
            return self._provider.generate_report(findings, exploit_chains, executive_summary)
        from plugins.security_and_forensics.mantis_security_review.engine import generate_report
        return generate_report(findings, exploit_chains, executive_summary)


def resolve_mantis_security_review(target: Any = None) -> MantisSecurityReviewService:
    """Resolve MantisSecurityReviewService from context, object, or fallback singleton (Rule 58)."""
    from plugins.security_and_forensics.mantis_security_review.engine.resolvers import (
        resolve_mantis_security_review as _engine_resolve,
    )

    resolved = _engine_resolve(target)
    if isinstance(resolved, MantisSecurityReviewService):
        return resolved
    return MantisSecurityReviewAdapter(resolved)


__all__ = [
    "MANTIS_SECURITY_REVIEW_KEY",
    "MantisSecurityReviewService",
    "MantisSecurityReviewAdapter",
    "MantisFinding",
    "ExploitChain",
    "ExploitStep",
    "resolve_mantis_security_review",
]

