"""AST Refactoring and Function Extraction Service protocol, models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class UnusedFunctionsResult(BaseModel):
    """Result of identifying unused top-level functions."""

    status: str = Field(default="ok", description="Status indicator")
    total_functions: int = Field(default=0, description="Total declared functions analyzed")
    unused_count: int = Field(default=0, description="Count of unused functions detected")
    unused_functions: list[dict[str, Any]] = Field(default_factory=list, description="Unused function items with names and line numbers")
    error: str | None = Field(default=None, description="Error details if analysis failed")


class FunctionExtractResult(BaseModel):
    """Result of generating a function extraction preview."""

    status: str = Field(default="ok", description="Status indicator")
    new_function_name: str = Field(default="", description="Name of extracted function")
    extracted_lines_count: int = Field(default=0, description="Count of lines extracted into new function")
    function_definition: str = Field(default="", description="Synthesized new function signature and body")
    refactored_preview: str = Field(default="", description="Refactored source preview replacing extracted lines with function call")
    error: str | None = Field(default=None, description="Error details if extraction preview failed")


@runtime_checkable
class RefactorEngineService(Protocol):
    """Protocol for AST-based refactoring, dead code identification, and function extraction."""

    def find_unused_functions(self, code: str) -> UnusedFunctionsResult:
        """Find declared top-level functions in a module that are never invoked within that module."""
        ...

    def extract_function_preview(
        self,
        code: str,
        start_line: int,
        end_line: int,
        new_func_name: str,
    ) -> FunctionExtractResult:
        """Generate a refactored preview extracting lines into a new function."""
        ...


REFACTOR_ENGINE_KEY: ServiceKey[RefactorEngineService] = ServiceKey("service.refactor_engine")
