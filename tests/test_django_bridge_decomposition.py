"""Tests for Django Bridge Plugin decomposition (plugins/software_engineering/django_bridge).

Verifies:
- Isolated importability and functional correctness of decomposed engine submodules:
  - engine.introspect (AST project scanning, models extraction, settings parsing)
  - engine.manage (Safe subprocess management command runner)
  - engine.generator (Declarative model code generation)
  - engine.simulator (ORM query to SQL compiler)
  - engine.validator (Template syntax & partialdef validator)
  - engine.tasks (Background tasks AST inspector)
  - engine.core (DjangoBridgeServiceImpl coordinator)
- Backward compatibility of main.py facade exports, tool functions, and module singleton plugin (Rule 45)
- Line-count bound on main.py coordinator facade (Rule 11 context budget)
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from plugins.software_engineering.django_bridge.engine.introspect import execute_inspect_project
from plugins.software_engineering.django_bridge.engine.manage import execute_manage_command
from plugins.software_engineering.django_bridge.engine.generator import generate_model_source
from plugins.software_engineering.django_bridge.engine.simulator import simulate_orm_query
from plugins.software_engineering.django_bridge.engine.validator import validate_template_syntax
from plugins.software_engineering.django_bridge.engine.tasks import inspect_project_tasks
from plugins.software_engineering.django_bridge.engine.core import DjangoBridgeServiceImpl as CoreServiceImpl
from plugins.software_engineering.django_bridge.main import (
    DjangoBridgePlugin,
    DjangoBridgeServiceImpl,
    django_inspect_project,
    django_manage_exec,
    django_model_generator,
    django_query_simulator,
    django_task_inspector,
    django_template_validator,
    plugin,
)
from harness.services.django_bridge import DJANGO_BRIDGE_KEY, DjangoBridgeService


def test_isolated_generator_submodule():
    """Verify engine.generator directly creates declarative Django model code."""
    fields = [
        {"name": "title", "type": "CharField", "max_length": 150},
        {"name": "author", "type": "ForeignKey", "related_model": "auth.User", "on_delete": "CASCADE"},
    ]
    code = generate_model_source(
        model_name="Book",
        fields=fields,
        app_label="library",
        docstring="Book catalog entry.",
        meta_options={"db_table": "library_books"},
    )
    assert "class Book(models.Model):" in code
    assert '"""Book catalog entry."""' in code
    assert "title = models.CharField(max_length=150)" in code
    assert "author = models.ForeignKey('auth.User', on_delete=models.CASCADE)" in code
    assert "db_table = 'library_books'" in code


def test_isolated_simulator_submodule():
    """Verify engine.simulator directly compiles ORM queries and detects unsafe calls."""
    res_safe = simulate_orm_query(
        query_expr="Book.objects.filter(is_published=True).order_by('-id')[:10]",
        model_name="Book",
    )
    assert res_safe.is_safe_read_only is True
    assert 'SELECT "books".* FROM "books"' in res_safe.generated_sql
    assert '"books"."is_published" = True' in res_safe.generated_sql
    assert "LIMIT 10" in res_safe.generated_sql

    res_unsafe = simulate_orm_query(
        query_expr="Book.objects.filter(id=1).delete()",
        model_name="Book",
    )
    assert res_unsafe.is_safe_read_only is False


def test_isolated_validator_submodule():
    """Verify engine.validator validates template tags, partialdefs, and catches unclosed tags."""
    valid_template = """
    {% extends "base.html" %}
    {% block main %}
      {% partialdef user_box %}
        <span>{{ user.name|title }}</span>
      {% endpartialdef %}
    {% endblock %}
    """
    res = validate_template_syntax(valid_template, enable_partials=True)
    assert res.valid is True
    assert "user_box" in res.partials_found
    assert "title" in res.filters_found

    invalid_template = """
    <div>
      {% if active %}
        <p>Active</p>
      {% endfor %}
    </div>
    """
    res_err = validate_template_syntax(invalid_template)
    assert res_err.valid is False
    assert any("Mismatched closing tag" in err for err in res_err.errors)


@pytest.mark.asyncio
async def test_isolated_manage_submodule():
    """Verify engine.manage blocks disallowed commands without spawning processes."""
    res = await execute_manage_command(
        project_path=".",
        command="malicious_eval",
        args=[],
    )
    assert res.success is False
    assert "not permitted" in res.stderr


@pytest.mark.asyncio
async def test_isolated_introspect_and_tasks_submodules():
    """Verify engine.introspect and engine.tasks on a temporary mock Django project."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # settings.py
        settings = "INSTALLED_APPS = ['store']\nDATABASES = {'default': {}}"
        (tmp_path / "settings.py").write_text(settings, encoding="utf-8")

        # store app
        store_dir = tmp_path / "store"
        store_dir.mkdir()
        (store_dir / "models.py").write_text(
            "from django.db import models\nclass Product(models.Model):\n    name = models.CharField(max_length=50)\n",
            encoding="utf-8",
        )
        (store_dir / "tasks.py").write_text(
            "def restock_inventory_task(): pass\n",
            encoding="utf-8",
        )

        project_info = await execute_inspect_project(str(tmp_path), include_models=True)
        assert project_info.project_root == str(tmp_path)
        assert any(a.name == "store" for a in project_info.installed_apps)
        assert any(m.name == "Product" for m in project_info.models)

        tasks = await inspect_project_tasks(str(tmp_path))
        assert len(tasks) >= 1
        assert any("restock_inventory" in t.func_name for t in tasks)


def test_facade_backward_compatibility():
    """Verify main.py re-exports, tool wrappers, and plugin singleton."""
    assert DjangoBridgeServiceImpl is CoreServiceImpl
    service = DjangoBridgeServiceImpl()
    assert isinstance(service, DjangoBridgeService)

    # Plugin singleton (Rule 45)
    assert isinstance(plugin, DjangoBridgePlugin)
    assert plugin.name == "plugin.django_bridge"
    assert DJANGO_BRIDGE_KEY in plugin.provides


def test_main_facade_line_count():
    """Verify main.py stays lean under 220 lines (Rule 11 context budget)."""
    main_file = Path("plugins/software_engineering/django_bridge/main.py")
    lines = main_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) < 220, f"main.py should be under 220 lines, but was {len(lines)}"
