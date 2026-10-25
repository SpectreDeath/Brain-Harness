"""Protocol and ServiceKey definitions for Interpretable Context Methodology (ICM)."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from harness.kernel.context import ServiceKey

from .models import (
    IcmFormType,
    IcmIndexReport,
    IcmLinkCheckReport,
    IcmQuoteCheckReport,
    IcmScaffoldResult,
    IcmTemplateInterpolateResult,
    IcmWorkspaceAuditReport,
)


@runtime_checkable
class IcmArchitectService(Protocol):
    """Authoritative protocol for ICM workspace auditing, verification, and scaffolding."""

    def audit_workspace(self, root: str | Path = ".") -> IcmWorkspaceAuditReport:
        """Audit a workspace against the 10 ICM invariants, classifying files and evaluating token budgets."""
        ...

    def verify_links(
        self,
        root: str | Path = ".",
        skip_folders: list[str] | None = None,
        graph_file: str | Path | None = None,
    ) -> IcmLinkCheckReport:
        """Verify that all relative markdown links and contract inputs resolve cleanly."""
        ...

    def verify_quotes(
        self,
        root: str | Path = ".",
        show_cuts: bool = False,
    ) -> IcmQuoteCheckReport:
        """Verify that quoted text appears verbatim in raw sources and enforce keep-out lists."""
        ...

    def rebuild_index(
        self,
        folders: list[str | Path],
        root: str | Path | None = None,
    ) -> IcmIndexReport:
        """Rebuild _index.md files across shelves and record folders from frontmatter metadata."""
        ...

    def scaffold_form(
        self,
        target_dir: str | Path,
        form: str | IcmFormType = IcmFormType.PIPELINE,
        name: str | None = None,
    ) -> IcmScaffoldResult:
        """Scaffold a minimal, production-ready ICM workspace for the selected form."""
        ...

    def scaffold_workspace(
        self,
        target_dir: str | Path,
        template_name: str = "workspace-builder",
        name: str | None = None,
        variables: dict[str, str] | None = None,
    ) -> IcmScaffoldResult:
        """Scaffold a full production workspace from canonical templates (arXiv:2603.16021)."""
        ...

    def interpolate_template(
        self,
        template_path: str | Path,
        variables: dict[str, str] | None = None,
        output_path: str | Path | None = None,
    ) -> IcmTemplateInterpolateResult:
        """Substitute {{VARIABLE}} tags and resolve conditionals per _core/placeholder-syntax.md."""
        ...


ICM_ARCHITECT_SERVICE_KEY: ServiceKey[IcmArchitectService] = ServiceKey(
    "harness.services.icm_architect"
)
