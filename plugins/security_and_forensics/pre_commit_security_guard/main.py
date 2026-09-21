"""Pre-Commit Security Guard Plugin for Brain Harness.

Implements shift-left SAST analysis, Shannon entropy credential interception,
deliberate synthetic failure verification, and SARIF dual-gate CI defense.
Synthesized from Umair Mirza's literature (freeCodeCamp, 2026, ki_umairmirza_precommit_security).
Rule 18: Single-responsibility domain partitioning in security_and_forensics.
Rule 45: Plugin module singleton and IoC provider invariant.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.pre_commit_security_guard import (
    PRE_COMMIT_SECURITY_GUARD_SERVICE_KEY,
    DualGateCheckData,
    PreCommitSecurityGuardService,
    SarifExportData,
    ScanReportData,
    SecurityFindingData,
    SmokeCheckData,
    SmokeReportData,
    SuppressionCheckData,
    SuppressionReportData,
)

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Ensure the skill scripts directory is on sys.path for engine resolution
_ws_root = Path(__file__).resolve().parents[3]
_skill_scripts = (
    _ws_root / ".agents" / "skills" / "pre-commit-security-guard" / "scripts"
)
if str(_skill_scripts) not in sys.path:
    sys.path.insert(0, str(_skill_scripts))

from pre_commit_security_engine import (
    PreCommitSecurityGuardEngine,
    ScanReport,
    SecurityFinding,
    SmokeReport,
    SuppressionReport,
)


class PreCommitSecurityGuardPlugin(HarnessPlugin, PreCommitSecurityGuardService):
    """Plugin providing shift-left SAST & secret interception via IoC container."""

    def __init__(self) -> None:
        super().__init__()
        self._engine = PreCommitSecurityGuardEngine()

    @property
    def name(self) -> str:
        return "plugin.pre_commit_security_guard"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Shift-left SAST linter, Shannon entropy secret scanner, deliberate synthetic "
            "failure smoke gate, and SARIF dual-gate CI defense plugin (Umair Mirza 2026)"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        """Declare provided services for topological sorting (Rule 3)."""
        return [PRE_COMMIT_SECURITY_GUARD_SERVICE_KEY]

    async def on_load(self, context: ServiceContext) -> None:
        """Register the service instance into IoC container (Rule 2, 45)."""
        context.provide(PRE_COMMIT_SECURITY_GUARD_SERVICE_KEY, self)

    # -------------------------------------------------------------------------
    # PreCommitSecurityGuardService Protocol Implementation
    # -------------------------------------------------------------------------

    def scan_staged_files(self, files: list[str] | None = None) -> ScanReportData:
        """Scan passed files or staged working tree files for vulnerabilities."""
        if files is None:
            # Fallback: scan repository python/js/ts files if none passed
            files = [
                str(p)
                for p in _ws_root.glob("*.py")
            ]

        raw_report: ScanReport = self._engine.scan_files(files)

        findings_data = [
            SecurityFindingData(
                rule_id=f.rule_id,
                name=f.name,
                severity=f.severity,
                scanner=f.scanner,
                file_path=f.file_path,
                line_number=f.line_number,
                code_snippet=f.code_snippet,
                message=f.message,
                remediation=f.remediation,
            )
            for f in raw_report.findings
        ]

        return ScanReportData(
            target=raw_report.target,
            passed=raw_report.passed,
            total_files_scanned=raw_report.total_files_scanned,
            findings=findings_data,
            duration_ms=raw_report.duration_ms,
            metrics=raw_report.metrics,
        )

    def run_synthetic_smoke_tests(self) -> SmokeReportData:
        """Execute deliberate synthetic failure tests verifying that guardrails block commits."""
        raw_smoke: SmokeReport = self._engine.run_synthetic_smoke_tests()

        checks_data = [
            SmokeCheckData(
                fixture_name=c.fixture_name,
                hazard_type=c.hazard_type,
                expected_failure=c.expected_failure,
                detected=c.detected,
                exit_code=c.exit_code,
                matched_rule=c.matched_rule,
                passed=c.passed,
                diagnostic=c.diagnostic,
            )
            for c in raw_smoke.checks
        ]

        return SmokeReportData(
            passed=raw_smoke.passed,
            checks=checks_data,
            fixtures_tested=raw_smoke.fixtures_tested,
            duration_ms=raw_smoke.duration_ms,
        )

    def audit_suppression_hygiene(self, root_dir: str = ".") -> SuppressionReportData:
        """Audit repository for unjustified comment suppressions and blanket exclusions."""
        raw_supp: SuppressionReport = self._engine.audit_suppressions(root_dir)

        checks_data = [
            SuppressionCheckData(
                file_path=c.file_path,
                line_number=c.line_number,
                comment_text=c.comment_text,
                has_rationale=c.has_rationale,
                rule_id=c.rule_id,
                is_blanket_exclusion=c.is_blanket_exclusion,
                valid=c.valid,
                message=c.message,
            )
            for c in raw_supp.checks
        ]

        return SuppressionReportData(
            passed=raw_supp.passed,
            total_suppressions=raw_supp.total_suppressions,
            valid_suppressions=raw_supp.valid_suppressions,
            unjustified_suppressions=raw_supp.unjustified_suppressions,
            blanket_exclusions=raw_supp.blanket_exclusions,
            checks=checks_data,
            message=raw_supp.message,
        )

    def audit_dual_gate_ci(self, workflow_path: str = ".github/workflows/security.yml") -> DualGateCheckData:
        """Audit GitHub Actions workflow configuration to guarantee dual-gate CI parity."""
        raw_ci = self._engine.audit_dual_gate_ci(workflow_path)

        return DualGateCheckData(
            target_workflow=raw_ci.target_workflow,
            has_fetch_depth_zero=raw_ci.has_fetch_depth_zero,
            has_sarif_upload=raw_ci.has_sarif_upload,
            has_secret_scanner=raw_ci.has_secret_scanner,
            has_sast_scanner=raw_ci.has_sast_scanner,
            passed=raw_ci.passed,
            reasons=list(raw_ci.reasons),
        )

    def export_sarif(self, report: ScanReportData) -> SarifExportData:
        """Format scan report findings into standard SARIF v2.1.0 schema."""
        # Convert DTO back to domain model for formatting
        domain_findings = tuple(
            SecurityFinding(
                rule_id=f.rule_id,
                name=f.name,
                severity=f.severity,
                scanner=f.scanner,
                file_path=f.file_path,
                line_number=f.line_number,
                code_snippet=f.code_snippet,
                message=f.message,
                remediation=f.remediation,
            )
            for f in report.findings
        )
        domain_report = ScanReport(
            target=report.target,
            passed=report.passed,
            total_files_scanned=report.total_files_scanned,
            findings=domain_findings,
            duration_ms=report.duration_ms,
            metrics=report.metrics,
        )

        sarif_rep = self._engine.export_sarif(domain_report)

        return SarifExportData(
            version=sarif_rep.version,
            schema_uri=sarif_rep.schema_uri,
            sarif_dict=sarif_rep.sarif_dict,
            finding_count=sarif_rep.finding_count,
        )

    def generate_visual_brief(self, output_path: str | None = None) -> str:
        """Generate interactive HTML visual brief with Mermaid diagrams."""
        out_p = self._engine.generate_visual_brief(output_path)
        return str(out_p)


# Rule 45: Export module singleton instance
plugin = PreCommitSecurityGuardPlugin()
