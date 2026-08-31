"""Unit and integration tests for the Django Bridge Plugin and Service."""

import pytest
from pathlib import Path
import tempfile
import shutil

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.django_bridge import (
    DJANGO_BRIDGE_KEY,
    DjangoBridgeService,
    DjangoModelField,
    DjangoModelSchema,
)
from plugins.software_engineering.django_bridge.main import (
    DjangoBridgePlugin,
    DjangoBridgeServiceImpl,
    django_inspect_project,
    django_manage_exec,
    django_model_generator,
    django_query_simulator,
    django_task_inspector,
    django_template_validator,
)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_plugin_manifest_validation() -> None:
    """Validate that plugin.django_bridge manifest passes all PluginValidator checks."""
    plugin_dir = Path("plugins/software_engineering/django_bridge")
    assert plugin_dir.exists(), "Plugin directory must exist"

    report = await PluginValidator.validate(plugin_dir)
    assert report.valid, f"Plugin manifest validation failed: {report.errors}"
    assert len(report.errors) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_plugin_lifecycle_and_service_registration() -> None:
    """Test enabling and disabling DjangoBridgePlugin registers DJANGO_BRIDGE_KEY into context."""
    context = ServiceContext()
    plugin = DjangoBridgePlugin()

    await plugin.enable(context)
    service = context.require(DJANGO_BRIDGE_KEY)
    assert service is not None
    assert isinstance(service, DjangoBridgeService)

    await plugin.disable(context)


@pytest.mark.unit
def test_model_generator_basic_and_relations() -> None:
    """Test generating Django model code with various field types, relations, and Meta options."""
    service = DjangoBridgeServiceImpl()

    fields = [
        {"name": "title", "type": "CharField", "max_length": 200},
        {"name": "slug", "type": "SlugField", "unique": True},
        {"name": "author", "type": "ForeignKey", "related_model": "auth.User", "on_delete": "CASCADE", "related_name": "posts"},
        {"name": "tags", "type": "ManyToManyField", "related_model": "taggit.Tag", "blank": True},
        {"name": "price", "type": "DecimalField", "max_digits": 8, "decimal_places": 2, "null": True, "blank": True},
        {"name": "is_active", "type": "BooleanField", "default": True},
    ]

    code = service.generate_model_code(
        model_name="BlogPost",
        fields=fields,
        app_label="blog",
        docstring="Blog post model with relations and price.",
        meta_options={
            "db_table": "custom_blog_posts",
            "ordering": ["-id", "title"],
            "verbose_name": "Blog Post",
        },
    )

    assert "class BlogPost(models.Model):" in code
    assert '"""Blog post model with relations and price."""' in code
    assert "title = models.CharField(max_length=200)" in code
    assert "slug = models.SlugField(max_length=255, unique=True)" in code
    assert "author = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='posts')" in code
    assert "tags = models.ManyToManyField('taggit.Tag', blank=True)" in code
    assert "price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)" in code
    assert "is_active = models.BooleanField(default=True)" in code
    assert "app_label = 'blog'" in code
    assert "db_table = 'custom_blog_posts'" in code
    assert "ordering = ['-id', 'title']" in code
    assert "def __str__(self) -> str:" in code
    assert "return str(self.title)" in code


@pytest.mark.unit
def test_query_simulator_filters_and_limits() -> None:
    """Test translating Django ORM query expression to SQL AST and explain plan."""
    service = DjangoBridgeServiceImpl()

    query_expr = "Article.objects.filter(is_published=True, views__gte=100, title__icontains='django').select_related('author').order_by('-created_at')[:25]"
    result = service.simulate_query(query_expr=query_expr, model_name="Article")

    assert result.is_safe_read_only is True
    assert result.model_name == "Article"
    assert 'SELECT "articles".* FROM "articles"' in result.generated_sql
    assert '"articles"."is_published" = True' in result.generated_sql
    assert '"articles"."views" >= 100' in result.generated_sql
    assert 'LIMIT 25' in result.generated_sql
    assert 'ORDER BY "articles"."created_at" DESC' in result.generated_sql
    assert "authors" in result.tables_referenced


