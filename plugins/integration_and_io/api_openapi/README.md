# plugin.api_openapi (v1.0.0)

OpenAPI / Swagger 3.0 specification synthesis, schema validation, and mock response generator

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/integration_and_io/api_openapi` |
| Category | `integration_and_io` |
| Isolation Mode | `in_process` |
| Services Provided | `service.openapi_spec` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `generate_openapi_spec` | `(title, version, routes)` | Synthesize a valid OpenAPI 3.0 JSON specification from route definitions |
| `validate_openapi_spec` | `(spec_dict)` | Validate OpenAPI 3.0 specification structure against spec requirements |
| `generate_mock_endpoint_response` | `(response_schema)` | Generate mock JSON response conforming to a route schema |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

OpenAPI 3.0 specification synthesis, validation, and mock response generator plugin.

#### Classes

- `class ApiOpenapiPlugin` — Harness Plugin providing OpenAPI 3.0 specification synthesis and validation.
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def generate_spec(title, version, routes) -> OpenApiSpecResult`
  - `def validate_spec(spec_dict) -> OpenApiValidationResult`
  - `def mock_response(response_schema) -> OpenApiMockResult`


#### Functions

- `def generate_openapi_spec(title, version, routes) -> dict[str, Any]` — Synthesize a standard OpenAPI 3.0 dictionary.
- `def validate_openapi_spec(spec_dict) -> dict[str, Any]` — Check structural validity of an OpenAPI 3.0 document.
- `def generate_mock_endpoint_response(response_schema) -> dict[str, Any]` — Generate sample mock values matching a JSON Schema.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.integration_and_io.api_openapi.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
