"""Authoritative Django Bridge Plugin and service coordinator for Brain Harness.

Provides high-leverage Django ecosystem bridges:
- Deep AST project inspection (apps, models, URLs, middleware, settings)
- Safe management command execution in guarded subprocesses
- Declarative model code generation and field mapping
- Django ORM query simulation, SQL compilation, and read-only safety gates
- Template syntax, tag stack balance, partialdef, and filter diagnostics
- Background task queues (django.tasks) introspection
"""

from __future__ import annotations

from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.django_bridge import (
    DJANGO_BRIDGE_KEY,
    DjangoBridgeService,
)

try:
    from plugins.software_engineering.django_bridge.engine import DjangoBridgeServiceImpl
except (ImportError, ValueError):
    from .engine import DjangoBridgeServiceImpl

logger = structlog.get_logger(__name__)


# -----------------------------------------------------------------------------
# Harness Plugin Implementation
# -----------------------------------------------------------------------------

class DjangoBridgePlugin(HarnessPlugin):
    """Authoritative Django Bridge Plugin registering tools and services into Brain Harness."""

    def __init__(self) -> None:
        super().__init__()
        self._service = DjangoBridgeServiceImpl()

    @property
    def name(self) -> str:
        return "plugin.django_bridge"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "High-leverage Django ecosystem bridge for deep AST project inspection, "
            "safe management command execution, model scaffolding, query simulation, "
            "template validation, and background tasks introspection."
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [DJANGO_BRIDGE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(DJANGO_BRIDGE_KEY, self._service)

    async def on_enable(self) -> None:
        logger.info("django_bridge_plugin_enabled", service=DJANGO_BRIDGE_KEY.name)

    async def on_disable(self) -> None:
        logger.info("django_bridge_plugin_disabled")

    async def on_unload(self) -> None:
        pass

    async def enable(self, context: ServiceContext) -> None:
        """Enable plugin and register DJANGO_BRIDGE_KEY service."""
        await self.on_load(context)
        await self.on_enable()

    async def disable(self, context: ServiceContext) -> None:
        """Disable plugin and clean up registrations."""
        await self.on_disable()


# Module-level singleton (Rule 45)
plugin = DjangoBridgePlugin()


# -----------------------------------------------------------------------------
# Top-Level Tool Entrypoints (Callable by Harness agent & StepExecutionEngine)
# -----------------------------------------------------------------------------

async def django_inspect_project(
    project_path: str,
    settings_module: str | None = None,
    include_models: bool = True,
) -> dict[str, Any]:
    """Deep inspection of a Django project: discovers installed apps, models, URLs, middleware, and settings."""
    service = DjangoBridgeServiceImpl()
    result = await service.inspect_project(
        project_path=project_path,
        settings_module=settings_module,
        include_models=include_models,
    )
    return result.to_dict()


async def django_manage_exec(
    project_path: str,
    command: str,
    args: list[str] | None = None,
    settings_module: str | None = None,
    timeout_sec: float = 30.0,
) -> dict[str, Any]:
    """Execute a safe Django management command in a guarded sandbox."""
    service = DjangoBridgeServiceImpl()
    result = await service.execute_manage(
        project_path=project_path,
        command=command,
        args=args,
        settings_module=settings_module,
        timeout_sec=timeout_sec,
    )
    return result.to_dict()


async def django_model_generator(
    model_name: str,
    fields: list[dict[str, Any]],
    app_label: str = "",
    docstring: str = "",
    meta_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Synthesizes declarative Django model classes and fields from JSON/schema specifications."""
    service = DjangoBridgeServiceImpl()
    code = service.generate_model_code(
        model_name=model_name,
        fields=fields,
        app_label=app_label,
        docstring=docstring,
        meta_options=meta_options,
    )
    return {
        "model_name": model_name,
        "app_label": app_label,
        "generated_code": code,
        "fields_count": len(fields),
    }


async def django_query_simulator(
    query_expr: str,
    model_name: str,
    project_path: str | None = None,
) -> dict[str, Any]:
    """Evaluates and compiles Django ORM query expressions into formatted SQL queries."""
    service = DjangoBridgeServiceImpl()
    result = service.simulate_query(
        query_expr=query_expr,
        model_name=model_name,
        project_path=project_path,
    )
    return result.to_dict()


async def django_template_validator(
    template_content: str,
    template_path: str | None = None,
    enable_partials: bool = True,
) -> dict[str, Any]:
    """Validates syntax, tags, template partials ({% partialdef %}), and filters in Django templates."""
    service = DjangoBridgeServiceImpl()
    result = service.validate_template(
        template_content=template_content,
        template_path=template_path,
        enable_partials=enable_partials,
    )
    return result.to_dict()


async def django_task_inspector(
    project_path: str,
    backend: str | None = None,
) -> list[dict[str, Any]]:
    """Introspects and verifies Django 6.x background task queues (django.tasks)."""
    service = DjangoBridgeServiceImpl()
    results = await service.inspect_tasks(
        project_path=project_path,
        backend=backend,
    )
    return [r.to_dict() for r in results]


__all__ = [
    "DjangoBridgePlugin",
    "DjangoBridgeServiceImpl",
    "django_inspect_project",
    "django_manage_exec",
    "django_model_generator",
    "django_query_simulator",
    "django_task_inspector",
    "django_template_validator",
    "plugin",
]
