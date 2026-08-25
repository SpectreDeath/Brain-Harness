"""OpenAPI 3.0 specification synthesis, validation, and mock response generator plugin."""

from __future__ import annotations

from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.openapi import (
    OPENAPI_SPEC_KEY,
    OpenApiMockResult,
    OpenApiSpecResult,
    OpenApiSpecService,
    OpenApiValidationResult,
)

logger = structlog.get_logger(__name__)


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


class ApiOpenapiPlugin(HarnessPlugin, OpenApiSpecService):
    """Harness Plugin providing OpenAPI 3.0 specification synthesis and validation."""

    name = "plugin.api_openapi"
    version = "1.0.0"
    description = "OpenAPI / Swagger 3.0 specification synthesis, schema validation, and mock response generator"
    trusted = True

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [OPENAPI_SPEC_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(OPENAPI_SPEC_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # OpenApiSpecService Implementation
    # -------------------------------------------------------------------------

    def generate_spec(
        self,
        title: str,
        version: str = "1.0.0",
        routes: list[dict[str, Any]] | None = None,
    ) -> OpenApiSpecResult:
        res = generate_openapi_spec(title=title, version=version, routes=routes)
        return OpenApiSpecResult(
            status=res["status"],
            spec=res.get("spec", {}),
            error=res.get("error"),
        )

    def validate_spec(self, spec_dict: dict[str, Any]) -> OpenApiValidationResult:
        res = validate_openapi_spec(spec_dict=spec_dict)
        return OpenApiValidationResult(
            status=res["status"],
            valid=res.get("valid", False),
            errors_count=res.get("errors_count", 0),
            errors=res.get("errors", []),
        )

    def mock_response(self, response_schema: dict[str, Any]) -> OpenApiMockResult:
        res = generate_mock_endpoint_response(response_schema=response_schema)
        return OpenApiMockResult(
            status=res["status"],
            mock_data=res.get("mock_data"),
            error=res.get("error"),
        )
