# plugin.django_bridge (v1.0.0)

High-leverage Django ecosystem bridge for deep AST project inspection, safe management command execution, declarative model scaffolding, ORM query simulation, template validation, and background tasks introspection.

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/software_engineering/django_bridge` |
| Category | `software_engineering` |
| Isolation Mode | `in_process` |
| Services Provided | `service.django_bridge` |
| Dependencies Required | None |

---

## Architecture & Subpackage Decomposition

The Django Bridge plugin is partitioned into specialized single-responsibility submodules under `engine/`, while exposing a lean, backward-compatible coordinator facade in `main.py`:

- **[engine/introspect.py](engine/introspect.py)**: Deep AST project inspection (`execute_inspect_project`), settings AST parsing (`parse_settings_ast`), model extraction (`parse_app_models`), URL pattern counting (`count_url_patterns`), and Django version detection (`detect_django_version`).
- **[engine/manage.py](engine/manage.py)**: Safe Django management command runner (`execute_manage_command`) with strict command whitelist gating (`SAFE_MANAGEMENT_COMMANDS`), subprocess isolation, and execution timeouts.
- **[engine/generator.py](engine/generator.py)**: Declarative Python model code generator (`generate_model_source`) synthesizing fields, relationships, and `Meta` options from JSON specifications.
- **[engine/simulator.py](engine/simulator.py)**: Django ORM query expression to SQL compiler (`simulate_orm_query`) with AST pattern extraction and read-only safety gates.
- **[engine/validator.py](engine/validator.py)**: Template syntax diagnostics (`validate_template_syntax`) verifying tag stack pairing, Django 6.x `partialdef` blocks, and filter pipelines.
- **[engine/tasks.py](engine/tasks.py)**: Background tasks AST inspector (`inspect_project_tasks`) discovering asynchronous tasks across apps.
- **[engine/core.py](engine/core.py)**: Coordinator `DjangoBridgeServiceImpl` implementing `DjangoBridgeService` protocol.
- **[main.py](main.py)**: Lean coordinator facade (~200 lines) re-exporting symbols, defining tool wrappers (`django_inspect_project`, `django_manage_exec`, `django_model_generator`, `django_query_simulator`, `django_template_validator`, `django_task_inspector`), implementing `DjangoBridgePlugin`, and exporting module singleton `plugin` (Rule 45).

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `django_inspect_project` | `(project_path, settings_module, include_models)` | Deep inspection of a Django project directory: discovers installed apps, models, fields, relations, URL patterns, views, middleware, template loaders, settings, and task queues. |
| `django_manage_exec` | `(project_path, command, args, settings_module, timeout_sec)` | Execute safe Django management commands (check, showmigrations, migrate --plan, sqlmigrate, diffsettings, inspectdb, makemigrations --dry-run) in a guarded sandbox. |
| `django_model_generator` | `(model_name, fields, app_label, docstring, meta_options)` | Synthesizes declarative Django model classes and fields from JSON/Pydantic schemas or database table specifications. |
| `django_query_simulator` | `(query_expr, model_name, project_path)` | Evaluates and compiles Django ORM query expressions into formatted SQL queries, parameters, and execution plans without executing destructive database mutations. |
| `django_template_validator` | `(template_content, template_path, enable_partials)` | Validates syntax, tags, template partials ({% partialdef %}), and filter pipelines in Django HTML/DQL templates. |
| `django_task_inspector` | `(project_path, backend)` | Introspects and verifies Django 6.x background task queues (django.tasks), task signatures, backends, and execution parameters. |
---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.software_engineering.django_bridge.main import plugin, DjangoBridgeServiceImpl

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)

# Direct service usage
service = DjangoBridgeServiceImpl()
result = service.simulate_query(
    query_expr="Article.objects.filter(is_published=True)[:10]",
    model_name="Article",
)
print(result.generated_sql)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), single-seam IoC resolution (Rule 58), single-source plugin exports (Rule 45), and bounded directory traversal (Rule 52).
