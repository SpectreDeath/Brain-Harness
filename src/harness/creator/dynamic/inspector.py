"""AST function inspector extracting signatures and parameter schemas from Python source."""

from __future__ import annotations

import ast
from collections.abc import Callable
from typing import Any

from harness.creator.dynamic.models import FunctionSignatureMetadata
from harness.services.tools import ToolSpec


class ASTFunctionInspector:
    """Authoritative AST inspector that extracts signatures and tool schemas from Python source code."""

    TYPE_MAPPINGS: dict[str, str] = {
        "str": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
        "list": "array",
        "List": "array",
        "dict": "object",
        "Dict": "object",
        "set": "array",
        "Set": "array",
        "tuple": "array",
        "Tuple": "array",
        "Any": "string",
    }

    @classmethod
    def _ast_type_to_json_type(cls, node: ast.AST | None) -> str:
        """Map an AST annotation node to a standard JSONSchema type string."""
        if node is None:
            return "string"
        if isinstance(node, ast.Name):
            return cls.TYPE_MAPPINGS.get(node.id, "string")
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return cls.TYPE_MAPPINGS.get(node.value, "string")
            return "string"
        if isinstance(node, ast.Subscript):
            base = cls._ast_type_to_json_type(node.value)
            if base in ("array", "object"):
                return base
            # Optional[T] / Union[T, None]
            if isinstance(node.value, ast.Name) and node.value.id in ("Optional", "Union"):
                if isinstance(node.slice, ast.Tuple) and node.slice.elts:
                    return cls._ast_type_to_json_type(node.slice.elts[0])
                return cls._ast_type_to_json_type(node.slice)
            return "string"
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            # T | None
            return cls._ast_type_to_json_type(node.left)
        return "string"

    @classmethod
    def inspect_ast(cls, code: str) -> dict[str, FunctionSignatureMetadata]:
        """Parse source code and extract function definitions with parameter schemas."""
        tree = ast.parse(code)
        results: dict[str, FunctionSignatureMetadata] = {}

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue

                docstring = ast.get_docstring(node) or ""
                params: dict[str, dict[str, Any]] = {}
                required: list[str] = []

                # Position non-default vs default args
                args = node.args.args
                defaults = node.args.defaults
                num_defaults = len(defaults)
                num_args = len(args)
                non_default_count = num_args - num_defaults

                for idx, arg in enumerate(args):
                    if arg.arg == "self":
                        continue

                    json_type = cls._ast_type_to_json_type(arg.annotation)
                    param_spec: dict[str, Any] = {"type": json_type}

                    # Determine if it has default value
                    default_idx = idx - non_default_count
                    if 0 <= default_idx < num_defaults:
                        default_node = defaults[default_idx]
                        if isinstance(default_node, ast.Constant):
                            param_spec["default"] = default_node.value
                    else:
                        required.append(arg.arg)

                    params[arg.arg] = param_spec

                ret_type = cls._ast_type_to_json_type(node.returns) if node.returns else None

                results[node.name] = FunctionSignatureMetadata(
                    name=node.name,
                    docstring=docstring,
                    parameters=params,
                    required=required,
                    return_type=ret_type,
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                )

        return results

    @classmethod
    def extract_tool_specs(
        cls,
        code: str,
        callables: dict[str, Callable[..., Any]] | None = None,
        provider: str = "",
    ) -> list[ToolSpec]:
        """Extract ToolSpec instances directly from AST source code and matching callables."""
        metadata_map = cls.inspect_ast(code)
        active_callables = callables or {}
        specs: list[ToolSpec] = []

        for name, meta in metadata_map.items():
            func = active_callables.get(name)
            if func is not None:
                # If function has docstring in code or callable, use it
                desc = meta.docstring or func.__doc__ or f"Tool: {name}"
                schema = meta.to_parameters_schema()
                specs.append(
                    ToolSpec(
                        name=name,
                        description=desc,
                        handler=func,
                        parameters_schema=schema,
                        provider=provider,
                    )
                )

        return specs
