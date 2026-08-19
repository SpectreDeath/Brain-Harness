# Quick Start Guide: `domain.api_openapi` (v1.0.0)

> OpenAPI / Swagger 3.0 specification synthesis, schema validation, and mock response generator

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`generate_openapi_spec`**: Synthesize a valid OpenAPI 3.0 JSON specification from route definitions
- **`validate_openapi_spec`**: Validate OpenAPI 3.0 specification structure against spec requirements
- **`generate_mock_endpoint_response`**: Generate mock JSON response conforming to a route schema

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.api_openapi.generate_openapi_spec', {'title': '<title>', 'version': '<version>', 'routes': '<routes>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.api_openapi
harness plugin enable domain.api_openapi
```

## ⚡ Available Entrypoints & Skills
- **`generate_openapi_spec(title: string, version: string, routes: array)`**
  Synthesize a valid OpenAPI 3.0 JSON specification from route definitions
- **`validate_openapi_spec(spec_dict: object)`**
  Validate OpenAPI 3.0 specification structure against spec requirements
- **`generate_mock_endpoint_response(response_schema: object)`**
  Generate mock JSON response conforming to a route schema