"""Default slotted implementation of Interpretable Context Methodology (ICM) architecture engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .auditor import IcmAuditor
from .indexer import IcmIndexer
from .models import (
    IcmFormType,
    IcmIndexReport,
    IcmLinkCheckReport,
    IcmQuoteCheckReport,
    IcmScaffoldResult,
    IcmTemplateInterpolateResult,
    IcmWorkspaceAuditReport,
)
from .protocol import IcmArchitectService
from .scaffolder import IcmScaffolder
from .template_engine import IcmTemplateEngine
from .verifier import IcmVerifier


class DefaultIcmArchitectService(IcmArchitectService):
    """Slotted ICM architecture service coordinating specialized sub-engines (arXiv:2603.16021)."""

    def __init__(
        self,
        auditor: IcmAuditor | None = None,
        verifier: IcmVerifier | None = None,
        indexer: IcmIndexer | None = None,
        scaffolder: IcmScaffolder | None = None,
        template_engine: IcmTemplateEngine | None = None,
    ) -> None:
        self._auditor = auditor or IcmAuditor()
        self._verifier = verifier or IcmVerifier()
        self._indexer = indexer or IcmIndexer()
        self._scaffolder = scaffolder or IcmScaffolder()
        self._template_engine = template_engine or IcmTemplateEngine()

    def audit_workspace(self, root: str | Path = ".") -> IcmWorkspaceAuditReport:
        """Audit workspace against 10 ICM invariants, classifying files and evaluating token budgets."""
        return self._auditor.audit_workspace(root=root)

    def verify_links(
        self,
        root: str | Path = ".",
        skip_folders: list[str] | None = None,
        graph_file: str | Path | None = None,
    ) -> IcmLinkCheckReport:
        """Verify that relative links and contract inputs resolve without breakage."""
        return self._verifier.verify_links(root=root, skip_folders=skip_folders, graph_file=graph_file)

    def verify_quotes(self, root: str | Path = ".", show_cuts: bool = False) -> IcmQuoteCheckReport:
        """Verify that quoted text appears verbatim in raw sources and enforce keep-outs."""
        return self._verifier.verify_quotes(root=root, show_cuts=show_cuts)

    def rebuild_index(self, folders: list[str | Path], root: str | Path | None = None) -> IcmIndexReport:
        """Rebuild _index.md files across specified shelves."""
        return self._indexer.rebuild_index(folders=folders, root=root)

    def scaffold_form(
        self,
        target_dir: str | Path,
        form: str | IcmFormType = IcmFormType.PIPELINE,
        name: str | None = None,
    ) -> IcmScaffoldResult:
        """Scaffold a new ICM workspace from one of 5 canonical forms."""
        return self._scaffolder.scaffold_form(target_dir=target_dir, form=form, name=name)

    def scaffold_workspace(
        self,
        target_dir: str | Path,
        template_name: str = "workspace-builder",
        name: str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> IcmScaffoldResult:
        """Instantiate a production-grade workspace from canonical templates (arXiv:2603.16021)."""
        return self._template_engine.instantiate_workspace(
            target_dir=target_dir,
            template_name=template_name,
            name=name,
            variables=variables,
        )

    def interpolate_template(
        self,
        template_path: str | Path,
        variables: dict[str, Any] | None = None,
        output_path: str | Path | None = None,
    ) -> IcmTemplateInterpolateResult:
        """Substitute {{VARIABLE}} tags and resolve conditionals per _core/placeholder-syntax.md."""
        return self._template_engine.interpolate_file(
            template_path=template_path,
            variables=variables,
            output_path=output_path,
        )
