"""Slotted signature metadata and schema models for dynamic tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class FunctionSignatureMetadata:
    """Extracted AST metadata for a Python function or tool."""

    name: str
    docstring: str = ""
    parameters: dict[str, dict[str, Any]] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)
    return_type: str | None = None
    is_async: bool = False

    def to_parameters_schema(self) -> dict[str, Any]:
        """Convert extracted AST parameter metadata to valid JSONSchema."""
        return {
            "type": "object",
            "properties": self.parameters,
            "required": self.required,
        }
