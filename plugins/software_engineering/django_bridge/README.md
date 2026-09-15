# plugin.django_bridge (v1.0.0)

High-leverage Django ecosystem bridge for deep AST project inspection, safe management command execution, declarative model scaffolding, ORM query simulation, template validation, and background tasks introspection.

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/software_engineering/django_bridge` |
| Category | `software_engineering` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

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

## Key Modules & AST Symbols

### Module [main.py](main.py)

Django Bridge Plugin — authoritative service and tools for Django codebase analysis and synthesis.

#### Classes

- `class DjangoBridgeServiceImpl` — Authoritative implementation of DjangoBridgeService using AST analysis and sandboxed execution.
  - `def inspect_project(project_path, settings_module, include_models) -> DjangoProjectInfo` — Inspect Django project AST, discovering apps, models, URLs, middleware, and settings.
  - `def execute_manage(project_path, command, args, settings_module, timeout_sec) -> DjangoManageResult` — Execute a safe Django management command in a guarded subprocess.
  - `def generate_model_code(model_name, fields, app_label, docstring, meta_options) -> str` — Generate idiomatic Python code for a Django Model.
  - `def simulate_query(query_expr, model_name, project_path) -> DjangoQueryResult` — Safely translate and compile a Django ORM query expression to SQL.
  - `def validate_template(template_content, template_path, enable_partials) -> DjangoValidationResult` — Validate syntax of Django templates, block tags, partials, and filters.
  - `def inspect_tasks(project_path, backend) -> list[DjangoTaskInfo]` — Introspect Django 6.x background tasks defined in tasks.py files.
- `class DjangoBridgePlugin` — Authoritative Django Bridge Plugin registering tools and services into Brain Harness.
  - `def __init__() -> None`
  - `def name() -> str`
  - `def version() -> str`
  - `def description() -> str`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def enable(context) -> None` — Enable plugin and register DJANGO_BRIDGE_KEY service.
  - `def disable(context) -> None` — Disable plugin and clean up registrations.


#### Functions

- `def django_inspect_project(project_path, settings_module, include_models) -> dict[str, Any]` — Deep inspection of a Django project: discovers installed apps, models, URLs, middleware, and settings.
- `def django_manage_exec(project_path, command, args, settings_module, timeout_sec) -> dict[str, Any]` — Execute a safe Django management command in a guarded sandbox.
- `def django_model_generator(model_name, fields, app_label, docstring, meta_options) -> dict[str, Any]` — Synthesizes declarative Django model classes and fields from JSON/schema specifications.
- `def django_query_simulator(query_expr, model_name, project_path) -> dict[str, Any]` — Evaluates and compiles Django ORM query expressions into formatted SQL queries.
- `def django_template_validator(template_content, template_path, enable_partials) -> dict[str, Any]` — Validates syntax, tags, template partials ({% partialdef %}), and filters in Django templates.
- `def django_task_inspector(project_path, backend) -> list[dict[str, Any]]` — Introspects and verifies Django 6.x background task queues (django.tasks).


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.software_engineering.django_bridge.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
