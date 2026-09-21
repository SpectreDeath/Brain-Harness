"""Pre-Commit Security Guard service protocol, typed models, and ServiceKey.

Elevates the shift-left SAST, Shannon entropy credential interception,
deliberate synthetic smoke tests, and SARIF dual-gate CI parity engine
into a first-class micro-kernel IoC service seam.
Synthesized from Umair Mirza's literature (freeCodeCamp, 2026, ki_umairmirza_precommit_security).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class SecurityFindingData(BaseModel):
    """Data transfer model for an individual security or secret finding."""

    rule_id: str = Field(..., description="Unique rule or diagnostic identifier")
    name: str = Field(..., description="Human-readable finding name")
    severity: str = Field(..., description="Severity level: critical, high, medium, low, info")
    scanner: str = Field(..., description="Scanner origin: sast_devskim, secret_gitleaks, suppression_hygiene, dual_gate_ci")
    file_path: str = Field(..., description="File path where finding was detected")
    line_number: int | None = Field(default=None, description="Line number if applicable")
    code_snippet: str = Field(default="", description="Relevant code snippet")
    message: str = Field(default="", description="Diagnostic message or explanation")
    remediation: str = Field(default="", description="Remediation instructions")


class ScanReportData(BaseModel):
    """Data transfer model for multi-file security scan results."""

    target: str = Field(..., description="Scan target description or batch label")
    passed: bool = Field(..., description="Whether scan passed without critical/high findings")
    total_files_scanned: int = Field(default=0, description="Total files inspected")
    findings: list[SecurityFindingData] = Field(default_factory=list, description="Discovered security findings")
    duration_ms: float = Field(default=0.0, description="Execution time in milliseconds")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Diagnostic metrics breakdown")


class SmokeCheckData(BaseModel):
    """Data transfer model for a deliberate synthetic failure smoke test."""

    fixture_name: str = Field(..., description="Synthetic fixture identifier")
    hazard_type: str = Field(..., description="Security hazard type tested")
    expected_failure: bool = Field(default=True, description="Whether failure is expected")
    detected: bool = Field(..., description="Whether the hazard was intercepted")
    exit_code: int = Field(..., description="Simulated commit exit code (1 = blocked, 0 = passed)")
    matched_rule: str = Field(..., description="Rule ID that intercepted the synthetic failure")
    passed: bool = Field(..., description="Whether the smoke check passed the safety gate")
    diagnostic: str = Field(default="", description="Diagnostic message")


class SmokeReportData(BaseModel):
    """Data transfer model for aggregated deliberate synthetic failure smoke results."""

    passed: bool = Field(..., description="Whether all synthetic smoke tests passed")
    checks: list[SmokeCheckData] = Field(default_factory=list, description="Executed smoke checks")
    fixtures_tested: int = Field(default=0, description="Total fixtures evaluated")
    duration_ms: float = Field(default=0.0, description="Execution time in milliseconds")


class SuppressionCheckData(BaseModel):
    """Data transfer model for an inline suppression or exclude rule."""

    file_path: str = Field(..., description="File path containing suppression")
    line_number: int = Field(..., description="Line number")
    comment_text: str = Field(..., description="Raw comment text")
    has_rationale: bool = Field(..., description="Whether documented rationale exists")
    rule_id: str | None = Field(default=None, description="Targeted rule ID if specified")
    is_blanket_exclusion: bool = Field(default=False, description="Whether this is a blanket directory exclude")
    valid: bool = Field(..., description="Whether the suppression passes hygiene rules")
    message: str = Field(default="", description="Diagnostic observation")


class SuppressionReportData(BaseModel):
    """Data transfer model for suppression hygiene audit results."""

    passed: bool = Field(..., description="Whether suppression hygiene checks passed")
    total_suppressions: int = Field(default=0, description="Total suppressions discovered")
    valid_suppressions: int = Field(default=0, description="Valid justified suppressions")
    unjustified_suppressions: int = Field(default=0, description="Unjustified suppressions lacking rationale")
    blanket_exclusions: int = Field(default=0, description="Prohibited blanket folder exclusions")
    checks: list[SuppressionCheckData] = Field(default_factory=list, description="Individual suppression checks")
    message: str = Field(default="", description="Overall diagnostic summary")


class DualGateCheckData(BaseModel):
    """Data transfer model for CI dual-gate parity checks."""

    target_workflow: str = Field(..., description="Workflow file path audited")
    has_fetch_depth_zero: bool = Field(..., description="Whether fetch-depth is 0")
    has_sarif_upload: bool = Field(..., description="Whether SARIF upload step exists")
    has_secret_scanner: bool = Field(..., description="Whether remote secret scanner exists")
    has_sast_scanner: bool = Field(..., description="Whether remote SAST scanner exists")
    passed: bool = Field(..., description="Whether CI workflow satisfies dual-gate requirements")
    reasons: list[str] = Field(default_factory=list, description="Failure reasons or gaps")


class SarifExportData(BaseModel):
    """Data transfer model for SARIF v2.1.0 output."""

    version: str = Field(default="2.1.0", description="SARIF version")
    schema_uri: str = Field(..., description="SARIF schema JSON URI")
    sarif_dict: dict[str, Any] = Field(default_factory=dict, description="Parsed SARIF document dictionary")
    finding_count: int = Field(default=0, description="Total findings exported in SARIF")


@runtime_checkable
class PreCommitSecurityGuardService(Protocol):
    """Protocol for Pre-Commit Security Guard operations in the micro-kernel."""

    def scan_staged_files(self, files: list[str] | None = None) -> ScanReportData:
        """Scan staged files or designated paths for SAST vulnerabilities and secrets."""
        ...

    def run_synthetic_smoke_tests(self) -> SmokeReportData:
        """Execute deliberate synthetic failure tests verifying commit blocking."""
        ...

    def audit_suppression_hygiene(self, root_dir: str = ".") -> SuppressionReportData:
        """Audit repository for unjustified comment suppressions and blanket folder exclusions."""
        ...

    def audit_dual_gate_ci(self, workflow_path: str = ".github/workflows/security.yml") -> DualGateCheckData:
        """Audit GitHub Actions workflow configuration to guarantee dual-gate CI parity."""
        ...

    def export_sarif(self, report: ScanReportData) -> SarifExportData:
        """Format scan report findings into SARIF v2.1.0 standard schema."""
        ...

    def generate_visual_brief(self, output_path: str | None = None) -> str:
        """Generate interactive HTML visual brief with Mermaid diagrams."""
        ...


PRE_COMMIT_SECURITY_GUARD_SERVICE_KEY: ServiceKey[PreCommitSecurityGuardService] = ServiceKey(
    "service.pre_commit_security_guard"
)