@pytest.mark.unit
def test_query_simulator_destructive_detection() -> None:
    """Test that destructive methods like delete() are flagged as not read-only safe."""
    service = DjangoBridgeServiceImpl()
    result = service.simulate_query(query_expr="Article.objects.filter(is_published=False).delete()", model_name="Article")
    assert result.is_safe_read_only is False


@pytest.mark.unit
def test_template_validator_valid_and_partials() -> None:
    """Test validating Django template syntax including Django 6.x partialdef tags."""
    service = DjangoBridgeServiceImpl()

    template = """
    {% extends "base.html" %}
    {% load static %}
    {% block content %}
      <div class="container">
        {% if user.is_authenticated %}
          <p>Welcome, {{ user.username|upper }}!</p>
          {% partialdef user_widget %}
            <div class="user-widget">
              <span>{{ user.email|lower }}</span>
            </div>
          {% endpartialdef %}
        {% endif %}
      </div>
    {% endblock %}
    """

    res = service.validate_template(template_content=template, enable_partials=True)
    assert res.valid is True
    assert len(res.errors) == 0
    assert "user_widget" in res.partials_found
    assert "if" in res.tags_found
    assert "block" in res.tags_found
    assert "upper" in res.filters_found or "lower" in res.filters_found


@pytest.mark.unit
def test_template_validator_mismatched_and_unclosed_tags() -> None:
    """Test syntax error detection for mismatched and unclosed tags."""
    service = DjangoBridgeServiceImpl()

    broken_template = """
    <div>
      {% if condition %}
        <p>Text</p>
      {% endfor %}
    </div>
    """

    res = service.validate_template(template_content=broken_template)
    assert res.valid is False
    assert any("Mismatched closing tag" in err for err in res.errors)

    unclosed_template = """
    <div>
      {% for item in items %}
        <p>{{ item }}</p>
    </div>
    """
    res2 = service.validate_template(template_content=unclosed_template)
    assert res2.valid is False
    assert any("Unclosed tag" in err for err in res2.errors)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_inspect_project_mock_and_tool_wrapper() -> None:
    """Test inspect_project and top-level tool functions on a mock Django project tree."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create settings.py
        settings_code = """
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'myapp',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]
DATABASES = {
    'default': {'ENGINE': 'django.db.backends.sqlite3'}
}
"""
        (tmp_path / "settings.py").write_text(settings_code, encoding="utf-8")

        # Create app directory
        app_dir = tmp_path / "myapp"
        app_dir.mkdir()
        (app_dir / "__init__.py").write_text("", encoding="utf-8")
        (app_dir / "apps.py").write_text("class MyappConfig: name = 'myapp'", encoding="utf-8")

        models_code = """
from django.db import models

class Item(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)

    class Meta:
        db_table = "store_items"
"""
        (app_dir / "models.py").write_text(models_code, encoding="utf-8")

        # Create tasks.py
        tasks_code = """
def process_order_task(order_id: int):
    pass
"""
        (app_dir / "tasks.py").write_text(tasks_code, encoding="utf-8")

        # Test tool invocation
        inspect_res = await django_inspect_project(project_path=str(tmp_path))
        assert inspect_res["project_root"] == str(tmp_path)
        assert len(inspect_res["installed_apps"]) >= 1
        assert any(a["name"] == "myapp" for a in inspect_res["installed_apps"])

        # Check models extracted
        assert len(inspect_res["models"]) >= 1
        item_model = next((m for m in inspect_res["models"] if m["name"] == "Item"), None)
        assert item_model is not None
        assert item_model["db_table"] == "store_items"
        assert len(item_model["fields"]) == 3

        # Test task inspector tool
        tasks = await django_task_inspector(project_path=str(tmp_path))
        assert len(tasks) >= 1
        assert any("process_order" in t["func_name"] for t in tasks)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_manage_exec_safety_gate() -> None:
    """Test that unauthorized/unsafe commands are blocked by manage_exec."""
    res = await django_manage_exec(
        project_path=".",
        command="malicious_drop_database",
        args=[],
    )
    assert res["success"] is False
    assert "not permitted" in res["stderr"]
