"""Deep Repo Auditor service package elevating /deep-repo-auditor into the IoC micro-kernel."""

from __future__ import annotations

from .briefs import generate_audit_visual_briefs
from .collector import DeepAuditCollector, resolve_nested_project_root
from .models import (
    AxisFinding,
    ComputeDimensionVector,
    DeepAuditReport,
    TopologyNodeSummary,
    VisualBriefPaths,
)
from .service import (
    DEEP_AUDITOR_SERVICE_KEY,
    DeepRepoAuditorService,
    DefaultDeepRepoAuditorService,
    resolve_deep_repo_auditor,
)

__all__ = [
    "DEEP_AUDITOR_SERVICE_KEY",
    "AxisFinding",
    "ComputeDimensionVector",
    "DeepAuditCollector",
    "DeepAuditReport",
    "DeepRepoAuditorService",
    "DefaultDeepRepoAuditorService",
    "TopologyNodeSummary",
    "VisualBriefPaths",
    "generate_audit_visual_briefs",
    "resolve_deep_repo_auditor",
    "resolve_nested_project_root",
]
