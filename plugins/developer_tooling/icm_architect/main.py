"""ICM Architect Plugin — Folder Structure as Agent Architecture (arXiv:2603.16021)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.icm_architect import (
    ICM_ARCHITECT_SERVICE_KEY,
    DefaultIcmArchitectService,
    IcmArchitectService,
    IcmFormType,
    IcmIndexReport,
    IcmLinkCheckReport,
    IcmQuoteCheckReport,
    IcmScaffoldResult,
    IcmWorkspaceAuditReport,
)

logger = structlog.get_logger(__name__)


class IcmArchitectPlugin(HarnessPlugin):
    """Plugin providing in-process ICM workspace architecture, auditing, and verification."""

    def __init__(self, service: IcmArchitectService | None = None) -> None:
        super().__init__()
        self._service = service or DefaultIcmArchitectService()

    @property
    def name(self) -> str:
        return "plugin.icm_architect"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Interpretable Context Methodology (ICM, arXiv:2603.16021) workspace architecture, "
            "contract auditing, link verification, quote verification, and index generation"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [ICM_ARCHITECT_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register the service into the micro-kernel IoC container (Rule 1 & Rule 2)."""
        context.provide(ICM_ARCHITECT_SERVICE_KEY, self._service)
        logger.info(
            "icm_architect_service_provided",
            service=str(ICM_ARCHITECT_SERVICE_KEY),
        )

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    # Delegation methods
    def audit(self, root: str | Path = ".") -> IcmWorkspaceAuditReport:
        return self._service.audit_workspace(root=root)

    def verify_links(
        self,
        root: str | Path = ".",
        skip_folders: list[str] | None = None,
        graph_file: str | Path | None = None,
    ) -> IcmLinkCheckReport:
        return self._service.verify_links(root=root, skip_folders=skip_folders, graph_file=graph_file)

    def verify_quotes(self, root: str | Path = ".", show_cuts: bool = False) -> IcmQuoteCheckReport:
        return self._service.verify_quotes(root=root, show_cuts=show_cuts)

    def rebuild_index(self, folders: list[str | Path], root: str | Path | None = None) -> IcmIndexReport:
        return self._service.rebuild_index(folders=folders, root=root)

    def scaffold(
        self,
        target_dir: str | Path,
        form: str | IcmFormType = IcmFormType.PIPELINE,
        name: str | None = None,
    ) -> IcmScaffoldResult:
        return self._service.scaffold_form(target_dir=target_dir, form=form, name=name)

    def scaffold_workspace(
        self,
        target_dir: str | Path,
        template_name: str = "workspace-builder",
        name: str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> IcmScaffoldResult:
        return self._service.scaffold_workspace(
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
    ) -> Any:
        return self._service.interpolate_template(
            template_path=template_path,
            variables=variables,
            output_path=output_path,
        )


# Rule 45: Export instantiated module singleton plugin instance
plugin = IcmArchitectPlugin()


# Top-level entrypoints matching plugin.json declarations
def icm_audit_workspace(root: str = ".", **kwargs: Any) -> dict[str, Any]:
    """Audit an ICM workspace against the 10 invariants and token limits."""
    report = plugin.audit(root=root)
    return report.to_dict()


def icm_verify_links(
    root: str = ".",
    skip_folders: list[str] | None = None,
    graph_file: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Verify relative markdown links and contract inputs."""
    report = plugin.verify_links(root=root, skip_folders=skip_folders, graph_file=graph_file)
    return report.to_dict()


def icm_verify_quotes(root: str = ".", show_cuts: bool = False, **kwargs: Any) -> dict[str, Any]:
    """Verify verbatim quote citations and keep-out phrases."""
    report = plugin.verify_quotes(root=root, show_cuts=show_cuts)
    return report.to_dict()


def icm_rebuild_index(folders: list[str], root: str = ".", **kwargs: Any) -> dict[str, Any]:
    """Rebuild _index.md files across specified shelves."""
    report = plugin.rebuild_index(folders=folders, root=root)
    return report.to_dict()


def icm_scaffold_form(target_dir: str, form: str = "pipeline", name: str | None = None, **kwargs: Any) -> dict[str, Any]:
    """Scaffold a new ICM workspace."""
    result = plugin.scaffold(target_dir=target_dir, form=form, name=name)
    return result.to_dict()


def icm_scaffold_workspace(
    target_dir: str,
    template_name: str = "workspace-builder",
    name: str | None = None,
    variables: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Scaffold a full production workspace from canonical templates (arXiv:2603.16021)."""
    result = plugin.scaffold_workspace(target_dir=target_dir, template_name=template_name, name=name, variables=variables)
    return result.to_dict()


def icm_interpolate_template(
    template_path: str,
    variables: dict[str, Any] | None = None,
    output_path: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Substitute {{VARIABLE}} tags and resolve conditionals per _core/placeholder-syntax.md."""
    res = plugin.interpolate_template(template_path=template_path, variables=variables, output_path=output_path)
    return res.to_dict()
