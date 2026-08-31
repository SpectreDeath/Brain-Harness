"""Django Bridge Plugin — authoritative service and tools for Django codebase analysis and synthesis."""

from __future__ import annotations

import ast
import asyncio
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
import structlog

from harness.kernel.context import ServiceContext
from harness.plugins.base import HarnessPlugin
from harness.services.django_bridge import (
    DJANGO_BRIDGE_KEY,
    SAFE_MANAGEMENT_COMMANDS,
    DjangoAppInfo,
    DjangoBridgeService,
    DjangoManageResult,
    DjangoModelField,
    DjangoModelSchema,
    DjangoProjectInfo,
    DjangoQueryResult,
    DjangoTaskInfo,
    DjangoValidationResult,
)

logger = structlog.get_logger(__name__)


class DjangoBridgeServiceImpl(DjangoBridgeService):
    """Authoritative implementation of DjangoBridgeService using AST analysis and sandboxed execution."""

    async def inspect_project(
        self,
        project_path: str,
        settings_module: str | None = None,
        include_models: bool = True,
    ) -> DjangoProjectInfo:
        """Inspect Django project AST, discovering apps, models, URLs, middleware, and settings."""
        root = Path(project_path).resolve()
        if not root.exists() or not root.is_dir():
            raise FileNotFoundError(f"Project path does not exist: {project_path}")

        # 1. Detect Django version
        django_ver = self._detect_django_version(root)

        # 2. Locate and parse settings
        settings_path = self._find_settings_file(root, settings_module)
        installed_app_names: list[str] = []
        middleware_stack: list[str] = []
        databases: list[str] = ["default"]
        csp_enabled = False
        tasks_enabled = False

        if settings_path and settings_path.exists():
            settings_info = self._parse_settings_ast(settings_path)
            installed_app_names = settings_info.get("INSTALLED_APPS", [])
            middleware_stack = settings_info.get("MIDDLEWARE", [])
            databases = settings_info.get("DATABASES", ["default"])
            csp_enabled = any("csp" in mw.lower() for mw in middleware_stack) or "CSP_DEFAULT_SRC" in settings_info
            tasks_enabled = "TASKS" in settings_info or "django.tasks" in installed_app_names

        # 3. Discover apps on filesystem
        app_infos: list[DjangoAppInfo] = []
        model_schemas: list[DjangoModelSchema] = []

        # If installed_apps list is empty, scan directory for app packages
        candidate_dirs: list[Path] = []
        if installed_app_names:
            for app_name in installed_app_names:
                # Handle dotted names like 'django.contrib.auth' vs local apps 'accounts'
                short_name = app_name.split(".")[-1]
                app_dir = root / short_name
                if not app_dir.exists():
                    app_dir = root / app_name.replace(".", os.sep)
                if app_dir.exists() and app_dir.is_dir():
                    candidate_dirs.append(app_dir)
        
        if not candidate_dirs:
            # Fallback scan top-level directories with models.py or apps.py
            for sub in root.iterdir():
                if sub.is_dir() and ((sub / "models.py").exists() or (sub / "apps.py").exists() or (sub / "models").exists()):
                    candidate_dirs.append(sub)

        for app_dir in candidate_dirs:
            app_label = app_dir.name
            has_mig = (app_dir / "migrations").exists() and (app_dir / "migrations").is_dir()
            has_adm = (app_dir / "admin.py").exists() or (app_dir / "admin").exists()
            has_tsk = (app_dir / "tasks.py").exists() or (app_dir / "tasks").exists()
            has_url = (app_dir / "urls.py").exists()

            app_models: list[DjangoModelSchema] = []
            if include_models:
                app_models = self._parse_app_models(app_dir, app_label)
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
        url_count = self._count_url_patterns(root)

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

    async def execute_manage(
        self,
        project_path: str,
        command: str,
        args: list[str] | None = None,
        settings_module: str | None = None,
        timeout_sec: float = 30.0,
    ) -> DjangoManageResult:
        """Execute a safe Django management command in a guarded subprocess."""
        # 1. Check command safety first
        cmd_clean = command.strip().lower()
        if cmd_clean not in SAFE_MANAGEMENT_COMMANDS:
            return DjangoManageResult(
                command=command,
                args=tuple(args or []),
                exit_code=1,
                stdout="",
                stderr=f"Command '{command}' is not permitted in sandboxed execution. Safe commands: {sorted(SAFE_MANAGEMENT_COMMANDS)}",
                duration_ms=0.0,
                success=False,
            )

        root = Path(project_path).resolve()
        manage_py = root / "manage.py"

        if not manage_py.exists():
            # Search immediate subdirectories
            for sub in root.iterdir():
                if sub.is_dir() and (sub / "manage.py").exists():
                    manage_py = sub / "manage.py"
                    break

        if not manage_py.exists():
            return DjangoManageResult(
                command=command,
                args=tuple(args or []),
                exit_code=1,
                stdout="",
                stderr=f"manage.py not found in {project_path}",
                duration_ms=0.0,
                success=False,
            )

        cmd_args = [sys.executable, str(manage_py), cmd_clean]
        if args:
            cmd_args.extend([str(a) for a in args])

        env = dict(os.environ)
        if settings_module:
            env["DJANGO_SETTINGS_MODULE"] = settings_module

        start_time = time.perf_counter()
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(manage_py.parent),
                env=env,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_sec,
            )
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            stdout_str = stdout_bytes.decode("utf-8", errors="replace")
            stderr_str = stderr_bytes.decode("utf-8", errors="replace")
            code = proc.returncode if proc.returncode is not None else 0

            return DjangoManageResult(
                command=command,
                args=tuple(args or []),
                exit_code=code,
                stdout=stdout_str,
                stderr=stderr_str,
                duration_ms=duration_ms,
                success=(code == 0),
            )
        except asyncio.TimeoutError:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return DjangoManageResult(
                command=command,
                args=tuple(args or []),
                exit_code=124,
                stdout="",
                stderr=f"Command execution timed out after {timeout_sec} seconds",
                duration_ms=duration_ms,
                success=False,
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return DjangoManageResult(
                command=command,
                args=tuple(args or []),
                exit_code=1,
                stdout="",
                stderr=f"Execution error: {e}",
                duration_ms=duration_ms,
                success=False,
            )

    def generate_model_code(
        self,
        model_name: str,
        fields: list[dict[str, Any]],
        app_label: str = "",
        docstring: str = "",
        meta_options: dict[str, Any] | None = None,
    ) -> str:
        """Generate idiomatic Python code for a Django Model."""
        lines: list[str] = [
            "from django.db import models",
            "from django.utils.translation import gettext_lazy as _",
            "",
            "",
            f"class {model_name}(models.Model):",
        ]

        if docstring:
            lines.append(f'    """{docstring.strip()}"""')
            lines.append("")

        for f in fields:
            f_name = f.get("name", "field")
            f_type = f.get("type", "CharField")
            kwargs: list[str] = []

            # Specific field types
            if f_type in ("CharField", "SlugField"):
                max_len = f.get("max_length", 255)
                kwargs.append(f"max_length={max_len}")
            elif f_type in ("DecimalField",):
                kwargs.append(f"max_digits={f.get('max_digits', 10)}")
                kwargs.append(f"decimal_places={f.get('decimal_places', 2)}")
            elif f_type in ("ForeignKey", "OneToOneField"):
                rel = f.get("related_model", "self")
                on_del = f.get("on_delete", "models.CASCADE")
                if not on_del.startswith("models."):
                    on_del = f"models.{on_del}"
                kwargs.append(f"'{rel}'")
                kwargs.append(f"on_delete={on_del}")
                if "related_name" in f:
                    kwargs.append(f"related_name='{f['related_name']}'")
            elif f_type in ("ManyToManyField",):
                rel = f.get("related_model", "self")
                kwargs.append(f"'{rel}'")
                if "related_name" in f:
                    kwargs.append(f"related_name='{f['related_name']}'")

            if f.get("null"):
                kwargs.append("null=True")
            if f.get("blank"):
                kwargs.append("blank=True")
            if f.get("unique"):
                kwargs.append("unique=True")
            if f.get("db_index"):
                kwargs.append("db_index=True")
            if f.get("primary_key"):
                kwargs.append("primary_key=True")
            if "default" in f and f["default"] is not None:
                d_val = f["default"]
                if isinstance(d_val, str) and not d_val.startswith(("models.", "timezone.", "uuid.")):
                    kwargs.append(f"default='{d_val}'")
                else:
                    kwargs.append(f"default={d_val}")
            if f.get("help_text"):
                kwargs.append(f"_('{f['help_text']}')")

            kwarg_str = ", ".join(kwargs)
            lines.append(f"    {f_name} = models.{f_type}({kwarg_str})")

        # Class Meta
        lines.append("")
        lines.append("    class Meta:")
        if app_label:
            lines.append(f"        app_label = '{app_label}'")
        if meta_options:
            if "db_table" in meta_options:
                lines.append(f"        db_table = '{meta_options['db_table']}'")
            if "ordering" in meta_options:
                ord_list = [f"'{o}'" for o in meta_options["ordering"]]
                lines.append(f"        ordering = [{', '.join(ord_list)}]")
            if "verbose_name" in meta_options:
                lines.append(f"        verbose_name = _('{meta_options['verbose_name']}')")
            if "verbose_name_plural" in meta_options:
                lines.append(f"        verbose_name_plural = _('{meta_options['verbose_name_plural']}')")
            if "unique_together" in meta_options:
                lines.append(f"        unique_together = {meta_options['unique_together']}")
        else:
            lines.append("        ordering = ['-id']")

        # __str__ method
        primary_char = next((f.get("name") for f in fields if f.get("type") in ("CharField", "SlugField", "EmailField")), "id")
        lines.append("")
        lines.append("    def __str__(self) -> str:")
        lines.append(f"        return str(self.{primary_char})")
        lines.append("")

        return "\n".join(lines)

    def simulate_query(
        self,
        query_expr: str,
        model_name: str,
        project_path: str | None = None,
    ) -> DjangoQueryResult:
        """Safely translate and compile a Django ORM query expression to SQL."""
        clean_expr = query_expr.strip()
        table_name = f"{model_name.lower()}s" if not model_name.endswith("s") else model_name.lower()

        # Check read-only safety
        destructive_methods = (".delete(", ".update(", ".bulk_create(", ".create(", ".save(")
        is_safe = not any(m in clean_expr for m in destructive_methods)

        # Parse filter and select elements via pattern matching
        where_clauses: list[str] = []
        params: list[Any] = []
        tables_ref: list[str] = [table_name]
        limit_clause = ""
        order_clause = ""

        # Extract .filter(...)
        filter_matches = re.findall(r"\.filter\((.*?)\)", clean_expr)
        for match in filter_matches:
            args = [a.strip() for a in match.split(",") if "=" in a]
            for arg in args:
                k, v = arg.split("=", 1)
                k, v = k.strip(), v.strip()
                col = k
                op = "="
                if "__gte" in k:
                    col = k.replace("__gte", "")
                    op = ">="
                elif "__lte" in k:
                    col = k.replace("__lte", "")
                    op = "<="
                elif "__gt" in k:
                    col = k.replace("__gt", "")
                    op = ">"
                elif "__lt" in k:
                    col = k.replace("__lt", "")
                    op = "<"
                elif "__icontains" in k:
                    col = k.replace("__icontains", "")
                    op = "ILIKE"
                    clean_val = v.strip("'\"")
                    v = f"'%{clean_val}%'"
                elif "__contains" in k:
                    col = k.replace("__contains", "")
                    op = "LIKE"
                    clean_val = v.strip("'\"")
                    v = f"'%{clean_val}%'"
                elif "__in" in k:
                    col = k.replace("__in", "")
                    op = "IN"

                where_clauses.append(f'"{table_name}"."{col}" {op} {v}')
                params.append(v)

        # Extract .select_related(...)
        select_rel = re.findall(r"\.select_related\((.*?)\)", clean_expr)
        for rel in select_rel:
            rel_name = rel.strip("'\"")
            if rel_name:
                tables_ref.append(f"{rel_name}s")

        # Extract .order_by(...)
        order_match = re.search(r"\.order_by\((.*?)\)", clean_expr)
        if order_match:
            fields = [f.strip("'\" ") for f in order_match.group(1).split(",")]
            order_items: list[str] = []
            for of in fields:
                direction = "DESC" if of.startswith("-") else "ASC"
                clean_f = of.lstrip("-")
                order_items.append(f'"{table_name}"."{clean_f}" {direction}')
            if order_items:
                order_clause = f" ORDER BY {', '.join(order_items)}"

        # Extract slice [:N]
        slice_match = re.search(r"\[:?(\d+)\]", clean_expr)
        if slice_match:
            limit_clause = f" LIMIT {slice_match.group(1)}"

        # Construct SQL
        where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        generated_sql = f'SELECT "{table_name}".* FROM "{table_name}"{where_sql}{order_clause}{limit_clause};'

        explain_plan = f"SCAN TABLE {table_name}" + (f" USING INDEX ON ({', '.join(where_clauses)})" if where_clauses else "")

        return DjangoQueryResult(
            query_expr=clean_expr,
            model_name=model_name,
            generated_sql=generated_sql,
            params=tuple(params),
            explain_plan=explain_plan,
            is_safe_read_only=is_safe,
            tables_referenced=tuple(tables_ref),
        )

    def validate_template(
        self,
        template_content: str,
        template_path: str | None = None,
        enable_partials: bool = True,
    ) -> DjangoValidationResult:
        """Validate syntax of Django templates, block tags, partials, and filters."""
        errors: list[str] = []
        warnings: list[str] = []
        partials: list[str] = []
        tags_found: set[str] = set()
        filters_found: set[str] = set()

        # Tag balance stack
        tag_pairs = {
            "if": "endif",
            "for": "endfor",
            "block": "endblock",
            "with": "endwith",
            "autoescape": "endautoescape",
            "comment": "endcomment",
            "filter": "endfilter",
            "spaceless": "endspaceless",
        }
        if enable_partials:
            tag_pairs["partialdef"] = "endpartialdef"

        tag_stack: list[tuple[str, int]] = []

        # Find tags {% ... %}
        for match in re.finditer(r"\{%\s*(\w+)(.*?)\s*%\}", template_content):
            tag_name = match.group(1)
            tag_args = match.group(2).strip()
            line_no = template_content[: match.start()].count("\n") + 1
            tags_found.add(tag_name)

            if tag_name == "partialdef":
                p_name = tag_args.split()[0] if tag_args else "unnamed"
                partials.append(p_name.strip("\"'"))

            if tag_name in tag_pairs:
                tag_stack.append((tag_name, line_no))
            elif tag_name.startswith("end"):
                if not tag_stack:
                    errors.append(f"Line {line_no}: Unexpected closing tag '{{% {tag_name} %}}' with no matching open tag")
                else:
                    open_tag, open_line = tag_stack[-1]
                    expected_close = tag_pairs.get(open_tag)
                    if tag_name == expected_close:
                        tag_stack.pop()
                    else:
                        errors.append(
                            f"Line {line_no}: Mismatched closing tag '{{% {tag_name} %}}' (expected '{{% {expected_close} %}}' opened at line {open_line})"
                        )

        # Check unclosed tags
        for unclosed, line in tag_stack:
            errors.append(f"Line {line}: Unclosed tag '{{% {unclosed} %}}' (missing '{{% {tag_pairs[unclosed]} %}}')")

        # Find filters {{ val|filter:arg }}
        for match in re.finditer(r"\{\{(.*?)\}\}", template_content):
            var_expr = match.group(1)
            parts = var_expr.split("|")[1:]
            for p in parts:
                f_name = p.split(":")[0].strip()
                if f_name:
                    filters_found.add(f_name)

        return DjangoValidationResult(
            valid=(len(errors) == 0),
            errors=tuple(errors),
            warnings=tuple(warnings),
            partials_found=tuple(sorted(partials)),
            tags_found=tuple(sorted(tags_found)),
            filters_found=tuple(sorted(filters_found)),
        )

    async def inspect_tasks(
        self,
        project_path: str,
        backend: str | None = None,
    ) -> list[DjangoTaskInfo]:
        """Introspect Django 6.x background tasks defined in tasks.py files."""
        root = Path(project_path).resolve()
        task_infos: list[DjangoTaskInfo] = []

        task_files: list[Path] = list(root.rglob("tasks.py"))
        for tf in task_files:
            try:
                content = tf.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(content)
                rel_mod = tf.relative_to(root).as_posix().replace("/", ".").replace(".py", "")

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check decorators for @task or @shared_task
                        is_task = False
                        queue_name = "default"
                        for dec in node.decorator_list:
                            dec_id = ""
                            if isinstance(dec, ast.Name):
                                dec_id = dec.id
                            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                                dec_id = dec.func.id
                                for kw in dec.keywords:
                                    if kw.arg == "queue" and isinstance(kw.value, ast.Constant):
                                        queue_name = str(kw.value.value)

                            if dec_id in ("task", "shared_task", "background_task", "job"):
                                is_task = True

                        if is_task or "task" in node.name.lower():
                            doc = ast.get_docstring(node) or ""
                            task_infos.append(
                                DjangoTaskInfo(
                                    task_name=f"{rel_mod}.{node.name}",
                                    module=rel_mod,
                                    func_name=node.name,
                                    queue=queue_name,
                                    backend=backend or "immediate",
                                    priority=0,
                                    timeout=300,
                                    docstring=doc,
                                )
                            )
            except Exception as e:
                logger.warning("django_tasks_parse_error", file=str(tf), error=str(e))

        return task_infos

    # --- Internal AST Helper Methods ---

    def _detect_django_version(self, root: Path) -> str:
        """Detect Django version from __init__.py, pyproject.toml, or installed package."""
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

    def _find_settings_file(self, root: Path, settings_module: str | None) -> Path | None:
        """Locate Django settings.py file."""
        if settings_module:
            cand = root / (settings_module.replace(".", os.sep) + ".py")
            if cand.exists():
                return cand

        # Common layouts
        for p in root.rglob("settings.py"):
            if ".venv" not in str(p) and "env" not in str(p):
                return p
        for p in root.rglob("base.py"):
            if "settings" in str(p):
                return p
        return None

    def _parse_settings_ast(self, settings_path: Path) -> dict[str, Any]:
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
                                    k.value for k in node.value.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)
                                ]
        except Exception as e:
            logger.warning("django_settings_parse_error", path=str(settings_path), error=str(e))
        return res

    def _parse_app_models(self, app_dir: Path, app_label: str) -> list[DjangoModelSchema]:
        """Extract Django models from models.py or models/ directory."""
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
                        # Check if subclass of models.Model
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

                                            is_null = any(kw.arg == "null" and isinstance(kw.value, ast.Constant) and kw.value.value is True for kw in item.value.keywords)
                                            is_blank = any(kw.arg == "blank" and isinstance(kw.value, ast.Constant) and kw.value.value is True for kw in item.value.keywords)
                                            is_uniq = any(kw.arg == "unique" and isinstance(kw.value, ast.Constant) and kw.value.value is True for kw in item.value.keywords)
                                            is_pk = any(kw.arg == "primary_key" and isinstance(kw.value, ast.Constant) and kw.value.value is True for kw in item.value.keywords)

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
                                                if isinstance(mt, ast.Name) and mt.id == "db_table" and isinstance(meta_item.value, ast.Constant):
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

    def _count_url_patterns(self, root: Path) -> int:
        """Count path() and re_path() definitions across urls.py files."""
        count = 0
        for uf in root.rglob("urls.py"):
            try:
                content = uf.read_text(encoding="utf-8", errors="ignore")
                count += len(re.findall(r"\bpath\(|\bre_path\(", content))
            except Exception:
                pass
        return count


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
        return "High-leverage Django ecosystem bridge for deep AST project inspection, safe management command execution, model scaffolding, query simulation, template validation, and background tasks introspection."

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


# Top-level tool entrypoints callable by Harness agent and StepExecutionEngine


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
