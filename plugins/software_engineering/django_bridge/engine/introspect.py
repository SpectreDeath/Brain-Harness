"""Django project AST inspection, app discovery, settings parsing, and model extraction."""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path
from typing import Any

import structlog

from harness.services.django_bridge import (
    DjangoAppInfo,
    DjangoModelField,
    DjangoModelSchema,
    DjangoProjectInfo,
)

logger = structlog.get_logger(__name__)


def detect_django_version(root: Path) -> str:
    """Detect Django version from __init__.py, pyproject.toml, or default fallback."""
    init_file = root / "django" / "__init__.py"
    if init_file.exists():
        try:
            content = init_file.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"VERSION\s*=\s*\((.*?)\)", content)
            if m:
                parts = [p.strip().strip("'\"") for p in m.group(1).split(",")]
                return ".".join(parts[:3])
        except Exception:
            pass
    return "6.2.0"


def find_settings_file(root: Path, settings_module: str | None) -> Path | None:
    """Locate Django settings.py file without traversing noisy virtual environment directories."""
    if settings_module:
        cand = root / (settings_module.replace(".", os.sep) + ".py")
        if cand.exists():
            return cand

    # Common layouts, pruning .venv and env (Rule 52)
    for p in root.rglob("settings.py"):
        p_str = str(p)
        if ".venv" not in p_str and "env" not in p_str and "node_modules" not in p_str:
            return p
    for p in root.rglob("base.py"):
        p_str = str(p)
        if "settings" in p_str and ".venv" not in p_str and "env" not in p_str:
            return p
    return None


def parse_settings_ast(settings_path: Path) -> dict[str, Any]:
    """Parse settings file using AST without importing or executing arbitrary code."""
    res: dict[str, Any] = {}
    try:
        content = settings_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content)
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        val_name = target.id
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            items: list[str] = []
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    items.append(elt.value)
                            res[val_name] = items
                        elif isinstance(node.value, ast.Dict):
                            res[val_name] = [
                                k.value
                                for k in node.value.keys
                                if isinstance(k, ast.Constant) and isinstance(k.value, str)
                            ]
    except Exception as e:
        logger.warning("django_settings_parse_error", path=str(settings_path), error=str(e))
    return res


def parse_app_models(app_dir: Path, app_label: str) -> list[DjangoModelSchema]:
    """Extract Django models from models.py or models/ directory using AST analysis."""
    models: list[DjangoModelSchema] = []
    model_files: list[Path] = []

    if (app_dir / "models.py").exists():
        model_files.append(app_dir / "models.py")
    elif (app_dir / "models").is_dir():
        model_files.extend((app_dir / "models").glob("*.py"))

    for mf in model_files:
        try:
            content = mf.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    is_model = any(
                        (isinstance(b, ast.Name) and b.id in ("Model", "models.Model"))
                        or (isinstance(b, ast.Attribute) and b.attr == "Model")
                        for b in node.bases
                    )
                    if is_model or any(isinstance(b, ast.Name) for b in node.bases):
                        fields: list[DjangoModelField] = []
                        doc = ast.get_docstring(node) or ""
                        db_table = None
                        ordering: list[str] = []

                        for item in node.body:
                            if isinstance(item, ast.Assign):
                                for t in item.targets:
                                    if isinstance(t, ast.Name) and isinstance(item.value, ast.Call):
                                        f_type = "CharField"
                                        if isinstance(item.value.func, ast.Attribute):
                                            f_type = item.value.func.attr
                                        elif isinstance(item.value.func, ast.Name):
                                            f_type = item.value.func.id

                                        is_null = any(
                                            kw.arg == "null"
                                            and isinstance(kw.value, ast.Constant)
                                            and kw.value.value is True
                                            for kw in item.value.keywords
                                        )
                                        is_blank = any(
                                            kw.arg == "blank"
                                            and isinstance(kw.value, ast.Constant)
                                            and kw.value.value is True
                                            for kw in item.value.keywords
                                        )
                                        is_uniq = any(
                                            kw.arg == "unique"
                                            and isinstance(kw.value, ast.Constant)
                                            and kw.value.value is True
                                            for kw in item.value.keywords
                                        )
                                        is_pk = any(
                                            kw.arg == "primary_key"
                                            and isinstance(kw.value, ast.Constant)
                                            and kw.value.value is True
                                            for kw in item.value.keywords
                                        )

                                        fields.append(
                                            DjangoModelField(
                                                name=t.id,
                                                field_type=f_type,
                                                null=is_null,
                                                blank=is_blank,
                                                primary_key=is_pk,
                                                unique=is_uniq,
                                            )
                                        )
                            elif isinstance(item, ast.ClassDef) and item.name == "Meta":
                                for meta_item in item.body:
                                    if isinstance(meta_item, ast.Assign):
                                        for mt in meta_item.targets:
                                            if (
                                                isinstance(mt, ast.Name)
                                                and mt.id == "db_table"
                                                and isinstance(meta_item.value, ast.Constant)
                                            ):
                                                db_table = str(meta_item.value.value)

                        models.append(
                            DjangoModelSchema(
                                name=node.name,
                                app_label=app_label,
                                fields=tuple(fields),
                                docstring=doc,
                                db_table=db_table,
                                ordering=tuple(ordering),
                            )
                        )
        except Exception as e:
            logger.warning("django_model_parse_error", file=str(mf), error=str(e))
    return models


