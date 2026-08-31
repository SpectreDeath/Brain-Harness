"""Django Bridge Service — typed service, schemas, and AST inspection protocols for Django ecosystems."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
import structlog

from harness.kernel.context import ServiceKey

logger = structlog.get_logger(__name__)

DJANGO_BRIDGE_KEY = ServiceKey["DjangoBridgeService"]("service.django_bridge")

# Safe management commands allowed for execution in sandboxed subprocesses
SAFE_MANAGEMENT_COMMANDS: set[str] = {
    "check",
    "showmigrations",
    "migrate",
    "sqlmigrate",
    "sqlflush",
    "sqlsequencereset",
    "diffsettings",
    "inspectdb",
    "makemigrations",
    "test",
    "dumpdata",
    "loaddata",
    "collectstatic",
    "compilemessages",
    "makemessages",
    "dbshell",
    "shell",
    "version",
}


@dataclass(slots=True, frozen=True)
class DjangoModelField:
    """Slotted and frozen model representing a Django Model Field."""

    name: str
    field_type: str
    null: bool = False
    blank: bool = False
    primary_key: bool = False
    unique: bool = False
    db_index: bool = False
    default: str | None = None
    related_model: str | None = None
    on_delete: str | None = None
    help_text: str = ""
    extra_kwargs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize field to dictionary."""
        return {
            "name": self.name,
            "field_type": self.field_type,
            "null": self.null,
            "blank": self.blank,
            "primary_key": self.primary_key,
            "unique": self.unique,
            "db_index": self.db_index,
            "default": self.default,
            "related_model": self.related_model,
            "on_delete": self.on_delete,
            "help_text": self.help_text,
            "extra_kwargs": self.extra_kwargs,
        }


@dataclass(slots=True, frozen=True)
class DjangoModelSchema:
    """Slotted model representing a Django Model class schema."""

    name: str
    app_label: str
    fields: tuple[DjangoModelField, ...]
    docstring: str = ""
    db_table: str | None = None
    ordering: tuple[str, ...] = ()
    unique_together: tuple[tuple[str, ...], ...] = ()
    indexes: tuple[str, ...] = ()
    verbose_name: str | None = None
    verbose_name_plural: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize model schema to dictionary."""
        return {
            "name": self.name,
            "app_label": self.app_label,
            "fields": [f.to_dict() for f in self.fields],
            "docstring": self.docstring,
            "db_table": self.db_table,
            "ordering": list(self.ordering),
            "unique_together": [list(u) for u in self.unique_together],
            "indexes": list(self.indexes),
            "verbose_name": self.verbose_name,
            "verbose_name_plural": self.verbose_name_plural,
        }


@dataclass(slots=True, frozen=True)
class DjangoAppInfo:
    """Slotted model representing an installed Django Application."""

    name: str
    label: str
    path: str
    models_count: int = 0
    has_migrations: bool = False
    has_admin: bool = False
    has_tasks: bool = False
    has_urls: bool = False


@dataclass(slots=True, frozen=True)
class DjangoProjectInfo:
    """Slotted model representing an entire Django Project inspection result."""

    project_root: str
    settings_module: str | None
    django_version: str
    installed_apps: tuple[DjangoAppInfo, ...]
    models: tuple[DjangoModelSchema, ...]
    url_patterns_count: int
    middleware_stack: tuple[str, ...]
    databases: tuple[str, ...]
    background_tasks_enabled: bool = False
    csp_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize project info to dictionary."""
        return {
            "project_root": self.project_root,
            "settings_module": self.settings_module,
            "django_version": self.django_version,
            "installed_apps": [
                {
                    "name": a.name,
                    "label": a.label,
                    "path": a.path,
                    "models_count": a.models_count,
                    "has_migrations": a.has_migrations,
                    "has_admin": a.has_admin,
                    "has_tasks": a.has_tasks,
                    "has_urls": a.has_urls,
                }
                for a in self.installed_apps
            ],
            "models": [m.to_dict() for m in self.models],
            "url_patterns_count": self.url_patterns_count,
            "middleware_stack": list(self.middleware_stack),
            "databases": list(self.databases),
            "background_tasks_enabled": self.background_tasks_enabled,
            "csp_enabled": self.csp_enabled,
        }


