"""Django 6.x background tasks AST inspection."""

from __future__ import annotations

import ast
from pathlib import Path

import structlog

from harness.services.django_bridge import DjangoTaskInfo

logger = structlog.get_logger(__name__)


async def inspect_project_tasks(
    project_path: str,
    backend: str | None = None,
) -> list[DjangoTaskInfo]:
    """Introspect Django 6.x background tasks across apps via AST analysis."""
    root = Path(project_path).resolve()
    task_infos: list[DjangoTaskInfo] = []

    task_files: list[Path] = []
    for tf in root.rglob("tasks.py"):
        if ".venv" not in str(tf) and "env" not in str(tf) and "node_modules" not in str(tf):
            task_files.append(tf)

    for tf in task_files:
        try:
            content = tf.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    is_task = any(
                        "task" in d.id.lower()
                        for d in node.decorator_list
                        if isinstance(d, ast.Name)
                    ) or "task" in node.name.lower()

                    if is_task:
                        doc = ast.get_docstring(node) or ""
                        mod_name = tf.stem
                        task_infos.append(
                            DjangoTaskInfo(
                                task_name=node.name,
                                module=mod_name,
                                func_name=node.name,
                                queue="default",
                                backend=backend or "immediate",
                                docstring=doc,
                            )
                        )
        except Exception as e:
            logger.warning("django_tasks_parse_error", file=str(tf), error=str(e))

    return task_infos
