"""Coordinator implementation of DjangoBridgeService using specialized engine modules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from harness.services.django_bridge import (
    DjangoBridgeService,
    DjangoManageResult,
    DjangoModelSchema,
    DjangoProjectInfo,
    DjangoQueryResult,
    DjangoTaskInfo,
    DjangoValidationResult,
)

from .generator import generate_model_source
from .introspect import (
    count_url_patterns,
    detect_django_version,
    execute_inspect_project,
    find_settings_file,
    parse_app_models,
    parse_settings_ast,
)
from .manage import execute_manage_command
from .simulator import simulate_orm_query
from .tasks import inspect_project_tasks
from .validator import validate_template_syntax


class DjangoBridgeServiceImpl(DjangoBridgeService):
    """Authoritative implementation of DjangoBridgeService using AST analysis and sandboxed execution."""

    async def inspect_project(
        self,
        project_path: str,
        settings_module: str | None = None,
        include_models: bool = True,
    ) -> DjangoProjectInfo:
        """Inspect Django project AST, discovering apps, models, URLs, middleware, and settings."""
        return await execute_inspect_project(
            project_path=project_path,
            settings_module=settings_module,
            include_models=include_models,
        )

    async def execute_manage(
        self,
        project_path: str,
        command: str,
        args: list[str] | None = None,
        settings_module: str | None = None,
        timeout_sec: float = 30.0,
    ) -> DjangoManageResult:
        """Execute a safe Django management command in a guarded subprocess."""
        return await execute_manage_command(
            project_path=project_path,
            command=command,
            args=args,
            settings_module=settings_module,
            timeout_sec=timeout_sec,
        )

    def generate_model_code(
        self,
        model_name: str,
        fields: list[dict[str, Any]],
        app_label: str = "",
        docstring: str = "",
        meta_options: dict[str, Any] | None = None,
    ) -> str:
        """Synthesizes declarative Django model classes and fields from JSON/schema specifications."""
        return generate_model_source(
            model_name=model_name,
            fields=fields,
            app_label=app_label,
            docstring=docstring,
            meta_options=meta_options,
        )

    def simulate_query(
        self,
        query_expr: str,
        model_name: str,
        project_path: str | None = None,
    ) -> DjangoQueryResult:
        """Safely translate and compile a Django ORM query expression to SQL."""
        return simulate_orm_query(
            query_expr=query_expr,
            model_name=model_name,
            project_path=project_path,
        )

    def validate_template(
        self,
        template_content: str,
        template_path: str | None = None,
        enable_partials: bool = True,
    ) -> DjangoValidationResult:
        """Validate syntax of Django templates, block tags, partials, and filters."""
        return validate_template_syntax(
            template_content=template_content,
            template_path=template_path,
            enable_partials=enable_partials,
        )

    async def inspect_tasks(
        self,
        project_path: str,
        backend: str | None = None,
    ) -> list[DjangoTaskInfo]:
        """Introspect Django 6.x background tasks defined across apps."""
        return await inspect_project_tasks(
            project_path=project_path,
            backend=backend,
        )

    # --- Backward Compatible Private AST Helper Methods ---

    def _detect_django_version(self, root: Path) -> str:
        return detect_django_version(root)

    def _find_settings_file(self, root: Path, settings_module: str | None) -> Path | None:
        return find_settings_file(root, settings_module)

    def _parse_settings_ast(self, settings_path: Path) -> dict[str, Any]:
        return parse_settings_ast(settings_path)

    def _parse_app_models(self, app_dir: Path, app_label: str) -> list[DjangoModelSchema]:
        return parse_app_models(app_dir, app_label)

    def _count_url_patterns(self, root: Path) -> int:
        return count_url_patterns(root)
