"""Google Mantis Autonomous Security Review & Triage Plugin for Brain Harness."""

from __future__ import annotations

from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from plugins.security_and_forensics.mantis_security_review.engine import (
    MANTIS_SECURITY_REVIEW_KEY,
    ExploitChain,
    ExploitStep,
    MantisFinding,
    MantisReviewEngine,
    MantisSecurityReviewService,
    calibrate_risk,
    chain_exploits,
    compute_stable_signature,
    critic_filter,
    dedupe_ladder,
    directory_summary,
    generate_report,
    history_scan,
    init_okf_db,
    plan_review,
    research_audit,
    resolve_mantis_security_review,
    review_gate,
)
from plugins.security_and_forensics.mantis_security_review.engine.tools import (
    _GLOBAL_ENGINE,
    mantis_calibrate_risk,
    mantis_chain_exploits,
    mantis_critic_filter,
    mantis_dedupe_ladder,
    mantis_directory_summary,
    mantis_generate_report,
    mantis_history_scan,
    mantis_plan_review,
    mantis_research_audit,
    mantis_review_gate,
)

logger = structlog.get_logger(__name__)


# -----------------------------------------------------------------------------
# Harness Plugin Class & IoC Lifecycle
# -----------------------------------------------------------------------------

class MantisSecurityReviewPlugin(HarnessPlugin, MantisSecurityReviewService):
    """Brain Harness Plugin providing Google Mantis security review and OKF storage services."""

    name = "plugin.mantis_security_review"
    version = "1.0.0"
    description = (
        "Google Mantis autonomous security review pipeline, VCS history mining, "
        "deduplication ladder, and risk calibration"
    )
    trusted = True

    def __init__(self, engine: MantisReviewEngine | None = None) -> None:
        self._engine = engine or _GLOBAL_ENGINE

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [MANTIS_SECURITY_REVIEW_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(MANTIS_SECURITY_REVIEW_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # Protocol Implementation Delegating to Engine
    # -------------------------------------------------------------------------

    def history_scan(
        self, repo_path: str, max_commits: int = 100, pattern_filter: str = ""
    ) -> dict[str, Any]:
        return self._engine.history_scan(repo_path, max_commits, pattern_filter)

    def directory_summary(self, dir_path: str, recursive: bool = True) -> dict[str, Any]:
        return self._engine.directory_summary(dir_path, recursive)

    def plan_review(
        self,
        threat_model: dict[str, Any],
        target_paths: list[str],
        focus_cwe: list[str] | None = None,
    ) -> dict[str, Any]:
        return self._engine.plan_review(threat_model, target_paths, focus_cwe)

    def research_audit(
        self,
        target_file: str,
        code_content: str,
        focus_cwe: list[str] | None = None,
    ) -> dict[str, Any]:
        return self._engine.research_audit(target_file, code_content, focus_cwe)

    def dedupe_ladder(
        self, findings: list[dict[str, Any]], mode: str = "syntactic_and_ast"
    ) -> dict[str, Any]:
        return self._engine.dedupe_ladder(findings, mode)

    def review_gate(
        self, finding: dict[str, Any], source_content: str, strictness: str = "high"
    ) -> dict[str, Any]:
        return self._engine.review_gate(finding, source_content, strictness)

    def critic_filter(
        self, finding: dict[str, Any], check_release_assertions: bool = True
    ) -> dict[str, Any]:
        return self._engine.critic_filter(finding, check_release_assertions)

    def chain_exploits(
        self, findings: list[dict[str, Any]], target_objective: str = ""
    ) -> dict[str, Any]:
        return self._engine.chain_exploits(findings, target_objective)

    def calibrate_risk(
        self, findings: list[dict[str, Any]], asset_criticality: str = "high"
    ) -> dict[str, Any]:
        return self._engine.calibrate_risk(findings, asset_criticality)

    def generate_report(
        self,
        findings: list[dict[str, Any]],
        exploit_chains: list[dict[str, Any]] | None = None,
        executive_summary: str = "",
    ) -> dict[str, Any]:
        return self._engine.generate_report(findings, exploit_chains, executive_summary)


# Exported module-level singleton (Rule 45)
plugin = MantisSecurityReviewPlugin()

__all__ = [
    "ExploitChain",
    "ExploitStep",
    "MANTIS_SECURITY_REVIEW_KEY",
    "MantisFinding",
    "MantisReviewEngine",
    "MantisSecurityReviewPlugin",
    "MantisSecurityReviewService",
    "calibrate_risk",
    "chain_exploits",
    "compute_stable_signature",
    "critic_filter",
    "dedupe_ladder",
    "directory_summary",
    "generate_report",
    "history_scan",
    "init_okf_db",
    "mantis_calibrate_risk",
    "mantis_chain_exploits",
    "mantis_critic_filter",
    "mantis_dedupe_ladder",
    "mantis_directory_summary",
    "mantis_generate_report",
    "mantis_history_scan",
    "mantis_plan_review",
    "mantis_research_audit",
    "mantis_review_gate",
    "plan_review",
    "plugin",
    "research_audit",
    "resolve_mantis_security_review",
    "review_gate",
]