@dataclass(slots=True, frozen=True)
class DjangoManageResult:
    """Slotted model representing the output of a Django management command execution."""

    command: str
    args: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    success: bool

    def to_dict(self) -> dict[str, Any]:
        """Serialize result to dictionary."""
        return {
            "command": self.command,
            "args": list(self.args),
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "success": self.success,
        }


@dataclass(slots=True, frozen=True)
class DjangoQueryResult:
    """Slotted model representing the translation of a Django ORM query to SQL."""

    query_expr: str
    model_name: str
    generated_sql: str
    params: tuple[Any, ...] = ()
    explain_plan: str | None = None
    is_safe_read_only: bool = True
    tables_referenced: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize query result to dictionary."""
        return {
            "query_expr": self.query_expr,
            "model_name": self.model_name,
            "generated_sql": self.generated_sql,
            "params": list(self.params),
            "explain_plan": self.explain_plan,
            "is_safe_read_only": self.is_safe_read_only,
            "tables_referenced": list(self.tables_referenced),
        }


@dataclass(slots=True, frozen=True)
class DjangoValidationResult:
    """Slotted model representing template syntax or model schema validation diagnostics."""

    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    partials_found: tuple[str, ...] = ()
    tags_found: tuple[str, ...] = ()
    filters_found: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize validation result to dictionary."""
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "partials_found": list(self.partials_found),
            "tags_found": list(self.tags_found),
            "filters_found": list(self.filters_found),
        }


@dataclass(slots=True, frozen=True)
class DjangoTaskInfo:
    """Slotted model representing a Django 6.x background task definition."""

    task_name: str
    module: str
    func_name: str
    queue: str = "default"
    backend: str = "immediate"
    priority: int = 0
    timeout: int | None = None
    docstring: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize task info to dictionary."""
        return {
            "task_name": self.task_name,
            "module": self.module,
            "func_name": self.func_name,
            "queue": self.queue,
            "backend": self.backend,
            "priority": self.priority,
            "timeout": self.timeout,
            "docstring": self.docstring,
        }


@runtime_checkable
class DjangoBridgeService(Protocol):
    """Authoritative protocol definition for Django introspection and synthesis service."""

    async def inspect_project(
        self,
        project_path: str,
        settings_module: str | None = None,
        include_models: bool = True,
    ) -> DjangoProjectInfo:
        """Inspect Django project AST, apps, models, settings, and URL patterns."""
        ...

    async def execute_manage(
        self,
        project_path: str,
        command: str,
        args: list[str] | None = None,
        settings_module: str | None = None,
        timeout_sec: float = 30.0,
    ) -> DjangoManageResult:
        """Execute safe Django management command in guarded subprocess."""
        ...

    def generate_model_code(
        self,
        model_name: str,
        fields: list[dict[str, Any]],
        app_label: str = "",
        docstring: str = "",
        meta_options: dict[str, Any] | None = None,
    ) -> str:
        """Generate Python source code for declarative Django Model class."""
        ...

    def simulate_query(
        self,
        query_expr: str,
        model_name: str,
        project_path: str | None = None,
    ) -> DjangoQueryResult:
        """Safely translate and compile Django ORM query expression to SQL."""
        ...

    def validate_template(
        self,
        template_content: str,
        template_path: str | None = None,
        enable_partials: bool = True,
    ) -> DjangoValidationResult:
        """Validate Django template syntax, block tags, partials, and filter pipelines."""
        ...

    async def inspect_tasks(
        self,
        project_path: str,
        backend: str | None = None,
    ) -> list[DjangoTaskInfo]:
        """Introspect Django 6.x background tasks defined across apps."""
        ...
