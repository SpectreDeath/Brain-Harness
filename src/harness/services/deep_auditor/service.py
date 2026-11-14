"""Deep Repo Auditor protocol, IoC ServiceKey, default implementation, and resolver."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceContext, ServiceKey

from .briefs import generate_audit_visual_briefs
from .collector import DeepAuditCollector
from .models import DeepAuditReport, VisualBriefPaths


@runtime_checkable
class DeepRepoAuditorService(Protocol):
    """Typed micro-kernel contract for 4-axis repository audits and visual brief generation."""

    def audit_repo(self, repo_path: str | Path) -> DeepAuditReport: ...

    def generate_briefs(
        self,
        report: DeepAuditReport,
        output_dir: str | Path | None = None,
    ) -> VisualBriefPaths: ...

    def extract_ki_candidates(self, report: DeepAuditReport) -> list[dict[str, Any]]: ...

    def run_full_audit(
        self,
        repo_path: str | Path,
        output_dir: str | Path | None = None,
    ) -> dict[str, Any]: ...


DEEP_AUDITOR_SERVICE_KEY: ServiceKey[DeepRepoAuditorService] = ServiceKey("service.deep_auditor")


class DefaultDeepRepoAuditorService(DeepRepoAuditorService):
    """Default slotted orchestrator elevating /deep-repo-auditor into the IoC kernel."""

    def __init__(self, collector: DeepAuditCollector | None = None) -> None:
        self._collector = collector or DeepAuditCollector()

    def audit_repo(self, repo_path: str | Path) -> DeepAuditReport:
        """Resolve project root, score 5D compute complexity, and evaluate all 4 axes."""
        root = Path(repo_path).resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"Repository path does not exist or is not a directory: {root}")
        resolved_root, topology, compute, axes = self._collector.collect(root)
        return DeepAuditReport(
            repo_root=str(root),
            resolved_root=str(resolved_root),
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
            compute=compute,
            topology=topology,
            axes=axes,
        )

    def generate_briefs(
        self,
        report: DeepAuditReport,
        output_dir: str | Path | None = None,
    ) -> VisualBriefPaths:
        """Render the 3 dark-mode HTML visual briefs for a completed DeepAuditReport."""
        return generate_audit_visual_briefs(report, output_dir=output_dir)

    def extract_ki_candidates(self, report: DeepAuditReport) -> list[dict[str, Any]]:
        """Derive portable Knowledge Item candidates anchored to audited axes."""
        candidates: list[dict[str, Any]] = []
        for idx, axis in enumerate(report.axes, 1):
            candidates.append(
                {
                    "id": f"ki_audit_candidate_{idx:02d}",
                    "title": f"{axis.axis}: {axis.title}",
                    "domain": "architecture_audit",
                    "status": axis.status,
                    "summary": axis.summary,
                    "evidence": list(axis.evidence),
                    "recommendations": list(axis.recommendations),
                }
            )
        return candidates

    def run_full_audit(
        self,
        repo_path: str | Path,
        output_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        """Execute full audit pipeline: 4-axis scan, 3 HTML briefs, and KI extraction."""
        report = self.audit_repo(repo_path)
        briefs = self.generate_briefs(report, output_dir=output_dir)
        candidates = self.extract_ki_candidates(report)
        return {
            "report": report.to_dict(),
            "briefs": briefs.to_dict(),
            "ki_candidates": candidates,
        }


def resolve_deep_repo_auditor(context: ServiceContext | None = None) -> DeepRepoAuditorService:
    """Resolve DeepRepoAuditorService from ServiceContext or register default cleanly."""
    if context is not None:
        existing = context.optional(DEEP_AUDITOR_SERVICE_KEY)
        if existing is not None:
            return existing
        instance: DeepRepoAuditorService = DefaultDeepRepoAuditorService()
        context.provide(DEEP_AUDITOR_SERVICE_KEY, instance)
        return instance
    return DefaultDeepRepoAuditorService()


__all__ = [
    "DEEP_AUDITOR_SERVICE_KEY",
    "DeepRepoAuditorService",
    "DefaultDeepRepoAuditorService",
    "resolve_deep_repo_auditor",
]
