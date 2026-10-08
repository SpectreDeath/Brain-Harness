"""In-memory module compilation and callable extraction for dynamic plugins."""

from __future__ import annotations

import ast
import types
from collections.abc import Callable
from typing import Any

import structlog

logger = structlog.get_logger()


def _compile_dynamic_module(
    name: str,
    code: str,
) -> tuple[types.ModuleType, dict[str, Callable[..., Any]]]:
    """Compile and extract callables from raw Python source code.

    Authoritative single execution site for dynamic in-memory plugins.
    """
    # Pre-validate syntax before executing
    try:
        ast.parse(code, filename=f"<dynamic_plugin_{name}>")
    except SyntaxError as e:
        raise ValueError(
            f"Syntax error in dynamic plugin '{name}': {e.msg} (line {e.lineno})"
        ) from e

    module = types.ModuleType(f"dynamic_plugin_{name}")
    try:
        exec(code, module.__dict__)  # noqa: S102
    except Exception as e:
        raise RuntimeError(
            f"Execution error in dynamic plugin '{name}': {e}"
        ) from e

    tools: dict[str, Callable[..., Any]] = {}
    for attr_name in dir(module):
        if not attr_name.startswith("_"):
            attr = getattr(module, attr_name)
            if callable(attr):
                tools[attr_name] = attr

    logger.info("Compiled dynamic in-memory module", name=name, tools_count=len(tools))
    return module, tools