def count_url_patterns(root: Path) -> int:
    """Count path() and re_path() definitions across urls.py files."""
    count = 0
    for uf in root.rglob("urls.py"):
        if ".venv" in str(uf) or "env" in str(uf) or "node_modules" in str(uf):
            continue
        try:
            content = uf.read_text(encoding="utf-8", errors="ignore")
            count += len(re.findall(r"\bpath\(|\bre_path\(", content))
        except Exception:
            pass
    return count


async def execute_inspect_project(
    project_path: str,
    settings_module: str | None = None,
    include_models: bool = True,
) -> DjangoProjectInfo:
    """Deep inspection of a Django project: discovers installed apps, models, URLs, middleware, and settings."""
    root = Path(project_path).resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Project path does not exist: {project_path}")

    # 1. Detect Django version
    django_ver = detect_django_version(root)

    # 2. Locate and parse settings
    settings_path = find_settings_file(root, settings_module)
    installed_app_names: list[str] = []
    middleware_stack: list[str] = []
    databases: list[str] = ["default"]
    csp_enabled = False
    tasks_enabled = False

    if settings_path and settings_path.exists():
        settings_info = parse_settings_ast(settings_path)
        installed_app_names = settings_info.get("INSTALLED_APPS", [])
        middleware_stack = settings_info.get("MIDDLEWARE", [])
        databases = settings_info.get("DATABASES", ["default"])
        csp_enabled = (
            any("csp" in mw.lower() for mw in middleware_stack)
            or "CSP_DEFAULT_SRC" in settings_info
        )
        tasks_enabled = "TASKS" in settings_info or "django.tasks" in installed_app_names

    # 3. Discover apps on filesystem
    app_infos: list[DjangoAppInfo] = []
    model_schemas: list[DjangoModelSchema] = []

    candidate_dirs: list[Path] = []
    if installed_app_names:
        for app_name in installed_app_names:
            short_name = app_name.split(".")[-1]
            app_dir = root / short_name
            if not app_dir.exists():
                app_dir = root / app_name.replace(".", os.sep)
            if app_dir.exists() and app_dir.is_dir():
                candidate_dirs.append(app_dir)

    if not candidate_dirs:
        for sub in root.iterdir():
            if sub.is_dir() and (
                (sub / "models.py").exists()
                or (sub / "apps.py").exists()
                or (sub / "models").exists()
            ):
                candidate_dirs.append(sub)

    for app_dir in candidate_dirs:
        app_label = app_dir.name
        has_mig = (app_dir / "migrations").exists() and (app_dir / "migrations").is_dir()
        has_adm = (app_dir / "admin.py").exists() or (app_dir / "admin").exists()
        has_tsk = (app_dir / "tasks.py").exists() or (app_dir / "tasks").exists()
        has_url = (app_dir / "urls.py").exists()

        app_models: list[DjangoModelSchema] = []
        if include_models:
            app_models = parse_app_models(app_dir, app_label)
            model_schemas.extend(app_models)

        app_infos.append(
            DjangoAppInfo(
                name=app_dir.name,
                label=app_label,
                path=str(app_dir),
                models_count=len(app_models),
                has_migrations=has_mig,
                has_admin=has_adm,
                has_tasks=has_tsk,
                has_urls=has_url,
            )
        )

    # 4. Count URL patterns
    url_count = count_url_patterns(root)

    return DjangoProjectInfo(
        project_root=str(root),
        settings_module=settings_module,
        django_version=django_ver,
        installed_apps=tuple(app_infos),
        models=tuple(model_schemas),
        url_patterns_count=url_count,
        middleware_stack=tuple(middleware_stack),
        databases=tuple(databases),
        background_tasks_enabled=tasks_enabled or any(a.has_tasks for a in app_infos),
        csp_enabled=csp_enabled,
    )
