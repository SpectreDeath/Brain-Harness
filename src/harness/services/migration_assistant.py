"""Migration Assistant Service protocol, models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class PydanticMigrationResult(BaseModel):
    """Result of scanning Python code for deprecated Pydantic v1 patterns."""

    status: str = Field(default="ok", description="Status indicator")
    ready_for_v2: bool = Field(default=True, description="True if no deprecated v1 patterns found")
    deprecated_patterns_count: int = Field(default=0, description="Count of detected deprecated patterns")
    issues: list[dict[str, Any]] = Field(default_factory=list, description="Detailed list of detected issues")
    error: str | None = Field(default=None, description="Error details if check failed")


class PythonCompatResult(BaseModel):
    """Result of scanning for legacy Python syntax patterns."""

    status: str = Field(default="ok", description="Status indicator")
    modern_python_compliant: bool = Field(default=True, description="True if syntax complies with modern Python conventions")
    suggestions_count: int = Field(default=0, description="Count of modern syntax suggestions")
    suggestions: list[dict[str, Any]] = Field(default_factory=list, description="Modernization suggestions")
    error: str | None = Field(default=None, description="Error details if check failed")


@runtime_checkable
class MigrationAssistantService(Protocol):
    """Protocol for Python and framework migration audits."""

    def check_pydantic_v2_readiness(self, code: str) -> PydanticMigrationResult:
        """Scan Python code for deprecated Pydantic v1 patterns."""
        ...

    def check_python_version_compat(self, code: str) -> PythonCompatResult:
        """Scan for pre-Python 3.10 legacy patterns."""
        ...


MIGRATION_ASSISTANT_KEY: ServiceKey[MigrationAssistantService] = ServiceKey("service.migration_assistant")
