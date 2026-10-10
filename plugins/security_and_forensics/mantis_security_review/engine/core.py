"""MantisReviewEngine coordinator class implementing Mantis security algorithms."""

from __future__ import annotations

from typing import Any
import structlog

from plugins.security_and_forensics.mantis_security_review.engine.auditor import (
    plan_review,
    research_audit,
)
from plugins.security_and_forensics.mantis_security_review.engine.chains import (
    calibrate_risk,
    chain_exploits,
)
from plugins.security_and_forensics.mantis_security_review.engine.db import init_okf_db
from plugins.security_and_forensics.mantis_security_review.engine.reporter import generate_report
from plugins.security_and_forensics.mantis_security_review.engine.triage import (
    critic_filter,
    dedupe_ladder,
    review_gate,
)
from plugins.security_and_forensics.mantis_security_review.engine.vcs import (
    directory_summary,
    history_scan,
)

logger = structlog.get_logger(__name__)


class MantisReviewEngine:
    """Standalone implementation of Mantis Review algorithms."""

    def __init__(self, db_path: str = "knowledge.db") -> None:
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self) -> None:
        try:
            conn = init_okf_db(self.db_path)
            conn.close()
        except Exception as e:
            logger.warning("okf_db_init_skipped", error=str(e))

    def history_scan(
        self, repo_path: str, max_commits: int = 100, pattern_filter: str = ""
    ) -> dict[str, Any]:
        """Mine VCS repository history for historical vulnerabilities and security fixes."""
        return history_scan(repo_path, max_commits=max_commits, pattern_filter=pattern_filter)

    def directory_summary(self, dir_path: str, recursive: bool = True) -> dict[str, Any]:
        """Generate hierarchical security directory map."""
        return directory_summary(dir_path, recursive=recursive)

    def plan_review(
        self,
        threat_model: dict[str, Any],
        target_paths: list[str],
        focus_cwe: list[str] | None = None,
    ) -> dict[str, Any]:
        """Formulate targeted security review plan."""
        return plan_review(threat_model, target_paths, focus_cwe=focus_cwe)

    def research_audit(
        self,
        target_file: str,
        code_content: str,
        focus_cwe: list[str] | None = None,
    ) -> dict[str, Any]:
        """Deep-dive static analysis audit of target source code."""
        return research_audit(target_file, code_content, focus_cwe=focus_cwe)

    def dedupe_ladder(
        self, findings: list[dict[str, Any]], mode: str = "syntactic_and_ast"
    ) -> dict[str, Any]:
        """Consolidate findings to eliminate redundant reports."""
        return dedupe_ladder(findings, mode=mode)

    def review_gate(
        self, finding: dict[str, Any], source_content: str, strictness: str = "high"
    ) -> dict[str, Any]:
        """Evaluate finding against source semantics to eliminate false positives."""
        return review_gate(finding, source_content, strictness=strictness)

    def critic_filter(
        self, finding: dict[str, Any], check_release_assertions: bool = True
    ) -> dict[str, Any]:
        """Assess production viability, filtering out debug-only features and assertion traps."""
        return critic_filter(finding, check_release_assertions=check_release_assertions)

    def chain_exploits(
        self, findings: list[dict[str, Any]], target_objective: str = ""
    ) -> dict[str, Any]:
        """Construct multi-stage compound exploit chains from validated findings."""
        return chain_exploits(findings, target_objective=target_objective)

    def calibrate_risk(
        self, findings: list[dict[str, Any]], asset_criticality: str = "high"
    ) -> dict[str, Any]:
        """Calculate multi-axis risk ratings."""
        return calibrate_risk(findings, asset_criticality=asset_criticality)

    def generate_report(
        self,
        findings: list[dict[str, Any]],
        exploit_chains: list[dict[str, Any]] | None = None,
        executive_summary: str = "",
    ) -> dict[str, Any]:
        """Compile stakeholder-facing security review packet."""
        return generate_report(
            findings, exploit_chains=exploit_chains, executive_summary=executive_summary
        )
