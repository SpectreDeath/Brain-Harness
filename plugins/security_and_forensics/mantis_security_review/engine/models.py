"""Domain models and protocols for Google Mantis security review and triage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey


@runtime_checkable
class MantisSecurityReviewService(Protocol):
    """Protocol for Google Mantis security review, triage, and OKF storage operations."""

    def history_scan(
        self, repo_path: str, max_commits: int = 100, pattern_filter: str = ""
    ) -> dict[str, Any]: ...

    def directory_summary(
        self, dir_path: str, recursive: bool = True
    ) -> dict[str, Any]: ...

    def plan_review(
        self,
        threat_model: dict[str, Any],
        target_paths: list[str],
        focus_cwe: list[str] | None = None,
    ) -> dict[str, Any]: ...

    def research_audit(
        self,
        target_file: str,
        code_content: str,
        focus_cwe: list[str] | None = None,
    ) -> dict[str, Any]: ...

    def dedupe_ladder(
        self, findings: list[dict[str, Any]], mode: str = "syntactic_and_ast"
    ) -> dict[str, Any]: ...

    def review_gate(
        self, finding: dict[str, Any], source_content: str, strictness: str = "high"
    ) -> dict[str, Any]: ...

    def critic_filter(
        self, finding: dict[str, Any], check_release_assertions: bool = True
    ) -> dict[str, Any]: ...

    def chain_exploits(
        self, findings: list[dict[str, Any]], target_objective: str = ""
    ) -> dict[str, Any]: ...

    def calibrate_risk(
        self, findings: list[dict[str, Any]], asset_criticality: str = "high"
    ) -> dict[str, Any]: ...

    def generate_report(
        self,
        findings: list[dict[str, Any]],
        exploit_chains: list[dict[str, Any]] | None = None,
        executive_summary: str = "",
    ) -> dict[str, Any]: ...


MANTIS_SECURITY_REVIEW_KEY: ServiceKey[MantisSecurityReviewService] = ServiceKey(
    "service.mantis_security_review"
)


@dataclass(slots=True, frozen=True)
class MantisFinding:
    """Slotted, immutable value object representing a normalized security finding (Rule 12)."""

    id: str
    filepath: str
    line: int
    cwe: str
    title: str
    severity: str
    signature: str
    target_symbol: str = ""
    description: str = ""
    status: str = "CONFIRMED"


@dataclass(slots=True, frozen=True)
class ExploitStep:
    """Single stage within an exploit chain."""

    step: int
    finding_id: str
    tactic: str
    description: str


@dataclass(slots=True, frozen=True)
class ExploitChain:
    """Compound multi-stage exploit chain."""

    chain_id: str
    objective: str
    steps: list[ExploitStep] = field(default_factory=list)
    compound_severity: str = "critical"
