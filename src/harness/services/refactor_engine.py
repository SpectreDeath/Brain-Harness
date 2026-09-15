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


class CodeTransformResult(BaseModel):
    """Result of an AST code transformation (Rule 12)."""

    status: str = Field(default="ok", description="Status indicator (ok, noop, error)")
    original_code: str = Field(..., description="Source code before transformation")
    refactored_code: str = Field(..., description="Synthesized code after transformation")
    transforms_applied: int = Field(default=0, description="Count of discrete AST transformations executed")
    description: str = Field(default="", description="Summary of applied refactoring")
    error: str | None = Field(default=None, description="Error details if transformation failed")


@runtime_checkable
class RefactorEngineService(Protocol):
    """Protocol for AST-based refactoring, dead code identification, and automated code repair."""

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

    def flatten_nested_ifs(self, code: str) -> CodeTransformResult:
        """Automatically merge SIM102 nested if statements into single compound conditionals."""
        ...

    def convert_to_slotted_dataclass(self, code: str, class_name: str) -> CodeTransformResult:
        """Transform a standard class into a slotted, frozen dataclass conforming to Rule 12."""
        ...

    def auto_remediate_diagnostics(
        self,
        code: str,
        diagnostics: list[dict[str, Any]],
    ) -> CodeTransformResult:
        """Automatically repair code based on diagnostic findings from linters."""
        ...


REFACTOR_ENGINE_KEY: ServiceKey[RefactorEngineService] = ServiceKey("service.refactor_engine")

