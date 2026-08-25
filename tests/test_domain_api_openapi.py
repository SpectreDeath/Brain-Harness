"""Tests for Domain 4: OpenAPI plugin."""

from __future__ import annotations

import pytest

from harness.kernel.context import ServiceContext
from harness.services.openapi import (
    OPENAPI_SPEC_KEY,
    OpenApiMockResult,
    OpenApiSpecResult,
    OpenApiSpecService,
    OpenApiValidationResult,
)
from plugins.integration_and_io.api_openapi.main import (
    ApiOpenapiPlugin,
    generate_mock_endpoint_response,
    generate_openapi_spec,
    validate_openapi_spec,
)


@pytest.mark.unit
class TestApiOpenapiPlugin:
    def test_generate_and_validate_openapi_spec(self) -> None:
        routes = [
            {"path": "/users", "method": "get", "summary": "List all users"},
            {"path": "/users/{id}", "method": "post", "summary": "Update user"},
        ]
        res = generate_openapi_spec("User Service API", "2.0.0", routes)
        assert res["status"] == "ok"
        spec = res["spec"]
        assert spec["info"]["title"] == "User Service API"
        assert "/users" in spec["paths"]

        res_val = validate_openapi_spec(spec)
        assert res_val["status"] == "ok"
        assert res_val["valid"] is True

    def test_generate_mock_endpoint_response(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "username": {"type": "string"},
                "is_active": {"type": "boolean"},
            },
        }
        res = generate_mock_endpoint_response(schema)
        assert res["status"] == "ok"
        data = res["mock_data"]
        assert data["id"] == 42
        assert data["username"] == "sample_username"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_plugin_ioc_lifecycle_and_service(self) -> None:
        plugin = ApiOpenapiPlugin()
        assert plugin.name == "plugin.api_openapi"
        assert OPENAPI_SPEC_KEY in plugin.provides

        ctx = ServiceContext()
        await plugin.on_load(ctx)
        await plugin.on_enable()

        service = ctx.require(OPENAPI_SPEC_KEY)
        assert isinstance(service, OpenApiSpecService)

        spec_res = service.generate_spec("Test App", "1.1.0", [{"path": "/health", "method": "get"}])
        assert isinstance(spec_res, OpenApiSpecResult)
        assert spec_res.status == "ok"
        assert "/health" in spec_res.spec["paths"]

        val_res = service.validate_spec(spec_res.spec)
        assert isinstance(val_res, OpenApiValidationResult)
        assert val_res.valid is True

        mock_res = service.mock_response({"type": "integer"})
        assert isinstance(mock_res, OpenApiMockResult)
        assert mock_res.mock_data == 100

        await plugin.on_disable()
        await plugin.on_unload()
