"""Unit tests for SchemaInferrer — deep AST and reflection for Python callables and docstrings."""

from __future__ import annotations

import typing
from typing import Any, Optional, Union

import pytest

from harness.creator.schema import SchemaInferrer


def sample_calculator(
    x: int,
    y: float = 0.0,
    label: str = "sum",
    enabled: bool = True,
    items: list[str] | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Calculate combination of numbers with optional metadata.

    Args:
        x: The primary integer operand.
        y: The floating point secondary operand.
        label: Description label tag.
        enabled: Toggle calculation flag.
        items: List of string qualifiers.
        options: Custom configuration dictionary.

    Returns:
        Result dictionary containing computed score.
    """
    return {"result": x + y, "label": label, "enabled": enabled}


def sphinx_documented_function(query: str, limit: int = 10) -> list[str]:
    """Search records in database.

    :param query: Search query term to match.
    :param limit: Maximum number of rows to return.
    """
    return [query] * limit


@pytest.mark.unit
class TestSchemaInferrer:
    def test_python_type_to_schema_type_primitives(self) -> None:
        assert SchemaInferrer.python_type_to_schema_type(int) == "integer"
        assert SchemaInferrer.python_type_to_schema_type(float) == "number"
        assert SchemaInferrer.python_type_to_schema_type(str) == "string"
        assert SchemaInferrer.python_type_to_schema_type(bool) == "boolean"
        assert SchemaInferrer.python_type_to_schema_type(list) == "array"
        assert SchemaInferrer.python_type_to_schema_type(dict) == "object"

    def test_python_type_to_schema_type_generics(self) -> None:
        assert SchemaInferrer.python_type_to_schema_type(list[int]) == "array"
        assert SchemaInferrer.python_type_to_schema_type(typing.List[str]) == "array"
        assert SchemaInferrer.python_type_to_schema_type(dict[str, Any]) == "object"
        assert SchemaInferrer.python_type_to_schema_type(typing.Dict[str, int]) == "object"
        assert SchemaInferrer.python_type_to_schema_type(Optional[int]) == "integer"
        assert SchemaInferrer.python_type_to_schema_type(Union[float, None]) == "number"
        assert SchemaInferrer.python_type_to_schema_type(int | None) == "integer"

    def test_python_type_to_schema_type_string_annotations(self) -> None:
        assert SchemaInferrer.python_type_to_schema_type("list[str]") == "array"
        assert SchemaInferrer.python_type_to_schema_type("dict[str, Any]") == "object"
        assert SchemaInferrer.python_type_to_schema_type("Optional[int]") == "integer"
        assert SchemaInferrer.python_type_to_schema_type("str | None") == "string"

    def test_infer_parameters_and_docstrings_google_style(self) -> None:
        params = SchemaInferrer.infer_parameters(sample_calculator)
        param_map = {p.name: p for p in params}

        assert len(params) == 6
        assert param_map["x"].type == "integer"
        assert param_map["x"].required is True
        assert "primary integer operand" in param_map["x"].description

        assert param_map["y"].type == "number"
        assert param_map["y"].required is False
        assert param_map["y"].default == 0.0

        assert param_map["label"].type == "string"
        assert param_map["label"].default == "sum"

        assert param_map["enabled"].type == "boolean"
        assert param_map["enabled"].default is True

        assert param_map["items"].type == "array"
        assert param_map["options"].type == "object"

    def test_infer_parameters_sphinx_style(self) -> None:
        params = SchemaInferrer.infer_parameters(sphinx_documented_function)
        param_map = {p.name: p for p in params}

        assert len(params) == 2
        assert param_map["query"].type == "string"
        assert param_map["query"].required is True
        assert "Search query term to match" in param_map["query"].description

        assert param_map["limit"].type == "integer"
        assert param_map["limit"].required is False
        assert param_map["limit"].default == 10
        assert "Maximum number of rows" in param_map["limit"].description

    def test_infer_entrypoint_spec(self) -> None:
        ep = SchemaInferrer.infer_entrypoint_spec(sample_calculator)
        assert ep.name == "sample_calculator"
        assert "Calculate combination of numbers" in ep.description
        assert len(ep.parameters) == 6
        assert ep.returns == "object"

    def test_infer_manifest(self) -> None:
        manifest = SchemaInferrer.infer_manifest(
            name="math-suite",
            tools=[sample_calculator, sphinx_documented_function],
            version="1.2.0",
            description="Complete math and search suite",
            category="math",
            preset="tool",
        )
        assert manifest.name == "math-suite"
        assert manifest.version == "1.2.0"
        assert len(manifest.entrypoints) == 2
        assert manifest.entrypoints[0].name == "sample_calculator"
        assert manifest.entrypoints[1].name == "sphinx_documented_function"
        assert manifest.category == "math"
        assert "tool" in manifest.tags
