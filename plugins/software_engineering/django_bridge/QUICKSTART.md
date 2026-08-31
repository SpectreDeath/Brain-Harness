# Django Bridge Plugin Quickstart

`plugin.django_bridge` provides native, high-leverage cognitive introspection and autonomous code generation capabilities for Django applications (Django 6.2.0-alpha, Django 6.x, Django 5.x, ASGI, and Daphne).

---

## Capabilities & Tools

### 1. `django_inspect_project`
Deep AST inspection of a Django project or app directory:
```python
result = await django_inspect_project(
    project_path="D:/GitHub/cloned/Django/djangoproject.com-main/djangoproject.com-main",
    include_models=True
)
print(result["django_version"])
print(result["installed_apps"])
print(result["models"])
```

### 2. `django_manage_exec`
Execute safe Django management commands inside a guarded subprocess sandbox:
```python
result = await django_manage_exec(
    project_path="path/to/django_project",
    command="showmigrations",
    args=["--plan"]
)
print(result["stdout"])
```

### 3. `django_model_generator`
Generate declarative, typed Django model classes:
```python
result = await django_model_generator(
    model_name="Article",
    app_label="blog",
    docstring="A blog post with markdown content and published status.",
    fields=[
        {"name": "title", "type": "CharField", "max_length": 255},
        {"name": "slug", "type": "SlugField", "unique": True},
        {"name": "content", "type": "TextField"},
        {"name": "author", "type": "ForeignKey", "related_model": "auth.User", "on_delete": "CASCADE"},
        {"name": "is_published", "type": "BooleanField", "default": False},
        {"name": "created_at", "type": "DateTimeField", "default": "timezone.now"},
    ],
    meta_options={
        "ordering": ["-created_at"],
        "verbose_name": "Blog Article"
    }
)
print(result["generated_code"])
```

### 4. `django_query_simulator`
Safely compile and explain Django ORM query expressions without database mutation:
```python
result = await django_query_simulator(
    query_expr="Article.objects.filter(is_published=True, created_at__gte='2026-01-01').order_by('-created_at')[:10]",
    model_name="Article"
)
print(result["generated_sql"])
print(result["explain_plan"])
```

### 5. `django_template_validator`
Validate syntax of Django templates and Django 6.x template partials (`{% partialdef %}`):
```python
result = await django_template_validator(
    template_content="""
    {% extends "base.html" %}
    {% block content %}
      {% partialdef user_card %}
        <div class="card">{{ user.name|upper }}</div>
      {% endpartialdef %}
    {% endblock %}
    """
)
print(result["valid"])  # True
print(result["partials_found"])  # ['user_card']
```

### 6. `django_task_inspector`
Introspect Django 6.x background task queues:
```python
tasks = await django_task_inspector(project_path="path/to/django_project")
for t in tasks:
    print(t["task_name"], t["queue"], t["backend"])
```

---

## Service IoC Registration

In addition to tool entrypoints, the plugin registers `DJANGO_BRIDGE_KEY` into the IoC `ServiceContext`:

```python
from harness.services.django_bridge import DJANGO_BRIDGE_KEY

django_service = context.resolve(DJANGO_BRIDGE_KEY)
project_info = await django_service.inspect_project("...")
```
