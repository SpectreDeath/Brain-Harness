"""Tests for Domain 4: OpenAPI plugin."""

from __future__ import annotations

import pytest

from plugins.integration_and_io.api_openapi.main import (
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
