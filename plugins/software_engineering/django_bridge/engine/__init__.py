"""Django bridge engine subpackage."""

from __future__ import annotations

from .core import DjangoBridgeServiceImpl
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

__all__ = [
    "DjangoBridgeServiceImpl",
    "count_url_patterns",
    "detect_django_version",
    "execute_inspect_project",
    "execute_manage_command",
    "find_settings_file",
    "generate_model_source",
    "inspect_project_tasks",
    "parse_app_models",
    "parse_settings_ast",
    "simulate_orm_query",
    "validate_template_syntax",
]
