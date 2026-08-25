"""OpenAPI 3.0 Specification service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class OpenApiSpecResult(BaseModel):
    """Result of OpenAPI specification generation."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    spec: dict[str, Any] = Field(default_factory=dict, description="Generated OpenAPI 3.0 specification")
    error: str | None = Field(default=None, description="Error details if generation failed")


class OpenApiValidationResult(BaseModel):
    """Result of validating an OpenAPI specification."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    valid: bool = Field(default=True, description="Whether the specification is structurally valid")
    errors_count: int = Field(default=0, description="Total count of structural errors")
    errors: list[str] = Field(default_factory=list, description="List of validation errors")


class OpenApiMockResult(BaseModel):
    """Result of generating a mock endpoint response."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    mock_data: Any = Field(default=None, description="Generated mock response data conforming to schema")
    error: str | None = Field(default=None, description="Error details if mock generation failed")


@runtime_checkable
class OpenApiSpecService(Protocol):
    """Protocol for OpenAPI specification synthesis, schema validation, and mock generation."""

    def generate_spec(
        self,
        title: str,
        version: str = "1.0.0",
        routes: list[dict[str, Any]] | None = None,
    ) -> OpenApiSpecResult:
        """Synthesize a valid OpenAPI 3.0 JSON specification from route definitions."""
        ...

    def validate_spec(self, spec_dict: dict[str, Any]) -> OpenApiValidationResult:
        """Validate OpenAPI 3.0 specification structure against specification rules."""
        ...

    def mock_response(self, response_schema: dict[str, Any]) -> OpenApiMockResult:
        """Generate mock JSON response conforming to a route schema."""
        ...


OPENAPI_SPEC_KEY: ServiceKey[OpenApiSpecService] = ServiceKey("service.openapi_spec")
