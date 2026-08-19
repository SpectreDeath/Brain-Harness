"""OpenAPI 3.0 specification synthesis, validation, and mock response generator plugin."""

from __future__ import annotations

from typing import Any


def generate_openapi_spec(
    title: str,
    version: str = "1.0.0",
    routes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Synthesize a standard OpenAPI 3.0 dictionary."""
    paths: dict[str, Any] = {}

    for r in routes or []:
        path = r.get("path", "/")
        method = r.get("method", "get").lower()
        summary = r.get("summary", f"{method.upper()} {path}")
        tags = r.get("tags", ["default"])
        responses = r.get("responses", {
            "200": {
                "description": "Successful operation",
                "content": {"application/json": {"schema": {"type": "object"}}},
            }
        })

        if path not in paths:
            paths[path] = {}

        paths[path][method] = {
            "summary": summary,
            "tags": tags,
            "parameters": r.get("parameters", []),
            "responses": responses,
        }

    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": title,
            "version": version,
            "description": f"Generated API documentation for {title}",
        },
        "paths": paths,
    }

    return {
        "status": "ok",
        "spec": spec,
    }


def validate_openapi_spec(spec_dict: dict[str, Any]) -> dict[str, Any]:
    """Check structural validity of an OpenAPI 3.0 document."""
    errors: list[str] = []

    if "openapi" not in spec_dict or not str(spec_dict["openapi"]).startswith("3."):
        errors.append("Missing or invalid 'openapi' version field (expected 3.x.x).")

    if "info" not in spec_dict or "title" not in spec_dict["info"] or "version" not in spec_dict["info"]:
        errors.append("Object 'info' must contain 'title' and 'version'.")

    if "paths" not in spec_dict or not isinstance(spec_dict["paths"], dict):
        errors.append("Root object must contain a 'paths' dictionary.")

    return {
        "status": "ok",
        "valid": len(errors) == 0,
        "errors_count": len(errors),
        "errors": errors,
    }


def generate_mock_endpoint_response(response_schema: dict[str, Any]) -> dict[str, Any]:
    """Generate sample mock values matching a JSON Schema."""
    schema_type = response_schema.get("type", "object")

    if schema_type == "object":
        props = response_schema.get("properties", {})
        mock_obj = {}
        for prop_name, prop_def in props.items():
            ptype = prop_def.get("type", "string")
            if ptype == "string":
                mock_obj[prop_name] = f"sample_{prop_name}"
            elif ptype in ("integer", "number"):
                mock_obj[prop_name] = 42
            elif ptype == "boolean":
                mock_obj[prop_name] = True
            elif ptype == "array":
                mock_obj[prop_name] = []
            else:
                mock_obj[prop_name] = {}
        return {"status": "ok", "mock_data": mock_obj}

    elif schema_type == "array":
        return {"status": "ok", "mock_data": []}
    elif schema_type in ("integer", "number"):
        return {"status": "ok", "mock_data": 100}
    elif schema_type == "boolean":
        return {"status": "ok", "mock_data": True}
    else:
        return {"status": "ok", "mock_data": "sample_string"}
